from django.contrib.auth.mixins import LoginRequiredMixin

from dotenv import load_dotenv
from openai import OpenAI
import requests
import json
import os


from .forms import CustomUserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin


from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from django.contrib.auth.decorators import login_required

from django.db.models.functions import TruncMonth, TruncDay, TruncYear, TruncWeek
from django.db.models import Sum

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout

from django.views.generic import TemplateView, CreateView
from django.urls import reverse_lazy

from concurrent.futures import ThreadPoolExecutor
from .models import Expense, Chat, Message

# Create your views here.


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class LandingPageView(TemplateView):
    template_name = 'myapp/landing.html'


class RegistrationView(CreateView):
    template_name = 'myapp/reg.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('myapp:login')


class Dashboard(TemplateView, LoginRequiredMixin):
    template_name = 'myapp/dashboard.html'


class RealWorldData(TemplateView, LoginRequiredMixin):
    template_name = 'myapp/real_world_data.html'


class CreateAnExpense(CreateView, LoginRequiredMixin):
    model = Expense
    fields = ['amount', 'category', 'details']
    template_name = 'myapp/create_expense.html'
    success_url = reverse_lazy('myapp:expenses')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


def logout_view(request):
    logout(request)
    return redirect('myapp:login')


class AIAssistant(TemplateView):
    template_name = 'myapp/ai_page.html'


# EXPENSES TRACKING ----------<


@login_required
def expenses_tracking(request):
    qs = Expense.objects.filter(user=request.user)
    total = qs.aggregate(total=Sum("amount"))["total"] or 0

    daily = (
        qs.annotate(day=TruncDay("date"))
        .values("day")
        .annotate(total=Sum("amount"))
        .order_by("day")
    )

    weekly = (
        qs.annotate(week=TruncWeek("date"))
        .values("week")
        .annotate(total=Sum("amount"))
        .order_by("week")
    )

    monthly = (
        qs.annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    yearly = (
        qs.annotate(year=TruncYear("date"))
        .values("year")
        .annotate(total=Sum("amount"))
        .order_by("year")
    )

    category = (
        qs.values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    category_daily = (
        qs.annotate(day=TruncDay("date"))
        .values("category__name", "day")
        .annotate(total=Sum("amount"))
        .order_by("day")
    )

    category_weekly = (
        qs.annotate(week=TruncWeek("date"))
        .values("category__name", "week")
        .annotate(total=Sum("amount"))
        .order_by("week")
    )

    category_monthly = (
        qs.annotate(month=TruncMonth("date"))
        .values("category__name", "month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    advice = None

    if request.method == "POST" and "analyze" in request.POST:
        advice = get_ai_advice(request,
                               total=total,
                               category=list(category),
                               category_daily=list(category_daily),
                               category_weekly=list(category_weekly),
                               category_monthly=list(category_monthly)
                               )

    return render(request, "myapp/expenses_tracking.html", {
        "total": round(total, 2),
        "daily": daily,
        "weekly": weekly,
        "monthly": monthly,
        "yearly": yearly,
        "category": category,
        "category_daily": category_daily,
        "category_weekly": category_weekly,
        "category_monthly": category_monthly,
        "advice": advice
    })


# AI EXPENSES ADVICE ----------<

@login_required
def get_ai_advice(total, category, category_daily, category_weekly, category_monthly):
    prompt = f"""
        You are a financial advisor analyzing a user's spending data.

        Data:
        Total spending: {round(total, 2)}

        Category totals:
        {category}

        Daily category spending:
        {category_daily}

        Monthly category spending:
        {category_monthly}

        Weekly category spending:
        {category_weekly}

        Rules:
        Return ONLY practical spending recommendations.

        Requirements:
        - Give exactly 3 tips
        - Each tip must be two sentences
        - Focus on reducing unnecessary spending
        - Do NOT explain the data
        - Do NOT repeat the numbers
        - Output as an HTML list using <li> tags

        Example output:
        <li>Reduce entertainment spending on weekends.</li>
        <li>Set a monthly limit for food delivery.</li>
        <li>Track daily purchases to avoid impulse spending.</li>
        """

    response = client.chat.completions.create(
        model="gpt-5.4-nano",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_completion_tokens=800,
    )
    return response.choices[0].message.content


# CHAT ----------<


@login_required
@csrf_exempt
def chat_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST'}, status=405)

    try:
        data = json.loads(request.body)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    user_message = data.get('message', '').strip()
    chat_id = data.get('chat_id')

    use_web_search = data.get('web_search', False)
    image_b64 = data.get('image')

    if not user_message and not image_b64:
        return JsonResponse({'error': 'Empty message'}, status=400)

    if chat_id:
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)

    else:
        title = (user_message or 'Image')[:60] + ('…' if len(user_message) > 60 else '')
        chat = Chat.objects.create(user=request.user, title=title)

    Message.objects.create(chat=chat, role='user', content=user_message or '[image]')

    history = list(
        chat.messages.order_by('created_at')
        .exclude(pk=chat.messages.latest('created_at').pk)
        .values('role', 'content')
    )

    system_prompt = (
        "You are a smart financial AI assistant built into MOMMA'S MILLIONAIRE, "
        "a personal finance tracking app. Help users manage budgets, analyze spending, "
        "set savings goals, and make smarter financial decisions. "
        "Be concise, practical, and friendly. "
        "IMPORTANT: Always respond in the same language the user is writing in. "
        "If only an image is provided with no text, use the language from previous messages in the conversation. "
        "Never switch languages mid-conversation."
    )

    def event_stream():
        full_reply = []

        try:
            yield f'data: {json.dumps({"chat_id": chat.id})}\n\n'

            if use_web_search:
                ws_response = client.responses.create(
                    model='gpt-5.4-nano',
                    tools=[{"type": "web_search_preview"}],
                    input=user_message,
                )

                reply_text = ws_response.output_text
                full_reply.append(reply_text)
                yield f'data: {json.dumps({"text": reply_text})}\n\n'

            elif image_b64:
                user_content = [
                    {"type": "image_url", "image_url": {"url": image_b64}},
                ]

                if user_message:
                    user_content.append({"type": "text", "text": user_message})

                vision_messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ]

                stream = client.chat.completions.create(
                    model='gpt-5.4-nano',
                    messages=vision_messages,
                    max_completion_tokens=800,
                    stream=True,
                )

                for chunk in stream:
                    delta = chunk.choices[0].delta.content or ''

                    if delta:
                        full_reply.append(delta)
                        yield f'data: {json.dumps({"text": delta})}\n\n'

            else:
                messages = [{"role": "system", "content": system_prompt}]
                messages.extend(history)
                messages.append({"role": "user", "content": user_message})

                stream = client.chat.completions.create(
                    model='gpt-5.4-nano',
                    messages=messages,
                    temperature=0.7,
                    max_completion_tokens=2000,
                    stream=True,
                )

                for chunk in stream:
                    delta = chunk.choices[0].delta.content or ''

                    if delta:
                        full_reply.append(delta)
                        yield f'data: {json.dumps({"text": delta})}\n\n'

        except Exception as e:
            yield f'data: {json.dumps({"text": f"Error: {str(e)}"})}\n\n'

        finally:
            if full_reply:
                Message.objects.create(
                    chat=chat,
                    role='assistant',
                    content=''.join(full_reply),
                )

        yield 'data: [DONE]\n\n'

    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream',
    )

    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@login_required
@require_GET
def chat_list(request):
    chats = Chat.objects.filter(user=request.user).values('id', 'title', 'created_at')

    data = []
    for chat in chats:
        data.append({
            'id': chat['id'],
            'title': chat['title'],
            'time': chat['created_at']
        })

    return JsonResponse({'chats': data})


@login_required
@csrf_exempt
@require_POST
def chat_new(request):
    chat = Chat.objects.create(user=request.user, title="New chat")

    return JsonResponse({'id': chat.id, 'title': chat.title})


@login_required
@require_GET
def chat_history(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, user=request.user)
    messages = list(chat.messages.values('role', 'content'))

    return JsonResponse({'id': chat.id, 'title': chat.title, 'messages': messages})


@login_required
@csrf_exempt
@require_POST
def chat_delete(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, user=request.user)
    chat.delete()

    return JsonResponse({'ok': True})


def fetch_indicator(country_code, key, indicator):
    url = f'https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator}?format=json&mrv=10&per_page=10'

    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()

            if len(data) > 1 and data[1]:
                entries = [e for e in data[1] if e.get('value') is not None]

                if entries:
                    latest = {
                        'value': entries[0]['value'],
                        'year': entries[0]['date'],
                    }

                    history = [{'year': e['date'], 'value': e['value']} for e in reversed(entries)]
                    return key, latest, history

    except Exception as e:
        print("Error fetching indicator:", e)

    return key, None, None


@login_required
def country_data(request, country_code):
    indicators = {
        'gdp': 'NY.GDP.MKTP.CD',
        'gdp_growth': 'NY.GDP.MKTP.KD.ZG',
        'gdp_per_capita': 'NY.GDP.PCAP.CD',

        'exports': 'NE.EXP.GNFS.CD',
        'imports': 'NE.IMP.GNFS.CD',

        'inflation': 'FP.CPI.TOTL.ZG',
        'expenses': 'GC.XPN.TOTL.GD.ZS',
        'interest_rate': 'FR.INR.LEND',

        'unemployment': 'SL.UEM.TOTL.ZS',
        'population': 'SP.POP.TOTL',
    }

    result = {'country': country_code, 'latest': {}, 'history': {}}

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(fetch_indicator, country_code, key, ind)
            for key, ind in indicators.items()
        ]

        for future in futures:
            key, latest, history = future.result()
            if latest and history:
                result['latest'][key] = latest
                result['history'][key] = history

    return JsonResponse(result)


class SimulatorView(TemplateView, LoginRequiredMixin):
    template_name = 'myapp/simulator.html'


class ControlPanelView(TemplateView, LoginRequiredMixin):
    template_name = 'myapp/control_panel.html'


class MyProfileView(TemplateView, LoginRequiredMixin):
    template_name = 'myapp/myprofile.html'



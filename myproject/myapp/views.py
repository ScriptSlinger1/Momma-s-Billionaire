from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm

from django.db.models import Sum
from django.db.models.functions import TruncMonth, TruncDay, TruncYear, TruncWeek

from django.shortcuts import render

from django.contrib.auth import logout
from django.shortcuts import redirect

from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView

from .models import Expense
from ollama import chat


# Create your views here.


class LandingPageView(TemplateView):
    template_name = 'myapp/landing.html'


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

    category_monthly = (
        qs.annotate(month=TruncMonth("date"))
        .values("category__name", "month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    category_weekly = (
        qs.annotate(week=TruncWeek("date"))
        .values("category__name", "week")
        .annotate(total=Sum("amount"))
        .order_by("week")
    )

    category_daily = (
        qs.annotate(day=TruncDay("date"))
        .values("category__name", "day")
        .annotate(total=Sum("amount"))
        .order_by("day")
    )

    advice = None

    if request.method == "POST" and "analyze" in request.POST:
        response = chat(
            model="llama3.2-vision",
            messages=[
                {
                    "role": "user",
                    "content": f"""
    You are a financial advisor analyzing a user's spending data.

    Data:
    Total spending: {round(total, 2)}

    Category totals:
    {list(category)}

    Monthly category spending:
    {list(category_monthly)}

    Weekly category spending:
    {list(category_weekly)}

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
                }
            ],
        )
        advice = response["message"]["content"]

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


class RegistrationView(CreateView):
    template_name = 'myapp/reg.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('myapp:login')


class DashboardPrototype(TemplateView):
    template_name = 'myapp/dashboard.html'


class CreateAnExpense(CreateView):
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

class RealWorldDataView(TemplateView):
    template_name = 'myapp/real_world_data.html'
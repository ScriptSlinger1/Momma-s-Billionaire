from django.db.models import Sum
from django.db.models.functions import TruncMonth, TruncDay, TruncYear, TruncWeek
from django.shortcuts import render
from django.views.generic import TemplateView
from .models import Expense


# Create your views here.

class LandingPageView(TemplateView):
    template_name = 'myapp/landing.html'

def expenses_tracking(request):
    qs = Expense.objects.filter(user=request.user)

    total = qs.aggregate(total=Sum("amount"))["total"] or 0
    daily = (
        qs.annotate(day=TruncDay("date"))
        .values("day")
        .annotate(total=Sum("amount"))
        .order_by("day")
    )
    monthly = (
        qs.annotate(month=TruncMonth("date"))
          .values("month")
          .annotate(total=Sum("amount"))
          .order_by("month")
    )

    weekly = (
        qs.annotate(week=TruncWeek("date"))
          .values("week")
          .annotate(total=Sum("amount"))
          .order_by("week")
    )

    yearly = (
        qs.annotate(year=TruncYear("date"))
          .values("year")
          .annotate(total=Sum("amount"))
          .order_by("year")
    )

    return render(request, "myapp/expenses_tracking.html", {
        "total": round(total, 2),
        "monthly": monthly,
        "weekly": weekly,
        "yearly": yearly,
        'daily': daily,
    })
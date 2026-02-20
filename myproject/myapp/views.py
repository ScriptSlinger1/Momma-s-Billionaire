from django.shortcuts import render
from django.views.generic import TemplateView


# Create your views here.

class LandingPageView(TemplateView):
    template_name = 'myapp/landing.html'

def expenses_tracking(request):
    return render(request, 'myapp/expenses_tracking.html')
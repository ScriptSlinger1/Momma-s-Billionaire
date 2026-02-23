from django.urls import path
from .views import LandingPageView, expenses_tracking

app_name = 'myapp'

urlpatterns = [
    path('', LandingPageView.as_view(), name='landing'),
    path('expenses/', expenses_tracking, name='expenses'),
]
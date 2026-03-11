from django.contrib.auth.views import LoginView
from django.urls import path
from .views import (LandingPageView,
                    expenses_tracking,
                    RegistrationView,
                    DashboardPrototype,
                    CreateAnExpense)
app_name = 'myapp'

urlpatterns = [
    path('', LandingPageView.as_view(), name='landing'),
    path('expenses/', expenses_tracking, name='expenses'),
    path('expense_create/', CreateAnExpense.as_view(), name='expense_create'),
    path('dashboard/', DashboardPrototype.as_view(), name='dashboard'),
    path('reg/', RegistrationView.as_view(), name='reg'),
    path('login/', LoginView.as_view(template_name='myapp/login.html', redirect_authenticated_user=True), name='login')
]
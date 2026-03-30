from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView, redirect_to_login
from django.urls import path

from .views import (
    LandingPageView, RegistrationView, logout_view,
    Dashboard, CreateAnExpense, expenses_tracking,
    AIAssistant, chat_api, chat_new, chat_list, chat_history, chat_delete,
    RealWorldData, country_data, SimulatorView, ControlPanelView,MyProfileView
)


app_name = 'myapp'


urlpatterns = [
    path('', LandingPageView.as_view(), name='landing'),
    path('dashboard/', Dashboard.as_view(), name='dashboard'),

    path('reg/', RegistrationView.as_view(), name='reg'),
    path('login/', LoginView.as_view(template_name='myapp/login.html', redirect_authenticated_user=True), name='login'),
    path('logout/', logout_view, name='logout'),

    path('expenses/', expenses_tracking, name='expenses'),
    path('expense_create/', CreateAnExpense.as_view(), name='expense_create'),

    path('ai/', AIAssistant.as_view(), name='ai'),
    path('ai/chat/', chat_api, name="chat_api"),
    path('ai/chats/', chat_list, name='chat_list'),
    path('ai/chats/new', chat_new, name='chat_new'),
    path('ai/chats/<int:chat_id>/', chat_history, name='chat_history'),
    path('ai/chats/<int:chat_id>/delete/', chat_delete, name='chat_delete'),

    path('data/', RealWorldData.as_view(), name='data'),
    path('data/country/<str:country_code>/', country_data, name='country_data'),

    path('sim/', SimulatorView.as_view(), name='sim'),

    path('panel/', ControlPanelView.as_view(), name='panel'),

    path('about-me/', MyProfileView.as_view(), name='about-me'),
]

if settings.DEBUG:
    urlpatterns.extend(
        static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    )

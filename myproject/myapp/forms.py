from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUserModel

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUserModel
        fields = ('username', 'first_name', 'last_name', 'bio', 'profile_picture')
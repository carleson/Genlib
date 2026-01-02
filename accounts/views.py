from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView, LogoutView


class RegisterView(CreateView):
    """Registreringsvy"""
    form_class = UserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Ditt konto har skapats! Du kan nu logga in.')
        return response


class CustomLoginView(LoginView):
    """Inloggningsvy"""
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f'Välkommen, {form.get_user().username}!')
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    """Utloggningsvy"""
    next_page = 'accounts:login'

    def dispatch(self, request, *args, **kwargs):
        messages.info(request, 'Du har loggats ut.')
        return super().dispatch(request, *args, **kwargs)

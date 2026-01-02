from django.urls import path
from .views import dashboard, initial_setup

app_name = 'core'

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('setup/', initial_setup, name='initial_setup'),
]

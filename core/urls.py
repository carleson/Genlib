from django.urls import path
from .views import (
    dashboard,
    initial_setup,
    backup_list,
    create_backup,
    download_backup,
    delete_backup,
    restore_backup,
    gedcom_import,
)

app_name = 'core'

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('setup/', initial_setup, name='initial_setup'),
    path('backup/', backup_list, name='backup_list'),
    path('backup/create/', create_backup, name='create_backup'),
    path('backup/download/<str:filename>/', download_backup, name='download_backup'),
    path('backup/delete/<str:filename>/', delete_backup, name='delete_backup'),
    path('backup/restore/', restore_backup, name='restore_backup'),
    path('gedcom/import/', gedcom_import, name='gedcom_import'),
]

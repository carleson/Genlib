from django.urls import path
from .views import (
    DocumentTypeListView, DocumentTypeCreateView, DocumentTypeUpdateView, DocumentTypeDeleteView,
    DocumentCreateView, DocumentUpdateView, DocumentDeleteView, DocumentViewUpdateView,
    document_download
)

app_name = 'documents'

urlpatterns = [
    # DocumentType URLs
    path('types/', DocumentTypeListView.as_view(), name='type_list'),
    path('types/create/', DocumentTypeCreateView.as_view(), name='type_create'),
    path('types/<int:pk>/edit/', DocumentTypeUpdateView.as_view(), name='type_update'),
    path('types/<int:pk>/delete/', DocumentTypeDeleteView.as_view(), name='type_delete'),

    # Document URLs
    path('create/', DocumentCreateView.as_view(), name='create'),
    path('<int:pk>/', DocumentViewUpdateView.as_view(), name='view'),
    path('<int:pk>/edit/', DocumentUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', DocumentDeleteView.as_view(), name='delete'),
    path('<int:pk>/download/', document_download, name='download'),
]

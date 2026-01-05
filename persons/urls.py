from django.urls import path
from .views import (
    PersonListView, PersonDetailView, PersonCreateView,
    PersonUpdateView, PersonDeleteView,
    PersonRelationshipCreateView, PersonRelationshipDeleteView,
    PersonChecklistView, ChecklistItemToggleView,
    ChecklistItemCreateView, ChecklistItemUpdateView, ChecklistItemDeleteView,
    ChecklistReportView,
    PersonRenameView, PersonDuplicateView, PersonExportView,
    PersonChronologicalReportView, PersonDocumentSyncView
)

app_name = 'persons'

urlpatterns = [
    path('', PersonListView.as_view(), name='list'),
    path('create/', PersonCreateView.as_view(), name='create'),
    path('<int:pk>/', PersonDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', PersonUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', PersonDeleteView.as_view(), name='delete'),
    # Relationship management
    path('<int:person_pk>/relationships/add/',
         PersonRelationshipCreateView.as_view(),
         name='relationship_create'),
    path('relationships/<int:pk>/delete/',
         PersonRelationshipDeleteView.as_view(),
         name='relationship_delete'),
    # Checklist management
    path('<int:pk>/checklist/', PersonChecklistView.as_view(), name='checklist'),
    path('checklist-item/<int:pk>/toggle/',
         ChecklistItemToggleView.as_view(),
         name='checklist_item_toggle'),
    path('<int:person_pk>/checklist/add/',
         ChecklistItemCreateView.as_view(),
         name='checklist_item_create'),
    path('checklist-item/<int:pk>/edit/',
         ChecklistItemUpdateView.as_view(),
         name='checklist_item_update'),
    path('checklist-item/<int:pk>/delete/',
         ChecklistItemDeleteView.as_view(),
         name='checklist_item_delete'),
    # Reports
    path('checklist-report/', ChecklistReportView.as_view(), name='checklist_report'),
    # Tools menu
    path('<int:pk>/rename/', PersonRenameView.as_view(), name='rename'),
    path('<int:pk>/duplicate/', PersonDuplicateView.as_view(), name='duplicate'),
    path('<int:pk>/export/', PersonExportView.as_view(), name='export'),
    path('<int:pk>/chronological-report/',
         PersonChronologicalReportView.as_view(),
         name='chronological_report'),
    path('<int:pk>/sync-documents/',
         PersonDocumentSyncView.as_view(),
         name='sync_documents'),
]

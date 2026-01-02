from django.contrib import admin
from .models import DocumentType, Document


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'target_directory', 'filename', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['filename', 'person', 'document_type', 'file_type', 'get_file_size_display', 'created_at']
    list_filter = ['document_type', 'file_type', 'created_at']
    search_fields = ['filename', 'source_info', 'tags']
    readonly_fields = ['created_at', 'updated_at', 'file_size', 'file_type']

    fieldsets = (
        ('Grundläggande information', {
            'fields': ('person', 'document_type', 'filename', 'file')
        }),
        ('Metadata', {
            'fields': ('source_info', 'tags')
        }),
        ('Filinformation', {
            'fields': ('relative_path', 'file_size', 'file_type', 'file_modified_at', 'created_at', 'updated_at')
        }),
    )

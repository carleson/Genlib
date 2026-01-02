from django.contrib import admin
from .models import Template, SystemConfig


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    """Admin för systemkonfiguration"""

    def has_add_permission(self, request):
        """Förhindra att fler än en instans skapas"""
        return not SystemConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Förhindra borttagning"""
        return False

    def save_model(self, request, obj, form, change):
        """Lägg till meddelande om ändring av sökväg"""
        from django.contrib import messages
        super().save_model(request, obj, form, change)
        messages.info(
            request,
            'Konfigurationen har sparats! Befintliga filer påverkas inte automatiskt. '
            'Se till att flytta befintliga filer till den nya sökvägen om du ändrade den.'
        )

    fieldsets = [
        ('Dokumentkatalog', {
            'fields': ['media_directory_path', 'media_directory_name'],
            'description': (
                '<p>Konfigurera var dokument ska lagras och vilken URL-sökväg som ska användas.</p>'
                '<p><strong>Dokumentkatalog sökväg:</strong> Kan vara absolut (t.ex. /home/user/dokument) '
                'eller relativ till projektets rotkatalog (t.ex. media eller ../arkiv).</p>'
                '<p><strong>Dokumentkatalog namn:</strong> Namnet som används i URL:er (t.ex. "media" ger /media/...).</p>'
            )
        }),
    ]


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

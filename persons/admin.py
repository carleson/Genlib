from django.contrib import admin
from django.db.models import Count, Q
from .models import (
    Person, PersonRelationship,
    ChecklistTemplate, ChecklistTemplateItem, PersonChecklistItem
)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'directory_name', 'user', 'checklist_progress', 'created_at']
    list_filter = ['user', 'template_used', 'created_at']
    search_fields = ['firstname', 'surname', 'directory_name', 'notes']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Grundläggande information', {
            'fields': ('user', 'firstname', 'surname', 'directory_name')
        }),
        ('Födelse och död', {
            'fields': ('birth_date', 'death_date')
        }),
        ('Övrigt', {
            'fields': ('notes', 'template_used', 'created_at', 'updated_at')
        }),
    )

    def checklist_progress(self, obj):
        """Visa checklistframsteg i procent"""
        total = obj.checklist_items.count()
        if total == 0:
            return '-'
        completed = obj.checklist_items.filter(is_completed=True).count()
        percentage = int((completed / total) * 100)
        return f'{completed}/{total} ({percentage}%)'
    checklist_progress.short_description = 'Checklista'


@admin.register(PersonRelationship)
class PersonRelationshipAdmin(admin.ModelAdmin):
    list_display = ['get_display_name', 'relationship_a_to_b', 'relationship_b_to_a', 'user', 'created_at']
    list_filter = ['user', 'relationship_a_to_b', 'relationship_b_to_a', 'created_at']
    search_fields = ['person_a__firstname', 'person_a__surname', 'person_b__firstname', 'person_b__surname', 'notes']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Personer', {'fields': ('user', 'person_a', 'person_b')}),
        ('Relationstyper', {'fields': ('relationship_a_to_b', 'relationship_b_to_a')}),
        ('Övrigt', {'fields': ('notes', 'created_at', 'updated_at')}),
    )

    def get_display_name(self, obj):
        return f"{obj.person_a.get_full_name()} - {obj.person_b.get_full_name()}"
    get_display_name.short_description = 'Personer'


class ChecklistTemplateItemInline(admin.TabularInline):
    """Inline admin för mallsobjekt"""
    model = ChecklistTemplateItem
    extra = 1
    fields = ['order', 'title', 'description', 'category', 'priority']
    ordering = ['order', 'title']


@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'item_count', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ChecklistTemplateItemInline]

    fieldsets = (
        ('Grundläggande information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Antal objekt'


@admin.register(ChecklistTemplateItem)
class ChecklistTemplateItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'template', 'category', 'priority', 'order', 'created_at']
    list_filter = ['template', 'category', 'priority', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['template', 'order', 'title']

    fieldsets = (
        ('Grundläggande information', {
            'fields': ('template', 'title', 'description')
        }),
        ('Kategorisering', {
            'fields': ('category', 'priority', 'order')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PersonChecklistItem)
class PersonChecklistItemAdmin(admin.ModelAdmin):
    list_display = [
        'get_person_name', 'title', 'category', 'priority',
        'is_completed', 'is_custom_display', 'completed_at'
    ]
    list_filter = [
        'is_completed', 'category', 'priority',
        'person__user', 'template_item__template'
    ]
    search_fields = [
        'person__firstname', 'person__surname',
        'title', 'description', 'notes'
    ]
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    date_hierarchy = 'completed_at'

    fieldsets = (
        ('Person och objekt', {
            'fields': ('person', 'template_item')
        }),
        ('Innehåll', {
            'fields': ('title', 'description', 'category', 'priority', 'order')
        }),
        ('Status', {
            'fields': ('is_completed', 'completed_at', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_completed', 'mark_incomplete']

    def get_person_name(self, obj):
        return obj.person.get_full_name()
    get_person_name.short_description = 'Person'
    get_person_name.admin_order_field = 'person__surname'

    def is_custom_display(self, obj):
        return obj.is_custom()
    is_custom_display.short_description = 'Anpassad'
    is_custom_display.boolean = True

    def mark_completed(self, request, queryset):
        updated = queryset.update(is_completed=True)
        self.message_user(request, f'{updated} objekt markerade som avklarade.')
    mark_completed.short_description = 'Markera valda som avklarade'

    def mark_incomplete(self, request, queryset):
        updated = queryset.update(is_completed=False)
        self.message_user(request, f'{updated} objekt markerade som ej avklarade.')
    mark_incomplete.short_description = 'Markera valda som ej avklarade'

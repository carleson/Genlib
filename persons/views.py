from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, View
)
from django.urls import reverse_lazy
from django.db.models import Q, Count, Sum, Case, When, IntegerField
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from pathlib import Path
import json
import csv
import shutil
from datetime import datetime

from .models import (
    Person, PersonRelationship, RelationshipType,
    PersonChecklistItem, ChecklistCategory
)
from .forms import PersonForm, PersonRelationshipForm, PersonRenameForm, PersonExportForm
from documents.models import Document
from core.utils import get_media_root


class PersonListView(LoginRequiredMixin, ListView):
    """Lista över alla personer"""
    model = Person
    template_name = 'persons/person_list.html'
    context_object_name = 'persons'
    paginate_by = 20

    def get_queryset(self):
        queryset = Person.objects.filter(user=self.request.user)

        # Sök
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(firstname__icontains=search) |
                Q(surname__icontains=search) |
                Q(directory_name__icontains=search) |
                Q(notes__icontains=search)
            )

        # Sortering
        sort = self.request.GET.get('sort', 'surname')
        if sort in ['surname', 'firstname', '-created_at', 'directory_name']:
            queryset = queryset.order_by(sort)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['sort'] = self.request.GET.get('sort', 'surname')
        return context


class PersonDetailView(LoginRequiredMixin, DetailView):
    """Detaljvy för en person"""
    model = Person
    template_name = 'persons/person_detail.html'
    context_object_name = 'person'

    def get_queryset(self):
        return Person.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = self.object

        # Hämta dokument för personen
        documents = Document.objects.filter(person=person)
        context['documents'] = documents

        # Gruppera dokument per typ
        documents_by_type = {}
        for doc in documents:
            type_name = doc.document_type.name
            if type_name not in documents_by_type:
                documents_by_type[type_name] = []
            documents_by_type[type_name].append(doc)
        context['documents_by_type'] = documents_by_type

        # Statistik
        context['total_documents'] = documents.count()
        context['total_size'] = documents.aggregate(total=Sum('file_size'))['total'] or 0

        # Add relationships
        all_relationships = person.get_all_relationships()

        # Group relationships by type
        relationships_grouped = {
            'parents': [],
            'children': [],
            'spouses': [],
            'siblings': [],
        }

        for rel in all_relationships:
            if rel.person_a == person:
                other_person = rel.person_b
                rel_type = rel.relationship_a_to_b
            else:
                other_person = rel.person_a
                rel_type = rel.relationship_b_to_a

            if rel_type == RelationshipType.PARENT:
                relationships_grouped['parents'].append((other_person, rel))
            elif rel_type == RelationshipType.CHILD:
                relationships_grouped['children'].append((other_person, rel))
            elif rel_type == RelationshipType.SPOUSE:
                relationships_grouped['spouses'].append((other_person, rel))
            elif rel_type == RelationshipType.SIBLING:
                relationships_grouped['siblings'].append((other_person, rel))

        context['relationships_grouped'] = relationships_grouped
        context['total_relationships'] = all_relationships.count()

        # Checklist-statistik
        context['total_checklist_items'] = person.checklist_items.count()
        context['completed_checklist_items'] = person.checklist_items.filter(is_completed=True).count()

        return context


class PersonCreateView(LoginRequiredMixin, CreateView):
    """Skapa ny person"""
    model = Person
    form_class = PersonForm
    template_name = 'persons/person_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, f'Personen {form.instance.get_full_name()} har skapats!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('persons:detail', kwargs={'pk': self.object.pk})


class PersonUpdateView(LoginRequiredMixin, UpdateView):
    """Redigera person"""
    model = Person
    form_class = PersonForm
    template_name = 'persons/person_form.html'

    def get_queryset(self):
        return Person.objects.filter(user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f'Personen {form.instance.get_full_name()} har uppdaterats!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('persons:detail', kwargs={'pk': self.object.pk})


class PersonDeleteView(LoginRequiredMixin, DeleteView):
    """Ta bort person"""
    model = Person
    template_name = 'persons/person_confirm_delete.html'
    success_url = reverse_lazy('persons:list')

    def get_queryset(self):
        return Person.objects.filter(user=self.request.user)

    def form_valid(self, form):
        person_name = self.object.get_full_name()
        messages.success(self.request, f'Personen {person_name} har tagits bort.')
        return super().form_valid(form)


class PersonRelationshipCreateView(LoginRequiredMixin, CreateView):
    """Create a new relationship for a person"""
    model = PersonRelationship
    form_class = PersonRelationshipForm
    template_name = 'persons/relationship_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.person = get_object_or_404(Person, pk=self.kwargs['person_pk'], user=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['person'] = self.person
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['person'] = self.person
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Relationen har skapats!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('persons:detail', kwargs={'pk': self.person.pk})


class PersonRelationshipDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a relationship"""
    model = PersonRelationship
    template_name = 'persons/relationship_confirm_delete.html'

    def dispatch(self, request, *args, **kwargs):
        relationship = self.get_object()
        if relationship.user != request.user:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        self.person = relationship.person_a if relationship.person_a.user == request.user else relationship.person_b
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return PersonRelationship.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['person'] = self.person
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Relationen har tagits bort.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('persons:detail', kwargs={'pk': self.person.pk})


# Checklistvyer


class PersonChecklistView(LoginRequiredMixin, DetailView):
    """Visa persons checklista med filtrering och bockningar"""
    model = Person
    template_name = 'persons/person_checklist.html'
    context_object_name = 'person'

    def get_queryset(self):
        return Person.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = self.object

        # Hämta filterparametrar
        category_filter = self.request.GET.get('category')
        status_filter = self.request.GET.get('status')

        # Bas queryset
        checklist_items = person.checklist_items.all()

        # Applicera filter
        if category_filter:
            checklist_items = checklist_items.filter(category=category_filter)

        if status_filter == 'completed':
            checklist_items = checklist_items.filter(is_completed=True)
        elif status_filter == 'incomplete':
            checklist_items = checklist_items.filter(is_completed=False)

        # Gruppera per kategori
        items_by_category = {}
        for category_code, category_name in ChecklistCategory.choices:
            category_items = checklist_items.filter(category=category_code)
            if category_items.exists():
                items_by_category[category_name] = category_items

        # Statistik
        total = person.checklist_items.count()
        completed = person.checklist_items.filter(is_completed=True).count()

        context.update({
            'checklist_items': checklist_items,
            'items_by_category': items_by_category,
            'total_items': total,
            'completed_items': completed,
            'completion_percentage': int((completed / total * 100)) if total > 0 else 0,
            'categories': ChecklistCategory.choices,
            'current_category': category_filter,
            'current_status': status_filter,
        })

        return context


class ChecklistItemToggleView(LoginRequiredMixin, View):
    """AJAX-vy för att bocka av/på checklistobjekt"""

    def post(self, request, pk):
        try:
            item = PersonChecklistItem.objects.select_related('person').get(
                pk=pk,
                person__user=request.user
            )

            # Växla avklarad
            item.is_completed = not item.is_completed
            item.save()

            return JsonResponse({
                'success': True,
                'is_completed': item.is_completed,
                'completed_at': item.completed_at.isoformat() if item.completed_at else None
            })
        except PersonChecklistItem.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Objektet hittades inte'}, status=404)


class ChecklistItemCreateView(LoginRequiredMixin, CreateView):
    """Skapa anpassat checklistobjekt för en person"""
    model = PersonChecklistItem
    template_name = 'persons/checklist_item_form.html'
    fields = ['title', 'description', 'category', 'priority', 'order']

    def dispatch(self, request, *args, **kwargs):
        self.person = get_object_or_404(
            Person,
            pk=self.kwargs['person_pk'],
            user=request.user
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['person'] = self.person
        return context

    def form_valid(self, form):
        form.instance.person = self.person
        form.instance.template_item = None  # Markera som anpassat
        messages.success(self.request, 'Anpassat checklistobjekt har lagts till!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('persons:checklist', kwargs={'pk': self.person.pk})


class ChecklistItemUpdateView(LoginRequiredMixin, UpdateView):
    """Uppdatera anpassat checklistobjekt"""
    model = PersonChecklistItem
    template_name = 'persons/checklist_item_form.html'
    fields = ['title', 'description', 'category', 'priority', 'order', 'notes']

    def get_queryset(self):
        # Tillåt endast redigering av anpassade objekt
        return PersonChecklistItem.objects.filter(
            person__user=self.request.user,
            template_item__isnull=True
        )

    def form_valid(self, form):
        messages.success(self.request, 'Checklistobjekt har uppdaterats!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('persons:checklist', kwargs={'pk': self.object.person.pk})


class ChecklistItemDeleteView(LoginRequiredMixin, DeleteView):
    """Ta bort anpassat checklistobjekt"""
    model = PersonChecklistItem
    template_name = 'persons/checklist_item_confirm_delete.html'

    def get_queryset(self):
        # Tillåt endast radering av anpassade objekt
        return PersonChecklistItem.objects.filter(
            person__user=self.request.user,
            template_item__isnull=True
        )

    def form_valid(self, form):
        messages.success(self.request, 'Checklistobjekt har tagits bort.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('persons:checklist', kwargs={'pk': self.object.person.pk})


class ChecklistReportView(LoginRequiredMixin, ListView):
    """Rapport som visar checklistframsteg för alla personer"""
    model = Person
    template_name = 'persons/checklist_report.html'
    context_object_name = 'persons'

    def get_queryset(self):
        return Person.objects.filter(user=self.request.user).annotate(
            total_items=Count('checklist_items'),
            completed_items=Count(
                'checklist_items',
                filter=Q(checklist_items__is_completed=True)
            )
        ).order_by('-completed_items', 'surname', 'firstname')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Hämta alla unika checklistobjekt-titlar för dropdown
        available_items = PersonChecklistItem.objects.filter(
            person__user=self.request.user
        ).values_list('title', flat=True).distinct().order_by('title')
        context['available_items'] = available_items

        # Filter efter specifikt checklistobjekt
        item_title_filter = self.request.GET.get('item_title')
        filter_status = self.request.GET.get('filter_status')

        if item_title_filter and filter_status:
            if filter_status == 'has':
                # Personer som har objektet avklarat
                filtered_persons = Person.objects.filter(
                    user=self.request.user,
                    checklist_items__title__iexact=item_title_filter,
                    checklist_items__is_completed=True
                ).annotate(
                    total_items=Count('checklist_items'),
                    completed_items=Count(
                        'checklist_items',
                        filter=Q(checklist_items__is_completed=True)
                    )
                ).distinct().order_by('-completed_items', 'surname', 'firstname')
            elif filter_status == 'lacks':
                # Personer som saknar objektet eller har det men ej avklarat
                persons_with_completed = Person.objects.filter(
                    user=self.request.user,
                    checklist_items__title__iexact=item_title_filter,
                    checklist_items__is_completed=True
                ).values_list('id', flat=True)

                filtered_persons = Person.objects.filter(
                    user=self.request.user
                ).exclude(
                    id__in=persons_with_completed
                ).annotate(
                    total_items=Count('checklist_items'),
                    completed_items=Count(
                        'checklist_items',
                        filter=Q(checklist_items__is_completed=True)
                    )
                ).order_by('-completed_items', 'surname', 'firstname')
            else:
                filtered_persons = None

            context['filtered_persons'] = filtered_persons
            context['item_title_filter'] = item_title_filter
            context['filter_status'] = filter_status

        # Övergripande statistik
        all_items = PersonChecklistItem.objects.filter(person__user=self.request.user)
        context.update({
            'total_checklist_items': all_items.count(),
            'total_completed': all_items.filter(is_completed=True).count(),
            'total_persons': self.get_queryset().count(),
        })

        return context


class PersonRenameView(LoginRequiredMixin, View):
    """Döp om person och flytta katalog atomärt"""

    def post(self, request, pk: int) -> HttpResponse:
        """Hantera döpning av person"""
        person = get_object_or_404(Person, pk=pk, user=request.user)
        form = PersonRenameForm(
            request.POST, user=request.user, person=person
        )

        if not form.is_valid():
            for error in form.errors.values():
                messages.error(request, error)
            return redirect('persons:detail', pk=pk)

        old_directory_name = person.directory_name
        new_directory_name = form.cleaned_data['new_directory_name']

        # Kontrollera om namnen faktiskt ändrats
        if old_directory_name == new_directory_name:
            new_firstname = form.cleaned_data.get('firstname', '')
            new_surname = form.cleaned_data.get('surname', '')

            # Uppdatera endast om namn har ändrats
            if (new_firstname != person.firstname or
                    new_surname != person.surname):
                person.firstname = new_firstname
                person.surname = new_surname
                person.save()
                messages.success(request, 'Personens namn har uppdaterats!')
            else:
                messages.info(request, 'Inga ändringar gjordes.')
            return redirect('persons:detail', pk=pk)

        # Bygg sökvägar med pathlib
        media_root = Path(get_media_root())
        old_path = media_root / 'persons' / old_directory_name
        new_path = media_root / 'persons' / new_directory_name

        try:
            with transaction.atomic():
                # Uppdatera person först
                person.firstname = form.cleaned_data.get('firstname', '')
                person.surname = form.cleaned_data.get('surname', '')
                person.directory_name = new_directory_name
                person.save()

                # Döp om katalog om den finns
                if old_path.exists():
                    if new_path.exists():
                        raise FileExistsError(
                            f'Målkatalogen {new_path} finns redan.'
                        )

                    # Använd shutil.move för atomär omdöpning
                    shutil.move(str(old_path), str(new_path))
                    messages.success(
                        request,
                        f'Personen och katalogen har döpts om från '
                        f'"{old_directory_name}" till "{new_directory_name}".'
                    )
                else:
                    messages.success(
                        request,
                        f'Personen har döpts om till "{new_directory_name}". '
                        f'Ingen katalog fanns att döpa om.'
                    )

        except FileExistsError as e:
            messages.error(request, f'Fel vid namnbyte: {str(e)}')
            return redirect('persons:detail', pk=pk)
        except OSError as e:
            messages.error(
                request,
                f'Kunde inte döpa om katalogen: {str(e)}. '
                'Databasändringarna har rullats tillbaka.'
            )
            return redirect('persons:detail', pk=pk)
        except Exception as e:
            messages.error(request, f'Oväntat fel: {str(e)}')
            return redirect('persons:detail', pk=pk)

        return redirect('persons:detail', pk=pk)


class PersonDuplicateView(LoginRequiredMixin, View):
    """Duplicera person med relationer och checklista"""

    def get(self, request, pk: int) -> HttpResponse:
        """Visa bekräftelsesida"""
        person = get_object_or_404(Person, pk=pk, user=request.user)
        context = {
            'person': person,
            'relationships_count': person.get_all_relationships().count(),
            'checklist_count': person.checklist_items.count(),
        }
        return render(
            request, 'persons/person_duplicate_confirm.html', context
        )

    def post(self, request, pk: int) -> HttpResponse:
        """Utför duplicering"""
        original_person = get_object_or_404(Person, pk=pk, user=request.user)

        try:
            with transaction.atomic():
                # Skapa ny person med "_kopia" suffix
                new_person = Person(
                    user=request.user,
                    firstname=original_person.firstname,
                    surname=original_person.surname,
                    birth_date=original_person.birth_date,
                    death_date=original_person.death_date,
                    notes=(
                        f"Kopia av {original_person.get_full_name()}\n\n"
                        f"{original_person.notes}"
                    ),
                    template_used=original_person.template_used,
                )

                # Generera unikt directory_name
                base_name = original_person.directory_name
                suffix = 1
                new_directory_name = f"{base_name}_kopia"

                while Person.objects.filter(
                    user=request.user,
                    directory_name=new_directory_name
                ).exists():
                    suffix += 1
                    new_directory_name = f"{base_name}_kopia_{suffix}"

                new_person.directory_name = new_directory_name
                new_person.save()

                # Kopiera relationer
                relationships = original_person.get_all_relationships()
                for rel in relationships:
                    if rel.person_a == original_person:
                        other_person = rel.person_b
                        rel_type_from_new = rel.relationship_a_to_b
                        rel_type_to_new = rel.relationship_b_to_a
                    else:
                        other_person = rel.person_a
                        rel_type_from_new = rel.relationship_b_to_a
                        rel_type_to_new = rel.relationship_a_to_b

                    # Skapa relation med kanonisk ordning
                    if new_person.id < other_person.id:
                        PersonRelationship.objects.create(
                            user=request.user,
                            person_a=new_person,
                            person_b=other_person,
                            relationship_a_to_b=rel_type_from_new,
                            relationship_b_to_a=rel_type_to_new,
                            notes=(
                                f"Kopierad från "
                                f"{original_person.get_full_name()}"
                            )
                        )
                    else:
                        PersonRelationship.objects.create(
                            user=request.user,
                            person_a=other_person,
                            person_b=new_person,
                            relationship_a_to_b=rel_type_to_new,
                            relationship_b_to_a=rel_type_from_new,
                            notes=(
                                f"Kopierad från "
                                f"{original_person.get_full_name()}"
                            )
                        )

                # Kopiera checklistobjekt
                for item in original_person.checklist_items.all():
                    PersonChecklistItem.objects.create(
                        person=new_person,
                        template_item=item.template_item,
                        title=item.title,
                        description=item.description,
                        category=item.category,
                        priority=item.priority,
                        order=item.order,
                        is_completed=False,  # Återställ completion status
                        notes=item.notes
                    )

                messages.success(
                    request,
                    f'Person "{original_person.get_full_name()}" har '
                    f'duplicerats som "{new_person.get_full_name()}" med '
                    f'{relationships.count()} relationer och '
                    f'{original_person.checklist_items.count()} '
                    f'checklistobjekt.'
                )

                return redirect('persons:detail', pk=new_person.pk)

        except Exception as e:
            messages.error(request, f'Fel vid duplicering: {str(e)}')
            return redirect('persons:detail', pk=pk)


class PersonExportView(LoginRequiredMixin, View):
    """Exportera persondata till JSON eller CSV"""

    def get(self, request, pk: int) -> HttpResponse:
        """Visa exportformulär"""
        person = get_object_or_404(Person, pk=pk, user=request.user)
        form = PersonExportForm()
        context = {'person': person, 'form': form}
        return render(request, 'persons/person_export.html', context)

    def post(self, request, pk: int) -> HttpResponse:
        """Generera och returnera exportfil"""
        person = get_object_or_404(Person, pk=pk, user=request.user)
        form = PersonExportForm(request.POST)

        if not form.is_valid():
            return render(request, 'persons/person_export.html', {
                'person': person,
                'form': form
            })

        export_format = form.cleaned_data['format']
        include_relationships = form.cleaned_data['include_relationships']
        include_checklist = form.cleaned_data['include_checklist']
        include_documents = form.cleaned_data['include_documents']

        # Bygg exportdata
        data = {
            'person': {
                'firstname': person.firstname,
                'surname': person.surname,
                'birth_date': (
                    person.birth_date.isoformat()
                    if person.birth_date else None
                ),
                'death_date': (
                    person.death_date.isoformat()
                    if person.death_date else None
                ),
                'notes': person.notes,
                'directory_name': person.directory_name,
                'created_at': person.created_at.isoformat(),
                'updated_at': person.updated_at.isoformat(),
            }
        }

        if include_relationships:
            relationships = []
            for rel in person.get_all_relationships():
                if rel.person_a == person:
                    other = rel.person_b
                    rel_type = rel.get_relationship_a_to_b_display()
                else:
                    other = rel.person_a
                    rel_type = rel.get_relationship_b_to_a_display()

                relationships.append({
                    'related_person': other.get_full_name(),
                    'relationship_type': rel_type,
                    'notes': rel.notes
                })
            data['relationships'] = relationships

        if include_checklist:
            checklist = []
            for item in person.checklist_items.all():
                checklist.append({
                    'title': item.title,
                    'description': item.description,
                    'category': item.get_category_display(),
                    'priority': item.get_priority_display(),
                    'is_completed': item.is_completed,
                    'completed_at': (
                        item.completed_at.isoformat()
                        if item.completed_at else None
                    ),
                    'notes': item.notes
                })
            data['checklist'] = checklist

        if include_documents:
            documents = []
            for doc in person.documents.all():
                documents.append({
                    'filename': doc.filename,
                    'document_type': doc.document_type.name,
                    'file_type': doc.file_type,
                    'file_size': doc.file_size,
                    'relative_path': doc.relative_path,
                    'tags': doc.tags,
                    'created_at': doc.created_at.isoformat()
                })
            data['documents'] = documents

        # Generera fil baserat på format
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename_base = f"{person.directory_name}_{timestamp}"

        if export_format == 'json':
            response = HttpResponse(
                json.dumps(data, indent=2, ensure_ascii=False),
                content_type='application/json'
            )
            response['Content-Disposition'] = (
                f'attachment; filename="{filename_base}.json"'
            )

        elif export_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = (
                f'attachment; filename="{filename_base}.csv"'
            )

            writer = csv.writer(response)

            # Person info
            writer.writerow(['PERSON'])
            writer.writerow([
                'Förnamn', 'Efternamn', 'Födelsedatum',
                'Dödsdatum', 'Katalognamn'
            ])
            writer.writerow([
                person.firstname,
                person.surname,
                person.birth_date or '',
                person.death_date or '',
                person.directory_name
            ])
            writer.writerow([])

            if person.notes:
                writer.writerow(['Anteckningar'])
                writer.writerow([person.notes])
                writer.writerow([])

            # Relationer
            if include_relationships and 'relationships' in data:
                writer.writerow(['RELATIONER'])
                writer.writerow([
                    'Relaterad person', 'Relationstyp', 'Anteckningar'
                ])
                for rel in data['relationships']:
                    writer.writerow([
                        rel['related_person'],
                        rel['relationship_type'],
                        rel['notes']
                    ])
                writer.writerow([])

            # Checklista
            if include_checklist and 'checklist' in data:
                writer.writerow(['CHECKLISTA'])
                writer.writerow([
                    'Titel', 'Beskrivning', 'Kategori',
                    'Prioritet', 'Avklarad', 'Anteckningar'
                ])
                for item in data['checklist']:
                    writer.writerow([
                        item['title'],
                        item['description'],
                        item['category'],
                        item['priority'],
                        'Ja' if item['is_completed'] else 'Nej',
                        item['notes']
                    ])
                writer.writerow([])

            # Dokument
            if include_documents and 'documents' in data:
                writer.writerow(['DOKUMENT'])
                writer.writerow([
                    'Filnamn', 'Dokumenttyp', 'Filtyp',
                    'Storlek', 'Sökväg', 'Taggar'
                ])
                for doc in data['documents']:
                    writer.writerow([
                        doc['filename'],
                        doc['document_type'],
                        doc['file_type'],
                        doc['file_size'],
                        doc['relative_path'],
                        doc['tags']
                    ])

        return response


class PersonChronologicalReportView(LoginRequiredMixin, DetailView):
    """Kronologisk rapport över alla källor för en person"""

    model = Person
    template_name = 'persons/person_chronological_report.html'
    context_object_name = 'person'

    def get_queryset(self):
        return Person.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = self.object

        # Hämta alla dokument sorterade kronologiskt
        documents = person.documents.all().order_by(
            'file_modified_at',
            'created_at'
        )

        # Gruppera per år
        documents_by_year = {}
        undated_documents = []

        for doc in documents:
            date = doc.file_modified_at or doc.created_at
            if date:
                year = date.year
                if year not in documents_by_year:
                    documents_by_year[year] = []
                documents_by_year[year].append(doc)
            else:
                undated_documents.append(doc)

        context['documents_by_year'] = dict(
            sorted(documents_by_year.items())
        )
        context['undated_documents'] = undated_documents
        context['total_documents'] = documents.count()

        return context

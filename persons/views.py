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
import os
import shutil
from datetime import datetime

from .models import (
    Person, PersonRelationship, RelationshipType,
    PersonChecklistItem, ChecklistCategory, BookmarkedPerson
)
from .forms import PersonForm, PersonRelationshipForm, PersonRenameForm, PersonExportForm
from documents.models import Document, DocumentType
from core.utils import get_media_root


class PersonListView(LoginRequiredMixin, ListView):
    """Lista över alla personer"""
    model = Person
    template_name = 'persons/person_list.html'
    context_object_name = 'persons'
    paginate_by = 20

    def get_queryset(self):
        from django.db.models.functions import Lower
        from django.db.models import Case, When, Value, CharField

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

        # Filter: Personer med dokument
        has_documents = self.request.GET.get('has_documents')
        if has_documents == 'on':
            queryset = queryset.annotate(
                document_count=Count('documents')
            ).filter(document_count__gt=0)

        # Filter: Levande personer
        is_alive = self.request.GET.get('is_alive')
        if is_alive == 'on':
            queryset = queryset.filter(death_date__isnull=True)

        # Filter: Bokmärkta personer
        is_bookmarked = self.request.GET.get('is_bookmarked')
        if is_bookmarked == 'on':
            bookmarked_person_ids = BookmarkedPerson.objects.filter(
                user=self.request.user
            ).values_list('person_id', flat=True)
            queryset = queryset.filter(id__in=bookmarked_person_ids)

        # Sortering med svensk alfabetisk ordning
        sort = self.request.GET.get('sort', 'surname')

        # Skapa sorteringsfält som hanterar NULL, tomma strängar och flera namn
        from django.db.models import Func

        class FirstWord(Func):
            """Extrahera första ordet från en sträng (före första mellanslaget)"""
            template = "CASE WHEN INSTR(%(expressions)s, ' ') > 0 THEN SUBSTR(%(expressions)s, 1, INSTR(%(expressions)s, ' ') - 1) ELSE %(expressions)s END"

        queryset = queryset.annotate(
            sort_surname=Case(
                When(surname='', then=Value('ZZZZZZZZZ')),
                When(surname__isnull=True, then=Value('ZZZZZZZZZ')),
                default=Lower('surname'),
                output_field=CharField(),
            ),
            # För förnamn: använd första ordet, sen hela namnet för sekundär sortering
            first_name_first_word=Case(
                When(firstname='', then=Value('ZZZZZZZZZ')),
                When(firstname__isnull=True, then=Value('ZZZZZZZZZ')),
                default=Lower(FirstWord('firstname')),
                output_field=CharField(),
            ),
            sort_firstname_full=Case(
                When(firstname='', then=Value('ZZZZZZZZZ')),
                When(firstname__isnull=True, then=Value('ZZZZZZZZZ')),
                default=Lower('firstname'),
                output_field=CharField(),
            )
        )

        if sort == 'surname':
            # Sortera på efternamn, sedan första ordet i förnamn, sedan hela förnamnet
            queryset = queryset.order_by('sort_surname', 'first_name_first_word', 'sort_firstname_full')
        elif sort == 'firstname':
            # Sortera på första ordet i förnamn, sedan hela förnamnet, sedan efternamn
            queryset = queryset.order_by('first_name_first_word', 'sort_firstname_full', 'sort_surname')
        elif sort == '-created_at':
            queryset = queryset.order_by('-created_at')
        elif sort == 'directory_name':
            queryset = queryset.order_by(Lower('directory_name'))
        elif sort == 'birth_date':
            # Sortera på födelsedatum, äldst först (NULL sist)
            queryset = queryset.order_by('birth_date')
        elif sort == '-birth_date':
            # Sortera på födelsedatum, yngst först (NULL sist)
            queryset = queryset.order_by('-birth_date')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['sort'] = self.request.GET.get('sort', 'surname')
        context['has_documents'] = self.request.GET.get('has_documents', '')
        context['is_alive'] = self.request.GET.get('is_alive', '')
        context['is_bookmarked'] = self.request.GET.get('is_bookmarked', '')

        # Räkna totalt antal personer (utan filter)
        context['total_persons'] = Person.objects.filter(user=self.request.user).count()

        # Räkna antal filtrerade träffar
        context['filtered_count'] = self.get_queryset().count()

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

        # Hämta dokument för personen (exkludera bilder - de visas i eget galleri)
        documents = Document.objects.filter(person=person).exclude(
            file_type__in=['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
        )
        context['documents'] = documents

        # Gruppera dokument per typ
        documents_by_type = {}
        for doc in documents:
            type_name = doc.document_type.name
            if type_name not in documents_by_type:
                documents_by_type[type_name] = []
            documents_by_type[type_name].append(doc)
        context['documents_by_type'] = documents_by_type

        # Statistik (alla dokument inklusive bilder)
        all_documents = Document.objects.filter(person=person)
        context['total_documents'] = all_documents.count()
        context['total_size'] = all_documents.aggregate(total=Sum('file_size'))['total'] or 0

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
                # rel.relationship_a_to_b är "min relation till andra personen"
                # Vi vill visa "vad är andra personen till mig", så använd reciprocal
                my_rel_to_other = rel.relationship_a_to_b
                other_rel_to_me = RelationshipType.get_reciprocal(my_rel_to_other)
            else:
                other_person = rel.person_a
                # rel.relationship_b_to_a är "min relation till andra personen"
                # Vi vill visa "vad är andra personen till mig", så använd reciprocal
                my_rel_to_other = rel.relationship_b_to_a
                other_rel_to_me = RelationshipType.get_reciprocal(my_rel_to_other)

            # Gruppera baserat på vad andra personen är till mig
            if other_rel_to_me == RelationshipType.PARENT:
                relationships_grouped['parents'].append((other_person, rel))
            elif other_rel_to_me == RelationshipType.CHILD:
                relationships_grouped['children'].append((other_person, rel))
            elif other_rel_to_me == RelationshipType.SPOUSE:
                relationships_grouped['spouses'].append((other_person, rel))
            elif other_rel_to_me == RelationshipType.SIBLING:
                relationships_grouped['siblings'].append((other_person, rel))

        context['relationships_grouped'] = relationships_grouped
        context['total_relationships'] = all_relationships.count()

        # Checklist-statistik
        context['total_checklist_items'] = person.checklist_items.count()
        context['completed_checklist_items'] = person.checklist_items.filter(is_completed=True).count()

        # Bokmärkesstatus
        context['is_bookmarked'] = BookmarkedPerson.objects.filter(
            user=self.request.user, person=person
        ).exists()

        # Bildgalleri
        images = person.get_images()
        context['images'] = images
        context['total_images'] = images.count()

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
                    # Använd reciprocal för att visa vad andra personen är till mig
                    my_rel = rel.relationship_a_to_b
                    other_rel = RelationshipType.get_reciprocal(my_rel)
                    rel_type = RelationshipType(other_rel).label
                else:
                    other = rel.person_a
                    # Använd reciprocal för att visa vad andra personen är till mig
                    my_rel = rel.relationship_b_to_a
                    other_rel = RelationshipType.get_reciprocal(my_rel)
                    rel_type = RelationshipType(other_rel).label

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


class PersonDocumentSyncView(LoginRequiredMixin, View):
    """Synkronisera dokument från filsystemet till databasen"""

    def post(self, request, pk: int) -> HttpResponse:
        """Utför synkronisering av dokument för en person"""
        person = get_object_or_404(Person, pk=pk, user=request.user)

        try:
            # Räknare för statistik
            added_count = 0
            removed_count = 0
            updated_count = 0

            # Hämta personens katalog
            person_dir = Path(get_media_root()) / 'persons' / person.directory_name

            if not person_dir.exists():
                messages.warning(
                    request,
                    f'Katalogen {person_dir} finns inte ännu. '
                    'Inga dokument att synkronisera.'
                )
                return redirect('persons:detail', pk=pk)

            # Hämta alla dokumenttyper
            document_types = DocumentType.objects.all()

            # Skapa en mappning av (target_directory, filename) -> DocumentType
            doc_type_map = {}
            for doc_type in document_types:
                doc_type_map[(doc_type.target_directory, doc_type.filename)] = doc_type

            # Samla alla filer som finns i filsystemet
            files_in_fs = set()
            new_documents_to_create = []

            # Skanna igenom alla kataloger i personens katalog
            for item in person_dir.rglob('*'):
                if item.is_file():
                    # Beräkna relativ sökväg från personens katalog
                    rel_path = item.relative_to(person_dir)
                    target_dir = str(rel_path.parent) if rel_path.parent != Path('.') else ''
                    filename = item.name

                    # Normalisera target_dir för att hantera Windows vs Unix-sökvägar
                    target_dir = target_dir.replace('\\', '/')

                    # Lägg till i set med filsystemfiler
                    files_in_fs.add((target_dir, filename))

                    # Kolla om dokumentet redan finns i databasen
                    existing_doc = Document.objects.filter(
                        person=person,
                        relative_path=str(rel_path).replace('\\', '/')
                    ).first()

                    if existing_doc:
                        # Uppdatera metadata för befintligt dokument
                        old_size = existing_doc.file_size
                        new_size = item.stat().st_size

                        if old_size != new_size:
                            existing_doc.file_size = new_size
                            existing_doc.file_modified_at = datetime.fromtimestamp(
                                item.stat().st_mtime
                            )
                            existing_doc.save()
                            updated_count += 1
                    else:
                        # Nytt dokument - försök hitta matchande DocumentType
                        doc_type = doc_type_map.get((target_dir, filename))

                        if doc_type:
                            # Skapa nytt Document-objekt
                            file_size = item.stat().st_size
                            _, ext = os.path.splitext(filename)
                            file_type = ext.lstrip('.').lower()

                            new_doc = Document(
                                person=person,
                                document_type=doc_type,
                                filename=filename,
                                relative_path=str(rel_path).replace('\\', '/'),
                                file_size=file_size,
                                file_type=file_type,
                                file_modified_at=datetime.fromtimestamp(
                                    item.stat().st_mtime
                                )
                            )

                            # Sätt filsökvägen
                            upload_path = os.path.join(
                                'persons',
                                person.directory_name,
                                str(rel_path).replace('\\', '/')
                            )
                            new_doc.file.name = upload_path

                            new_documents_to_create.append(new_doc)
                            added_count += 1

            # Skapa alla nya dokument
            if new_documents_to_create:
                Document.objects.bulk_create(new_documents_to_create)

            # Ta bort dokument som inte längre finns i filsystemet
            existing_documents = Document.objects.filter(person=person)
            for doc in existing_documents:
                # Extrahera target_directory och filename från relative_path
                rel_path_parts = Path(doc.relative_path)
                target_dir = str(rel_path_parts.parent) if rel_path_parts.parent != Path('.') else ''
                filename = rel_path_parts.name

                # Normalisera
                target_dir = target_dir.replace('\\', '/')

                if (target_dir, filename) not in files_in_fs:
                    # Filen finns inte längre i filsystemet
                    doc.delete()
                    removed_count += 1

            # Bygg meddelande
            message_parts = []
            if added_count > 0:
                message_parts.append(f'{added_count} dokument tillagda')
            if updated_count > 0:
                message_parts.append(f'{updated_count} dokument uppdaterade')
            if removed_count > 0:
                message_parts.append(f'{removed_count} dokument borttagna')

            if message_parts:
                messages.success(
                    request,
                    f'Dokumentsynkronisering klar: {", ".join(message_parts)}.'
                )
            else:
                messages.info(
                    request,
                    'Dokumenten är redan synkroniserade. Inga ändringar gjordes.'
                )

        except Exception as e:
            messages.error(
                request,
                f'Fel vid dokumentsynkronisering: {str(e)}'
            )

        return redirect('persons:detail', pk=pk)


class SetProfileImageView(LoginRequiredMixin, View):
    """AJAX-endpoint för att sätta/ta bort huvudbild"""

    def post(self, request, pk: int, document_pk: int) -> JsonResponse:
        """Sätt en bild som huvudbild för personen"""
        person = get_object_or_404(Person, pk=pk, user=request.user)
        document = get_object_or_404(Document, pk=document_pk, person=person)

        # Validera att dokumentet är en bild
        if document.file_type not in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
            return JsonResponse({
                'success': False,
                'error': 'Dokumentet är inte en bildfil'
            }, status=400)

        # Sätt som huvudbild
        person.profile_image = document
        person.save()

        return JsonResponse({
            'success': True,
            'message': f'"{document.filename}" är nu huvudbild'
        })

    def delete(self, request, pk: int) -> JsonResponse:
        """Ta bort huvudbild för personen"""
        person = get_object_or_404(Person, pk=pk, user=request.user)

        if person.profile_image:
            person.profile_image = None
            person.save()

            return JsonResponse({
                'success': True,
                'message': 'Huvudbild borttagen'
            })

        return JsonResponse({
            'success': False,
            'error': 'Ingen huvudbild att ta bort'
        }, status=400)


class ImageUploadView(LoginRequiredMixin, View):
    """Ladda upp en eller flera bilder för en person"""

    def post(self, request, pk: int) -> HttpResponse:
        """Hantera uppladdning av flera bilder"""
        from documents.models import DocumentType

        person = get_object_or_404(Person, pk=pk, user=request.user)
        files = request.FILES.getlist('images')

        if not files:
            messages.error(request, 'Inga filer valda för uppladdning.')
            return redirect('persons:detail', pk=pk)

        # Hämta DocumentType för bilder (standard: "bild")
        # Försök först hitta "bild", annars leta efter en DocumentType med "bilder" i target_directory
        doc_type = DocumentType.objects.filter(name='bild').first()
        if not doc_type:
            doc_type = DocumentType.objects.filter(
                target_directory__icontains='bilder'
            ).first()

        if not doc_type:
            messages.error(
                request,
                'Ingen dokumenttyp för bilder hittades. Skapa en dokumenttyp med namnet "bild" och target_directory "bilder".'
            )
            return redirect('persons:detail', pk=pk)

        # Använd DocumentType's target_directory
        image_dir_name = doc_type.target_directory

        # Skapa bildkatalog om den inte finns
        person_path = person.get_full_directory_path()
        image_path = Path(person_path) / image_dir_name
        image_path.mkdir(parents=True, exist_ok=True)

        uploaded_count = 0
        errors = []

        for uploaded_file in files:
            try:
                # Validera att det är en bildfil
                file_ext = uploaded_file.name.split('.')[-1].lower()
                if file_ext not in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
                    errors.append(f'{uploaded_file.name}: Inte en giltig bildfiltyp')
                    continue

                # Generera unikt filnamn om filen redan finns
                filename = uploaded_file.name
                file_path = image_path / filename
                counter = 1
                while file_path.exists():
                    name_parts = filename.rsplit('.', 1)
                    if len(name_parts) == 2:
                        filename = f"{name_parts[0]}_{counter}.{name_parts[1]}"
                    else:
                        filename = f"{filename}_{counter}"
                    file_path = image_path / filename
                    counter += 1

                # Spara filen
                with open(file_path, 'wb+') as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)

                # Skapa Document-post
                relative_path = f"{image_dir_name}/{filename}"
                document = Document(
                    person=person,
                    document_type=doc_type,
                    filename=filename,
                    relative_path=relative_path,
                    file_size=file_path.stat().st_size,
                    file_type=file_ext
                )

                # Sätt file.name till rätt sökväg från media root
                # Format: persons/{person.directory_name}/{relative_path}
                document.file.name = f"persons/{person.directory_name}/{relative_path}"

                document.save()
                uploaded_count += 1

            except Exception as e:
                errors.append(f'{uploaded_file.name}: {str(e)}')

        # Skicka meddelanden till användaren
        if uploaded_count > 0:
            if uploaded_count == 1:
                messages.success(request, f'1 bild uppladdad.')
            else:
                messages.success(request, f'{uploaded_count} bilder uppladdade.')

        if errors:
            for error in errors:
                messages.error(request, error)

        return redirect('persons:detail', pk=pk)


class ImageDeleteView(LoginRequiredMixin, View):
    """Radera en bild via AJAX"""

    def delete(self, request, pk: int, image_pk: int) -> JsonResponse:
        """Radera en bild för personen"""
        person = get_object_or_404(Person, pk=pk, user=request.user)
        document = get_object_or_404(Document, pk=image_pk, person=person)

        # Validera att dokumentet är en bild
        if document.file_type not in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
            return JsonResponse({
                'success': False,
                'error': 'Dokumentet är inte en bildfil'
            }, status=400)

        filename = document.filename

        # Rensa profile_image om detta dokument är satt som profilbild
        if person.profile_image and person.profile_image.id == document.id:
            person.profile_image = None
            person.save()

        # Ta bort filen från filsystemet
        try:
            # Konstruera full sökväg till filen
            file_path = Path(person.get_full_directory_path()) / document.relative_path
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Kunde inte ta bort filen: {str(e)}'
            }, status=500)

        # Ta bort Document-posten från databasen
        document.delete()

        return JsonResponse({
            'success': True,
            'message': f'Bilden "{filename}" har tagits bort'
        })


class FamilyTreeView(LoginRequiredMixin, View):
    """Interaktiv släktträdsvy"""

    def get(self, request) -> HttpResponse:
        """Visa släktträdet"""
        from django.db.models.functions import Lower
        from django.db.models import Case, When, Value, CharField, Func

        class FirstWord(Func):
            """Extrahera första ordet från en sträng (före första mellanslaget)"""
            template = "CASE WHEN INSTR(%(expressions)s, ' ') > 0 THEN SUBSTR(%(expressions)s, 1, INSTR(%(expressions)s, ' ') - 1) ELSE %(expressions)s END"

        # Hämta alla personer för användaren med korrekt sortering
        persons = Person.objects.filter(user=request.user).select_related(
            'template_used'
        ).prefetch_related(
            'relationships_as_a',
            'relationships_as_b'
        ).annotate(
            sort_surname=Case(
                When(surname='', then=Value('ZZZZZZZZZ')),
                When(surname__isnull=True, then=Value('ZZZZZZZZZ')),
                default=Lower('surname'),
                output_field=CharField(),
            ),
            first_name_first_word=Case(
                When(firstname='', then=Value('ZZZZZZZZZ')),
                When(firstname__isnull=True, then=Value('ZZZZZZZZZ')),
                default=Lower(FirstWord('firstname')),
                output_field=CharField(),
            ),
            sort_firstname_full=Case(
                When(firstname='', then=Value('ZZZZZZZZZ')),
                When(firstname__isnull=True, then=Value('ZZZZZZZZZ')),
                default=Lower('firstname'),
                output_field=CharField(),
            )
        ).order_by('first_name_first_word', 'sort_firstname_full', 'sort_surname')

        # Hämta vald person (om någon)
        selected_person_id = request.GET.get('person_id')
        selected_person = None
        if selected_person_id:
            selected_person = Person.objects.filter(
                pk=selected_person_id,
                user=request.user
            ).first()

        # Om ingen person vald, välj huvudperson, annars person med många relationer
        if not selected_person and persons.exists():
            # Först, försök hitta huvudpersonen
            main_person = Person.objects.filter(
                user=request.user,
                is_main_person=True
            ).first()

            if main_person:
                selected_person = main_person
            else:
                # Annars, försök hitta en person med flest relationer
                person_with_most_rels = None
                max_rels = 0
                for person in persons[:50]:  # Kolla första 50
                    rel_count = person.get_all_relationships().count()
                    if rel_count > max_rels:
                        max_rels = rel_count
                        person_with_most_rels = person
                selected_person = person_with_most_rels or persons.first()

        # Bygg träddata med flera generationer
        tree_data = None
        if selected_person:
            tree_data = self._build_tree_data(selected_person)

        context = {
            'persons': persons,
            'selected_person': selected_person,
            'total_persons': persons.count(),
            'tree_data': tree_data,
        }

        return render(request, 'persons/family_tree.html', context)

    def _build_tree_data(self, person):
        """Bygg träd-datastruktur för vald person med flera generationer"""

        def get_person_data(p):
            """Hämta persondata"""
            if not p:
                return None
            return {
                'id': p.id,
                'name': p.get_full_name(),
                'birth_date': p.birth_date,
                'death_date': p.death_date,
                'years_display': p.get_years_display(),
            }

        def get_parents(p):
            """Hämta föräldrar för en person"""
            parents_rel = p.get_relationships_by_type(RelationshipType.PARENT)
            parents = [rel[0] for rel in parents_rel]
            return parents[:2]  # Max 2 föräldrar

        def get_spouse(p):
            """Hämta make/maka för en person"""
            spouse_rel = p.get_relationships_by_type(RelationshipType.SPOUSE)
            if spouse_rel:
                return spouse_rel[0][0]  # Första maken/makan
            return None

        def get_children(p, spouse=None):
            """Hämta barn för en person (och eventuell make/maka)"""
            children_rel = p.get_relationships_by_type(RelationshipType.CHILD)
            children = [rel[0] for rel in children_rel]

            # Om det finns en make/maka, filtrera barn som är gemensamma
            if spouse:
                spouse_children_rel = spouse.get_relationships_by_type(RelationshipType.CHILD)
                spouse_children_ids = [rel[0].id for rel in spouse_children_rel]
                # Gemensamma barn
                common_children = [c for c in children if c.id in spouse_children_ids]
                if common_children:
                    return common_children

            return children

        # Centrerad person
        tree = {
            'person': get_person_data(person),
            'spouse': None,
            'parents': [],
            'grandparents': {'paternal': [], 'maternal': []},
            'children': [],
            'grandchildren': [],
        }

        # Hämta make/maka
        spouse = get_spouse(person)
        if spouse:
            tree['spouse'] = get_person_data(spouse)

        # Hämta föräldrar
        parents = get_parents(person)
        for parent in parents:
            parent_data = {
                'person': get_person_data(parent),
                'spouse': None,
            }

            # Hämta föräldrars make/maka (andra föräldern)
            parent_spouse = get_spouse(parent)
            if parent_spouse and parent_spouse.id in [p.id for p in parents]:
                parent_data['spouse'] = get_person_data(parent_spouse)

            tree['parents'].append(parent_data)

            # Hämta farföräldrar/morföräldrar
            grandparents = get_parents(parent)
            grandparents_data = []
            for gp in grandparents:
                gp_data = {
                    'person': get_person_data(gp),
                    'spouse': None,
                }
                gp_spouse = get_spouse(gp)
                if gp_spouse and gp_spouse.id in [g.id for g in grandparents]:
                    gp_data['spouse'] = get_person_data(gp_spouse)
                grandparents_data.append(gp_data)

            # Bestäm om det är faderns eller moderns föräldrar
            if len(tree['parents']) == 1:
                tree['grandparents']['paternal'] = grandparents_data
            else:
                tree['grandparents']['maternal'] = grandparents_data

        # Hämta barn
        children = get_children(person, spouse)
        for child in children:
            child_data = {
                'person': get_person_data(child),
                'spouse': None,
                'children': [],
            }

            # Hämta barnets make/maka
            child_spouse = get_spouse(child)
            if child_spouse:
                child_data['spouse'] = get_person_data(child_spouse)

            # Hämta barnbarn
            grandchildren = get_children(child, child_spouse)
            for gc in grandchildren:
                child_data['children'].append(get_person_data(gc))

            tree['children'].append(child_data)

        return tree


@login_required
def toggle_bookmark(request, pk):
    """Toggle bokmärke för en person"""
    person = get_object_or_404(Person, pk=pk, user=request.user)

    # Försök hämta befintligt bokmärke
    bookmark = BookmarkedPerson.objects.filter(user=request.user, person=person).first()

    if bookmark:
        # Ta bort bokmärke
        bookmark.delete()
        is_bookmarked = False
    else:
        # Skapa nytt bokmärke
        BookmarkedPerson.objects.create(user=request.user, person=person)
        is_bookmarked = True

    return JsonResponse({
        'success': True,
        'is_bookmarked': is_bookmarked
    })


@login_required
def set_main_person(request, pk):
    """Sätt person som huvudperson"""
    person = get_object_or_404(Person, pk=pk, user=request.user)

    # Ta bort huvudperson-flaggan från alla andra personer
    Person.objects.filter(user=request.user).exclude(pk=pk).update(is_main_person=False)

    # Sätt den valda personen som huvudperson
    person.is_main_person = True
    person.save()

    messages.success(request, f"{person.get_full_name()} är nu angiven som huvudperson.")
    return redirect('persons:detail', pk=pk)


class OpenFileExplorerView(LoginRequiredMixin, View):
    """Öppnar systemets filutforskare för personens katalog (endast localhost)"""

    def post(self, request, pk: int) -> JsonResponse:
        """Öppna filutforskaren"""
        import subprocess
        import sys
        from pathlib import Path

        # Hämta person och validera ägare
        person = get_object_or_404(Person, pk=pk, user=request.user)
        directory_path = Path(person.get_full_directory_path())

        # Validera att katalogen existerar
        if not directory_path.exists():
            return JsonResponse({
                'success': False,
                'message': f'Katalogen finns inte: {directory_path}'
            }, status=404)

        if not directory_path.is_dir():
            return JsonResponse({
                'success': False,
                'message': f'Sökvägen är inte en katalog: {directory_path}'
            }, status=400)

        # Öppna filutforskaren baserat på OS
        try:
            if sys.platform == 'win32':
                # Windows
                subprocess.Popen(['explorer', str(directory_path)])
                message = 'Filutforskaren öppnad'
            elif sys.platform == 'darwin':
                # macOS
                subprocess.Popen(['open', str(directory_path)])
                message = 'Finder öppnad'
            else:
                # Linux - försök xdg-open först, sedan fallback till vanliga file managers
                try:
                    subprocess.Popen(['xdg-open', str(directory_path)])
                    message = 'Filhanteraren öppnad'
                except FileNotFoundError:
                    # Fallback till vanliga Linux file managers
                    file_managers = [
                        'nautilus',  # GNOME
                        'dolphin',   # KDE
                        'thunar',    # XFCE
                        'pcmanfm',   # LXDE
                        'nemo',      # Cinnamon
                    ]
                    opened = False
                    for fm in file_managers:
                        try:
                            subprocess.Popen([fm, str(directory_path)])
                            message = f'{fm.capitalize()} öppnad'
                            opened = True
                            break
                        except FileNotFoundError:
                            continue

                    if not opened:
                        return JsonResponse({
                            'success': False,
                            'message': 'Kunde inte hitta någon filhanterare. Installera xdg-utils eller en av följande: ' + ', '.join(file_managers)
                        }, status=500)

            return JsonResponse({
                'success': True,
                'message': message
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Fel vid öppning av filutforskaren: {str(e)}'
            }, status=500)


class ListFilesView(LoginRequiredMixin, View):
    """Listar filer i personens katalog (för remote access)"""

    def get(self, request, pk: int) -> JsonResponse:
        """Hämta fillista"""
        from pathlib import Path

        # Hämta person och validera ägare
        person = get_object_or_404(Person, pk=pk, user=request.user)
        directory_path = Path(person.get_full_directory_path())

        # Validera att katalogen existerar
        if not directory_path.exists():
            return JsonResponse({
                'success': False,
                'message': f'Katalogen finns inte: {directory_path}'
            }, status=404)

        if not directory_path.is_dir():
            return JsonResponse({
                'success': False,
                'message': f'Sökvägen är inte en katalog: {directory_path}'
            }, status=400)

        # Samla alla filer och undermappar (flat struktur)
        files = []
        try:
            for item in sorted(directory_path.rglob('*')):
                # Skippa dolda filer
                if any(part.startswith('.') for part in item.parts):
                    continue

                try:
                    stat = item.stat()
                    relative_path = item.relative_to(directory_path)

                    files.append({
                        'name': item.name,
                        'relative_path': str(relative_path),
                        'is_dir': item.is_dir(),
                        'size': stat.st_size if item.is_file() else 0,
                        'modified': stat.st_mtime,
                    })
                except (OSError, PermissionError):
                    # Skippa filer vi inte kan läsa
                    continue

            return JsonResponse({
                'success': True,
                'directory_path': str(directory_path),
                'files': files
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Fel vid läsning av katalog: {str(e)}'
            }, status=500)

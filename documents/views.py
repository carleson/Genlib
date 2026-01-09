from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.http import HttpResponse, FileResponse, Http404
from .models import DocumentType, Document
from .forms import DocumentTypeForm, DocumentForm, DocumentViewForm
from persons.models import Person
from core.utils import get_media_root
import os
import mimetypes


# DocumentType views
class DocumentTypeListView(LoginRequiredMixin, ListView):
    """Lista över dokumenttyper"""
    model = DocumentType
    template_name = 'documents/documenttype_list.html'
    context_object_name = 'document_types'
    ordering = ['name']


class DocumentTypeCreateView(LoginRequiredMixin, CreateView):
    """Skapa ny dokumenttyp"""
    model = DocumentType
    form_class = DocumentTypeForm
    template_name = 'documents/documenttype_form.html'
    success_url = reverse_lazy('documents:type_list')

    def form_valid(self, form):
        messages.success(self.request, f'Dokumenttypen "{form.instance.name}" har skapats!')
        return super().form_valid(form)


class DocumentTypeUpdateView(LoginRequiredMixin, UpdateView):
    """Redigera dokumenttyp"""
    model = DocumentType
    form_class = DocumentTypeForm
    template_name = 'documents/documenttype_form.html'
    success_url = reverse_lazy('documents:type_list')

    def form_valid(self, form):
        messages.success(self.request, f'Dokumenttypen "{form.instance.name}" har uppdaterats!')
        return super().form_valid(form)


class DocumentTypeDeleteView(LoginRequiredMixin, DeleteView):
    """Ta bort dokumenttyp"""
    model = DocumentType
    template_name = 'documents/documenttype_confirm_delete.html'
    success_url = reverse_lazy('documents:type_list')

    def form_valid(self, form):
        type_name = self.object.name
        messages.success(self.request, f'Dokumenttypen "{type_name}" har tagits bort.')
        return super().form_valid(form)


# Document views
class DocumentCreateView(LoginRequiredMixin, CreateView):
    """Skapa nytt dokument"""
    model = Document
    form_class = DocumentForm
    template_name = 'documents/document_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        person_id = self.request.GET.get('person')
        if person_id:
            initial['person'] = person_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Hämta document types och personer för JavaScript
        import json

        document_types = DocumentType.objects.all().values('id', 'name', 'filename', 'target_directory')
        context['document_types_json'] = json.dumps(list(document_types))

        persons = Person.objects.filter(user=self.request.user).values('id', 'directory_name')
        context['persons_json'] = json.dumps(list(persons))

        return context

    def form_valid(self, form):
        # Sätt relativ sökväg baserat på dokumenttyp
        document = form.instance
        doc_type = document.document_type
        person = document.person
        upload_type = form.cleaned_data.get('upload_type')
        uploaded_file = form.cleaned_data.get('file')

        # Om fil laddas upp, använd filens originalnamn
        if upload_type == 'file' and uploaded_file:
            document.filename = uploaded_file.name

        # Bygg relativ sökväg
        relative_path = os.path.join(
            doc_type.target_directory,
            document.filename
        )
        document.relative_path = relative_path

        # Skapa katalogstruktur
        full_directory_path = os.path.join(
            get_media_root(),
            'persons',
            person.directory_name,
            doc_type.target_directory
        )
        os.makedirs(full_directory_path, exist_ok=True)

        # Hantera filuppladdning eller textinnehåll
        if upload_type == 'file' and uploaded_file:
            # Spara uppladdad fil
            file_path = os.path.join(
                get_media_root(),
                'persons',
                person.directory_name,
                relative_path
            )

            # Skriv uppladdad fil till disk
            with open(file_path, 'wb') as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)

            # Sätt filstorlek och filtyp
            document.file_size = os.path.getsize(file_path)
            _, ext = os.path.splitext(document.filename)
            document.file_type = ext.lstrip('.').lower()

            # Sätt filsökväg i modellen
            upload_path = os.path.join(
                'persons',
                person.directory_name,
                relative_path
            )
            document.file.name = upload_path

        else:
            # Hämta text från formuläret och spara till fil
            text_content = form.cleaned_data.get('text', '')
            if text_content:
                file_path = os.path.join(
                    get_media_root(),
                    'persons',
                    person.directory_name,
                    relative_path
                )

                # Skriv text till fil
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)

                # Sätt filstorlek och filtyp manuellt
                document.file_size = os.path.getsize(file_path)
                _, ext = os.path.splitext(document.filename)
                document.file_type = ext.lstrip('.').lower()

                # Sätt filsökväg i modellen
                upload_path = os.path.join(
                    'persons',
                    person.directory_name,
                    relative_path
                )
                document.file.name = upload_path

        messages.success(self.request, f'Dokumentet "{document.filename}" har lagts till!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('persons:detail', kwargs={'pk': self.object.person.pk})


class DocumentUpdateView(LoginRequiredMixin, UpdateView):
    """Redigera dokument"""
    model = Document
    form_class = DocumentForm
    template_name = 'documents/document_form.html'

    def get_queryset(self):
        # Endast dokument för användarens personer
        user_persons = Person.objects.filter(user=self.request.user)
        return Document.objects.filter(person__in=user_persons)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # Läs in textfilinnehåll
        if self.object.file and self.object.file_type in ['txt', 'md']:
            try:
                file_path = os.path.join(
                    get_media_root(),
                    'persons',
                    self.object.person.directory_name,
                    self.object.document_type.target_directory,
                    self.object.filename
                )
                with open(file_path, 'r', encoding='utf-8') as f:
                    initial['text'] = f.read()
            except Exception as e:
                initial['text'] = f'Kunde inte läsa filen: {e}'
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Hämta document types och personer för JavaScript
        import json

        document_types = DocumentType.objects.all().values('id', 'name', 'filename', 'target_directory')
        context['document_types_json'] = json.dumps(list(document_types))

        persons = Person.objects.filter(user=self.request.user).values('id', 'directory_name')
        context['persons_json'] = json.dumps(list(persons))

        return context

    def form_valid(self, form):
        # Spara text till fil om den har ändrats
        text_content = form.cleaned_data.get('text')
        if text_content is not None:
            file_path = os.path.join(
                get_media_root(),
                'persons',
                self.object.person.directory_name,
                self.object.document_type.target_directory,
                self.object.filename
            )
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)

                # Uppdatera filstorlek
                self.object.file_size = os.path.getsize(file_path)
            except Exception as e:
                messages.error(self.request, f'Kunde inte spara filen: {e}')
                return self.form_invalid(form)

        messages.success(self.request, f'Dokumentet "{form.instance.filename}" har uppdaterats!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('persons:detail', kwargs={'pk': self.object.person.pk})


class DocumentDeleteView(LoginRequiredMixin, DeleteView):
    """Ta bort dokument"""
    model = Document
    template_name = 'documents/document_confirm_delete.html'

    def get_queryset(self):
        # Endast dokument för användarens personer
        user_persons = Person.objects.filter(user=self.request.user)
        return Document.objects.filter(person__in=user_persons)

    def form_valid(self, form):
        document = self.object
        person_id = document.person.pk
        filename = document.filename

        # Rensa profile_image om detta dokument är satt som profilbild
        if hasattr(document, 'profile_for') and document.profile_for.exists():
            for person in document.profile_for.all():
                person.profile_image = None
                person.save()

        # Ta bort filen från filsystemet
        try:
            from pathlib import Path
            # Konstruera full sökväg till filen
            file_path = Path(document.person.get_full_directory_path()) / document.relative_path
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            messages.warning(self.request, f'Kunde inte ta bort filen: {e}')

        messages.success(self.request, f'Dokumentet "{filename}" har tagits bort.')
        self.success_url = reverse_lazy('persons:detail', kwargs={'pk': person_id})
        return super().form_valid(form)


class DocumentViewUpdateView(LoginRequiredMixin, UpdateView):
    """Förenklad vy för att visa och redigera dokument"""
    model = Document
    form_class = DocumentViewForm
    template_name = 'documents/document_view.html'

    def get_queryset(self):
        # Endast dokument för användarens personer
        user_persons = Person.objects.filter(user=self.request.user)
        return Document.objects.filter(person__in=user_persons)

    def get_initial(self):
        initial = super().get_initial()

        # Läs in textfilinnehåll till formuläret
        if self.object.file_type in ['txt', 'md']:
            try:
                # Bygg filsökvägen från metadata
                file_path = os.path.join(
                    get_media_root(),
                    'persons',
                    self.object.person.directory_name,
                    self.object.document_type.target_directory,
                    self.object.filename
                )
                with open(file_path, 'r', encoding='utf-8') as f:
                    initial['file_content'] = f.read()
            except Exception as e:
                initial['file_content'] = f'Kunde inte läsa filen: {e}\nSökväg: {file_path if "file_path" in locals() else "okänd"}'

        # Läs EXIF-data för bilder
        if self.object.file_type in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
            try:
                from pathlib import Path
                from .exif_utils import read_exif_data, get_common_exif_fields

                # Konstruera filsökväg
                file_path = Path(self.object.person.get_full_directory_path()) / self.object.relative_path

                if file_path.exists():
                    exif_data = read_exif_data(file_path)
                    common_exif = get_common_exif_fields(exif_data)

                    # Fyll i EXIF-fält i formuläret
                    initial['exif_datetime'] = common_exif.get('DateTime', '')
                    initial['exif_datetime_original'] = common_exif.get('DateTimeOriginal', '')
                    initial['exif_make'] = common_exif.get('Make', '')
                    initial['exif_model'] = common_exif.get('Model', '')
                    initial['exif_artist'] = common_exif.get('Artist', '')
                    initial['exif_copyright'] = common_exif.get('Copyright', '')
                    initial['exif_description'] = common_exif.get('ImageDescription', '')

            except Exception as e:
                print(f'Kunde inte läsa EXIF-data: {e}')

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_text_file'] = self.object.file and self.object.file_type in ['txt', 'md']
        context['is_pdf'] = self.object.file and self.object.file_type == 'pdf'
        context['is_image'] = self.object.file and self.object.file_type in ['jpg', 'jpeg', 'png', 'gif', 'bmp']

        # För bilder, lägg till personens information för auto-ifyllning av metadata
        if context['is_image']:
            person = self.object.person
            person_info = person.get_full_name()

            # Lägg till datum om de finns
            if person.birth_date or person.death_date:
                dates = []
                if person.birth_date:
                    dates.append(person.birth_date.strftime('%Y-%m-%d'))
                else:
                    dates.append('')

                if person.death_date:
                    dates.append(person.death_date.strftime('%Y-%m-%d'))

                if len(dates) == 2:
                    person_info += f" ({dates[0]} - {dates[1]})"
                elif dates[0]:
                    person_info += f" ({dates[0]})"

            context['person_metadata'] = person_info

        return context

    def form_valid(self, form):
        from pathlib import Path

        old_filename = self.object.filename
        new_filename = form.cleaned_data.get('filename')
        filename_changed = False

        # Hantera filnamnsändring
        if old_filename != new_filename:
            try:
                # Konstruera gamla sökvägen baserat på relative_path (den faktiska filen)
                old_path = Path(self.object.person.get_full_directory_path()) / self.object.relative_path

                # Extrahera aktuellt filnamn från relative_path
                actual_old_filename = Path(self.object.relative_path).name

                # Uppdatera relative_path med nya filnamnet
                new_relative_path = str(Path(self.object.relative_path).parent / new_filename)
                new_path = Path(self.object.person.get_full_directory_path()) / new_relative_path

                # Debug-information
                print(f"Omdöpning:")
                print(f"  old_path: {old_path}")
                print(f"  new_path: {new_path}")
                print(f"  old_path exists: {old_path.exists()}")

                # Byt namn på filen i filsystemet
                if old_path.exists():
                    # Först döp om filen fysiskt
                    old_path.rename(new_path)
                    print(f"  Filen har döpts om i filsystemet")

                    # Uppdatera Document-objektet (men spara inte än, det görs senare)
                    self.object.filename = new_filename
                    self.object.relative_path = new_relative_path

                    # Uppdatera file.name också
                    self.object.file.name = f"persons/{self.object.person.directory_name}/{new_relative_path}"

                    filename_changed = True
                    messages.success(self.request, f'Filen har döpts om från "{actual_old_filename}" till "{new_filename}"')
                else:
                    messages.error(self.request, f'Filen kunde inte hittas: {old_path}')
                    return self.form_invalid(form)

            except Exception as e:
                import traceback
                traceback.print_exc()
                messages.error(self.request, f'Kunde inte döpa om filen: {e}')
                return self.form_invalid(form)

        # Spara textfilinnehåll tillbaka till filen
        if self.object.file_type in ['txt', 'md']:
            file_content = form.cleaned_data.get('file_content')
            if file_content is not None:
                try:
                    # Bygg filsökvägen från metadata
                    file_path = Path(self.object.person.get_full_directory_path()) / self.object.relative_path

                    # Skapa katalogstruktur om den inte finns
                    file_path.parent.mkdir(parents=True, exist_ok=True)

                    # Skriv till filen
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(file_content)
                    messages.success(self.request, f'Textfilen har sparats')
                except Exception as e:
                    messages.error(self.request, f'Kunde inte spara filen: {e}')
                    return self.form_invalid(form)

        # Hantera EXIF-data för bilder
        if self.object.file_type in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
            try:
                from .exif_utils import write_exif_data

                # Samla EXIF-data från formuläret
                exif_updates = {
                    'DateTime': form.cleaned_data.get('exif_datetime', ''),
                    'DateTimeOriginal': form.cleaned_data.get('exif_datetime_original', ''),
                    'Make': form.cleaned_data.get('exif_make', ''),
                    'Model': form.cleaned_data.get('exif_model', ''),
                    'Artist': form.cleaned_data.get('exif_artist', ''),
                    'Copyright': form.cleaned_data.get('exif_copyright', ''),
                    'ImageDescription': form.cleaned_data.get('exif_description', ''),
                }

                # Ta bort tomma värden
                exif_updates = {k: v for k, v in exif_updates.items() if v}

                if exif_updates:
                    # Skriv EXIF-data till filen
                    file_path = Path(self.object.person.get_full_directory_path()) / self.object.relative_path
                    if file_path.exists():
                        if write_exif_data(file_path, exif_updates):
                            messages.success(self.request, 'EXIF-data har uppdaterats')
                        else:
                            messages.warning(self.request, 'Kunde inte uppdatera EXIF-data')

            except Exception as e:
                messages.warning(self.request, f'Fel vid uppdatering av EXIF-data: {e}')

        if not messages.get_messages(self.request):
            messages.success(self.request, 'Dokumentet har uppdaterats!')

        # Om filnamnet ändrades, spara explicit och redirecta
        if filename_changed:
            # Spara alla ändringar inklusive tags från formuläret
            self.object.tags = form.cleaned_data.get('tags', '')
            self.object.save()
            # Redirecta till success_url
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(self.get_success_url())
        else:
            # Låt Django's standard form_valid hantera sparandet och redirect
            return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('documents:view', kwargs={'pk': self.object.pk})


@login_required
def document_download(request, pk):
    """Ladda ner ett dokument"""
    # Hämta dokumentet
    document = get_object_or_404(Document, pk=pk)

    # Kontrollera att användaren har tillgång till dokumentet
    if document.person.user != request.user:
        raise Http404("Dokumentet finns inte eller du har inte behörighet att komma åt det.")

    # Bygg filsökvägen
    file_path = os.path.join(
        get_media_root(),
        'persons',
        document.person.directory_name,
        document.document_type.target_directory,
        document.filename
    )

    # Kontrollera att filen finns
    if not os.path.exists(file_path):
        messages.error(request, f'Filen kunde inte hittas: {document.filename}')
        return redirect('persons:detail', pk=document.person.pk)

    # Bestäm MIME-typ
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'

    # Öppna och returnera filen
    try:
        response = FileResponse(open(file_path, 'rb'), content_type=mime_type)
        response['Content-Disposition'] = f'attachment; filename="{document.filename}"'
        return response
    except Exception as e:
        messages.error(request, f'Kunde inte ladda ner filen: {str(e)}')
        return redirect('persons:detail', pk=document.person.pk)

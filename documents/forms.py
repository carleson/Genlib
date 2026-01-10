from django import forms
from .models import DocumentType, Document
from persons.models import Person


class DocumentTypeForm(forms.ModelForm):
    class Meta:
        model = DocumentType
        fields = ['name', 'target_directory', 'filename', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'target_directory': forms.TextInput(attrs={'class': 'form-control'}),
            'filename': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DocumentForm(forms.ModelForm):
    upload_type = forms.ChoiceField(
        choices=[('text', 'Skriv text'), ('file', 'Ladda upp fil')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='text',
        label='Lägg till dokument genom att'
    )

    text = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 15, 'style': 'font-family: monospace;'}),
        required=False,
        label='Text',
        help_text='Skriv eller klistra in källinformationen här'
    )

    file = forms.FileField(
        required=False,
        label='Fil',
        help_text='Välj en bild eller dokument att ladda upp (jpg, png, webp, pdf, txt, etc.)',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*,.webp,.pdf,.txt,.doc,.docx'})
    )

    class Meta:
        model = Document
        fields = ['person', 'document_type', 'filename', 'relative_path', 'tags']
        widgets = {
            'person': forms.Select(attrs={'class': 'form-select', 'id': 'id_person'}),
            'document_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_document_type'}),
            'filename': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_filename'}),
            'relative_path': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly', 'id': 'id_relative_path'}),
            'tags': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            # Begränsa personer till användarens egna
            self.fields['person'].queryset = Person.objects.filter(user=user)

        # Sätt person från GET-parametern om den finns
        person_id = self.initial.get('person')
        if person_id:
            self.fields['person'].initial = person_id

    def clean(self):
        cleaned_data = super().clean()
        upload_type = cleaned_data.get('upload_type')
        text = cleaned_data.get('text')
        file = cleaned_data.get('file')

        # Validera att antingen text eller fil är ifylld
        if upload_type == 'text' and not text:
            raise forms.ValidationError('Du måste skriva text om du väljer "Skriv text".')
        elif upload_type == 'file' and not file:
            raise forms.ValidationError('Du måste välja en fil om du väljer "Ladda upp fil".')

        return cleaned_data


class DocumentViewForm(forms.ModelForm):
    """Förenklad vy för att visa och redigera dokument"""
    file_content = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 20, 'style': 'font-family: monospace;'}),
        required=False,
        label='Källinformation'
    )

    # EXIF-fält för bilder
    exif_datetime = forms.CharField(
        required=False,
        label='Datum/Tid',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'YYYY:MM:DD HH:MM:SS'}),
        help_text='Format: YYYY:MM:DD HH:MM:SS (t.ex. 2024:01:15 14:30:00)'
    )
    exif_datetime_original = forms.CharField(
        required=False,
        label='Originaldatum',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'YYYY:MM:DD HH:MM:SS'}),
        help_text='När bilden togs'
    )
    exif_make = forms.CharField(
        required=False,
        label='Kameratillverkare',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    exif_model = forms.CharField(
        required=False,
        label='Kameramodell',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    exif_artist = forms.CharField(
        required=False,
        label='Fotograf',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    exif_copyright = forms.CharField(
        required=False,
        label='Copyright',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    exif_description = forms.CharField(
        required=False,
        label='Bildbeskrivning',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
    )

    class Meta:
        model = Document
        fields = ['filename', 'tags']
        widgets = {
            'filename': forms.TextInput(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control'}),
        }

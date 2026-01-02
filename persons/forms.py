from django import forms
from .models import Person, PersonRelationship
from core.models import Template


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ['firstname', 'surname', 'birth_date', 'death_date', 'notes',
                  'directory_name', 'template_used']
        widgets = {
            'firstname': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_firstname'}),
            'surname': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_surname'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'id_birth_date'}),
            'death_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'directory_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly', 'id': 'id_directory_name'}),
            'template_used': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_directory_name(self):
        directory_name = self.cleaned_data.get('directory_name')
        if self.user:
            # Kontrollera om katalognamnet redan finns för användaren
            existing = Person.objects.filter(
                user=self.user,
                directory_name=directory_name
            ).exclude(pk=self.instance.pk if self.instance else None)

            if existing.exists():
                raise forms.ValidationError(
                    f'Du har redan en person med katalognamnet "{directory_name}".'
                )
        return directory_name

    def clean(self):
        cleaned_data = super().clean()
        firstname = cleaned_data.get('firstname')
        surname = cleaned_data.get('surname')

        if not firstname and not surname:
            raise forms.ValidationError(
                'Minst ett av förnamn eller efternamn måste anges.'
            )

        return cleaned_data


class PersonRelationshipForm(forms.ModelForm):
    """Form for creating/editing person relationships"""

    related_person = forms.ModelChoiceField(
        queryset=Person.objects.none(),
        empty_label="Välj person...",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Relaterad person"
    )

    relationship_type = forms.ChoiceField(
        choices=[
            ('', 'Välj relationstyp...'),
            ('PARENT', 'Förälder till vald person'),
            ('CHILD', 'Barn till vald person'),
            ('SPOUSE', 'Make/Maka till vald person'),
            ('SIBLING', 'Syskon till vald person'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Relationstyp"
    )

    class Meta:
        model = PersonRelationship
        fields = ['related_person', 'relationship_type', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.person = kwargs.pop('person', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user:
            # Only show persons belonging to current user, excluding current person
            self.fields['related_person'].queryset = Person.objects.filter(
                user=self.user
            ).exclude(pk=self.person.pk if self.person else None).order_by('surname', 'firstname')

    def clean(self):
        cleaned_data = super().clean()
        related_person = cleaned_data.get('related_person')
        relationship_type = cleaned_data.get('relationship_type')

        if not related_person or not relationship_type:
            return cleaned_data

        # Check if relationship already exists
        from django.db.models import Q
        existing = PersonRelationship.objects.filter(
            Q(person_a=self.person, person_b=related_person) |
            Q(person_a=related_person, person_b=self.person)
        ).exclude(pk=self.instance.pk if self.instance.pk else None)

        if existing.exists():
            raise forms.ValidationError('En relation mellan dessa personer finns redan.')

        return cleaned_data

    def save(self, commit=True):
        """Create relationship with proper person ordering and reciprocal types"""
        from persons.models import RelationshipType

        related_person = self.cleaned_data['related_person']
        relationship_type = self.cleaned_data['relationship_type']
        reciprocal = RelationshipType.get_reciprocal(relationship_type)

        instance = super().save(commit=False)

        if self.person.id < related_person.id:
            instance.person_a = self.person
            instance.person_b = related_person
            instance.relationship_a_to_b = relationship_type
            instance.relationship_b_to_a = reciprocal
        else:
            instance.person_a = related_person
            instance.person_b = self.person
            instance.relationship_a_to_b = reciprocal
            instance.relationship_b_to_a = relationship_type

        instance.user = self.user

        if commit:
            instance.save()

        return instance


class PersonRenameForm(forms.Form):
    """Form för att döpa om en person"""

    firstname = forms.CharField(
        max_length=100,
        required=False,
        label="Förnamn",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    surname = forms.CharField(
        max_length=100,
        required=False,
        label="Efternamn",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    new_directory_name = forms.CharField(
        max_length=200,
        label="Nytt katalognamn",
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'readonly': True}
        )
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.person = kwargs.pop('person', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        firstname = cleaned_data.get('firstname')
        surname = cleaned_data.get('surname')

        if not firstname and not surname:
            raise forms.ValidationError(
                'Minst ett av förnamn eller efternamn måste anges.'
            )

        return cleaned_data

    def clean_new_directory_name(self):
        new_directory_name = self.cleaned_data.get('new_directory_name')

        if self.user and self.person:
            # Kontrollera unikhet, exkludera nuvarande person
            existing = Person.objects.filter(
                user=self.user,
                directory_name=new_directory_name
            ).exclude(pk=self.person.pk)

            if existing.exists():
                raise forms.ValidationError(
                    f'Du har redan en person med katalognamnet '
                    f'"{new_directory_name}".'
                )

        return new_directory_name


class PersonExportForm(forms.Form):
    """Form för att välja exportformat"""

    format = forms.ChoiceField(
        choices=[
            ('json', 'JSON'),
            ('csv', 'CSV'),
        ],
        initial='json',
        widget=forms.RadioSelect(),
        label="Exportformat"
    )
    include_relationships = forms.BooleanField(
        required=False,
        initial=True,
        label="Inkludera relationer"
    )
    include_checklist = forms.BooleanField(
        required=False,
        initial=True,
        label="Inkludera checklista"
    )
    include_documents = forms.BooleanField(
        required=False,
        initial=True,
        label="Inkludera dokumentlista"
    )

"""Formulär för core-appen"""
from django import forms
from django.contrib.auth.models import User
from pathlib import Path
import os


class InitialSetupForm(forms.Form):
    """Formulär för initial setup av applikationen"""

    # Val mellan nytt projekt eller restore
    setup_type = forms.ChoiceField(
        choices=[
            ('new', 'Nytt projekt'),
            ('restore', 'Återställ från backup')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='new',
        label='Välj installationstyp'
    )

    # Restore-fält
    backup_file = forms.FileField(
        required=False,
        label="Backup-fil",
        help_text="Välj en ZIP-fil från tidigare backup",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.zip'
        })
    )

    # Superuser-fält (för nytt projekt)
    username = forms.CharField(
        max_length=150,
        label="Användarnamn",
        help_text="Användarnamn för administratörskontot",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'admin'
        })
    )
    email = forms.EmailField(
        label="E-postadress",
        required=False,
        help_text="Valfri e-postadress för administratören",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'admin@example.com'
        })
    )
    password = forms.CharField(
        label="Lösenord",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Välj ett starkt lösenord'
        }),
        help_text="Minst 8 tecken"
    )
    password_confirm = forms.CharField(
        label="Bekräfta lösenord",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ange lösenordet igen'
        })
    )

    # Media-katalog
    media_directory_path = forms.CharField(
        max_length=500,
        label="Media-bibliotekskatalog",
        help_text="Absolut sökväg till katalog där mediafiler ska lagras (t.ex. /home/user/genlib-media) eller relativ sökväg (t.ex. media)",
        initial="media",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '/absolut/sökväg/till/media eller media'
        })
    )

    # Backup-katalog
    backup_directory_path = forms.CharField(
        max_length=500,
        label="Backup-katalog",
        help_text="Absolut sökväg till katalog där backuper ska lagras (t.ex. /home/user/genlib-backups) eller relativ sökväg (t.ex. backups)",
        initial="backups",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '/absolut/sökväg/till/backups eller backups'
        })
    )

    def clean(self):
        """Validera hela formuläret baserat på setup_type"""
        cleaned_data = super().clean()
        setup_type = cleaned_data.get('setup_type')

        if setup_type == 'new':
            # Validera fält för nytt projekt
            username = cleaned_data.get('username')
            password = cleaned_data.get('password')
            password_confirm = cleaned_data.get('password_confirm')
            media_directory_path = cleaned_data.get('media_directory_path')

            # Kontrollera att alla obligatoriska fält för nytt projekt är ifyllda
            if not username:
                self.add_error('username', 'Användarnamn krävs för nytt projekt')
            if not password:
                self.add_error('password', 'Lösenord krävs för nytt projekt')
            if not password_confirm:
                self.add_error('password_confirm', 'Bekräfta lösenord krävs')

            # Validera lösenord
            if password and len(password) < 8:
                self.add_error('password', 'Lösenordet måste vara minst 8 tecken långt')

            if password and password_confirm and password != password_confirm:
                self.add_error('password_confirm', 'Lösenorden matchar inte')

            # Validera användarnamn
            if username and User.objects.filter(username=username).exists():
                self.add_error('username', f"Användarnamnet '{username}' är redan taget")

        elif setup_type == 'restore':
            # Validera fält för restore
            backup_file = cleaned_data.get('backup_file')
            if not backup_file:
                self.add_error('backup_file', 'Backup-fil krävs för återställning')
            elif backup_file:
                # Validera att det är en ZIP-fil
                if not backup_file.name.endswith('.zip'):
                    self.add_error('backup_file', 'Endast ZIP-filer är tillåtna')

        return cleaned_data

    def clean_media_directory_path(self):
        """Validera media-katalogen (endast för nytt projekt)"""
        setup_type = self.data.get('setup_type')

        # Hoppa över validering om det är restore
        if setup_type == 'restore':
            return self.cleaned_data.get('media_directory_path', 'media')

        path_str = self.cleaned_data.get('media_directory_path')
        if not path_str:
            return 'media'  # Default-värde

        path = Path(path_str)

        # Om det är en absolut sökväg, validera den
        if path.is_absolute():
            # Kontrollera att parent-katalogen finns
            if not path.parent.exists():
                raise forms.ValidationError(
                    f"Överordnad katalog {path.parent} finns inte! "
                    "Skapa den först eller välj en annan sökväg."
                )

            # Skapa katalogen om den inte finns
            if not path.exists():
                try:
                    path.mkdir(parents=False, exist_ok=True)
                except OSError as e:
                    raise forms.ValidationError(
                        f"Kunde inte skapa katalogen: {e}"
                    )

            # Kontrollera skrivrättigheter
            if not os.access(path, os.W_OK):
                raise forms.ValidationError(
                    f"Ingen skrivrättighet till katalogen {path}!"
                )

        return path_str

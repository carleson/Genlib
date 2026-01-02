from django.db import models
from django.contrib.auth.models import User
from pathlib import Path


class SystemConfig(models.Model):
    """Systemkonfiguration - singleton modell (endast en instans)"""
    media_directory_path = models.CharField(
        max_length=500,
        default='media',
        verbose_name="Dokumentkatalog sökväg",
        help_text="Absolut sökväg (t.ex. /home/user/dokument) eller relativ (t.ex. media)"
    )
    media_directory_name = models.CharField(
        max_length=100,
        default='media',
        verbose_name="Dokumentkatalog namn",
        help_text="Namnet på katalogen (används i URL)"
    )

    class Meta:
        verbose_name = "Systemkonfiguration"
        verbose_name_plural = "Systemkonfiguration"

    def __str__(self):
        return "Systemkonfiguration"

    def save(self, *args, **kwargs):
        """Säkerställ att det endast finns en instans"""
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Förhindra borttagning"""
        pass

    @classmethod
    def load(cls):
        """Hämta eller skapa konfiguration"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def get_media_root(self):
        """Returnera absolut sökväg till media root"""
        from django.conf import settings
        path = Path(self.media_directory_path)
        if path.is_absolute():
            return path
        else:
            return settings.BASE_DIR / path


class Template(models.Model):
    """Mall för katalogstruktur"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Namn")
    description = models.TextField(blank=True, verbose_name="Beskrivning")
    directories = models.TextField(
        verbose_name="Kataloger",
        help_text="En katalog per rad, t.ex. 'dokument/', 'bilder/', 'anteckningar/'"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Skapad")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Uppdaterad")

    class Meta:
        verbose_name = "Mall"
        verbose_name_plural = "Mallar"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_directories_list(self):
        """Returnera lista av kataloger"""
        return [d.strip() for d in self.directories.split('\n') if d.strip()]


class SetupStatus(models.Model):
    """Singleton modell för att spåra initial setup-status"""
    is_completed = models.BooleanField(
        default=False,
        verbose_name="Setup klar",
        help_text="Indikerar om initial setup är genomförd"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Slutförd",
        help_text="När setup slutfördes"
    )

    class Meta:
        verbose_name = "Setup-status"
        verbose_name_plural = "Setup-status"

    def __str__(self):
        return f"Setup: {'Klar' if self.is_completed else 'Ej klar'}"

    def save(self, *args, **kwargs):
        """Säkerställ att det endast finns en instans"""
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Förhindra borttagning"""
        pass

    @classmethod
    def load(cls):
        """Hämta eller skapa setup-status"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    @classmethod
    def is_setup_complete(cls):
        """Kontrollera om setup är genomförd"""
        try:
            return cls.load().is_completed
        except Exception:
            # Om databasen inte är initierad returnera False
            return False

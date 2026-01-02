import os
from django.db import models
from django.conf import settings
from persons.models import Person


class DocumentType(models.Model):
    """Typ av dokument som kan kopplas till personer"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Namn/ID")
    target_directory = models.CharField(
        max_length=200,
        verbose_name="Målkatalog",
        help_text="Relativ sökväg, t.ex. 'dokument' eller 'dokument/födelse'"
    )
    filename = models.CharField(
        max_length=200,
        verbose_name="Filnamn",
        help_text="Standard filnamn för denna typ, t.ex. 'Sveriges befolkning 1970.txt'"
    )
    description = models.TextField(blank=True, verbose_name="Beskrivning")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Skapad")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Uppdaterad")

    class Meta:
        verbose_name = "Dokumenttyp"
        verbose_name_plural = "Dokumenttyper"
        ordering = ['name']

    def __str__(self):
        return self.name


class Document(models.Model):
    """Dokument kopplat till en person"""
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name="Person"
    )
    document_type = models.ForeignKey(
        DocumentType,
        on_delete=models.CASCADE,
        verbose_name="Dokumenttyp"
    )
    filename = models.CharField(max_length=255, verbose_name="Filnamn")
    file = models.FileField(
        upload_to='',  # Vi sätter path dynamiskt i save()
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Fil"
    )
    relative_path = models.CharField(max_length=500, verbose_name="Relativ sökväg")
    file_size = models.BigIntegerField(default=0, verbose_name="Filstorlek (bytes)")
    file_type = models.CharField(max_length=10, verbose_name="Filtyp")
    tags = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Taggar",
        help_text="Kommaseparerad lista"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Skapad")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Uppdaterad")
    file_modified_at = models.DateTimeField(null=True, blank=True, verbose_name="Fil modifierad")

    class Meta:
        verbose_name = "Dokument"
        verbose_name_plural = "Dokument"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['person', 'document_type']),
            models.Index(fields=['file_type']),
        ]

    def __str__(self):
        return f"{self.person.get_full_name()} - {self.filename}"

    def save(self, *args, **kwargs):
        """Sätt filstorlek och filtyp automatiskt om de inte redan är satta"""
        if self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except Exception:
                # Om vi inte kan få filstorleken, sätt den till 0
                self.file_size = 0

        if not self.file_type and self.filename:
            # Extrahera filtyp från filnamn
            _, ext = os.path.splitext(self.filename)
            self.file_type = ext.lstrip('.').lower()

        super().save(*args, **kwargs)

    def get_tags_list(self):
        """Returnera lista av taggar"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []

    def get_file_size_display(self):
        """Returnera filstorlek i läsbart format"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

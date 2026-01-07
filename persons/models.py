from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from core.models import Template


class Person(models.Model):
    """Person i släktforskning"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Användare")
    firstname = models.CharField(max_length=100, blank=True, verbose_name="Förnamn")
    surname = models.CharField(max_length=100, blank=True, verbose_name="Efternamn")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Födelsedatum")
    death_date = models.DateField(null=True, blank=True, verbose_name="Dödsdatum")
    age = models.IntegerField(null=True, blank=True, verbose_name="Ålder", help_text="Beräknad ålder")
    notes = models.TextField(blank=True, verbose_name="Anteckningar")
    directory_name = models.CharField(max_length=200, verbose_name="Katalognamn")
    template_used = models.ForeignKey(
        Template,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Mall använd"
    )
    is_main_person = models.BooleanField(
        default=False,
        verbose_name="Huvudperson",
        help_text="Huvudperson används som standard i trädvyn"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Skapad")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Uppdaterad")

    class Meta:
        verbose_name = "Person"
        verbose_name_plural = "Personer"
        ordering = ['surname', 'firstname']
        unique_together = [['user', 'directory_name']]
        indexes = [
            models.Index(fields=['surname', 'firstname']),
            models.Index(fields=['directory_name']),
        ]

    def __str__(self):
        if self.firstname and self.surname:
            return f"{self.firstname} {self.surname}"
        elif self.firstname:
            return self.firstname
        elif self.surname:
            return self.surname
        return self.directory_name

    def clean(self):
        """Validera att minst förnamn eller efternamn anges"""
        if not self.firstname and not self.surname:
            raise ValidationError("Minst ett av förnamn eller efternamn måste anges.")

        if self.birth_date and self.death_date:
            if self.death_date < self.birth_date:
                raise ValidationError("Dödsdatum kan inte vara före födelsedatum.")

    def get_full_name(self):
        """Returnera fullständigt namn"""
        return str(self)

    def get_years_display(self):
        """
        Returnera en formatterad sträng med födelse- och dödsår samt ålder.
        Format: "1950-2020 (70 år)" eller "1990 (34 år)" om personen lever.
        """
        if not self.birth_date:
            return None

        birth_year = self.birth_date.year
        if self.death_date:
            death_year = self.death_date.year
            if self.age:
                return f"{birth_year}-{death_year} ({self.age} år)"
            else:
                return f"{birth_year}-{death_year}"
        else:
            if self.age:
                return f"{birth_year} ({self.age} år)"
            else:
                return str(birth_year)

    def calculate_age(self):
        """
        Beräkna ålder baserat på födelsedatum och dödsdatum.

        Regler:
        - Om dödsdatum finns: beräkna ålder vid döden
        - Om personen lever och födelsedatum finns: beräkna nuvarande ålder
        - Endast om födelsedatum inte är mer än 100 år sedan
        - Returnerar None om åldern inte kan beräknas
        """
        from datetime import date

        if not self.birth_date:
            return None

        # Bestäm slutdatum för beräkningen
        if self.death_date:
            end_date = self.death_date
        else:
            end_date = date.today()
            # Kontrollera att födelsedatum inte är mer än 100 år sedan
            # Beräkna 100 år sedan genom att subtrahera 100 från årtalet
            hundred_years_ago = end_date.replace(year=end_date.year - 100)
            if self.birth_date < hundred_years_ago:
                return None

        # Beräkna ålder
        age = end_date.year - self.birth_date.year

        # Justera för om födelsedagen inte har inträffat ännu detta år
        if (end_date.month, end_date.day) < (self.birth_date.month, self.birth_date.day):
            age -= 1

        return age if age >= 0 else None

    def get_directory_path(self):
        """Returnera relativ sökväg till personens katalog"""
        return f"persons/{self.directory_name}"

    def get_full_directory_path(self):
        """Returnera fullständig absolut sökväg till personens katalog"""
        from core.utils import get_media_root
        import os
        return os.path.join(get_media_root(), self.get_directory_path())

    def get_all_relationships(self):
        """Return all relationships for this person"""
        from django.db.models import Q
        return PersonRelationship.objects.filter(Q(person_a=self) | Q(person_b=self))

    def get_relationships_by_type(self, relationship_type):
        """Get all persons related by a specific type"""
        from django.db.models import Q
        relationships = PersonRelationship.objects.filter(
            Q(person_a=self, relationship_a_to_b=relationship_type) |
            Q(person_b=self, relationship_b_to_a=relationship_type)
        )
        results = []
        for rel in relationships:
            if rel.person_a == self:
                results.append((rel.person_b, rel))
            else:
                results.append((rel.person_a, rel))
        return results

    def save(self, *args, **kwargs):
        """Spara personen och uppdatera ålder automatiskt"""
        # Beräkna och uppdatera ålder innan sparande
        self.age = self.calculate_age()
        super().save(*args, **kwargs)


class RelationshipType(models.TextChoices):
    """Relationship types with symmetric pairs"""
    PARENT = 'PARENT', 'Förälder'
    CHILD = 'CHILD', 'Barn'
    SPOUSE = 'SPOUSE', 'Make/Maka'
    SIBLING = 'SIBLING', 'Syskon'

    @classmethod
    def get_reciprocal(cls, relationship_type):
        """Return the reciprocal relationship type"""
        reciprocals = {
            cls.PARENT: cls.CHILD,
            cls.CHILD: cls.PARENT,
            cls.SPOUSE: cls.SPOUSE,
            cls.SIBLING: cls.SIBLING,
        }
        return reciprocals.get(relationship_type, relationship_type)


class PersonRelationship(models.Model):
    """Symmetric relationship between two persons"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Användare")
    person_a = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='relationships_as_a',
        verbose_name="Person A"
    )
    person_b = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='relationships_as_b',
        verbose_name="Person B"
    )
    relationship_a_to_b = models.CharField(
        max_length=20,
        choices=RelationshipType.choices,
        verbose_name="Relation A till B"
    )
    relationship_b_to_a = models.CharField(
        max_length=20,
        choices=RelationshipType.choices,
        verbose_name="Relation B till A"
    )
    notes = models.TextField(blank=True, verbose_name="Anteckningar")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Skapad")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Uppdaterad")

    class Meta:
        verbose_name = "Personrelation"
        verbose_name_plural = "Personrelationer"
        ordering = ['-created_at']
        unique_together = [['person_a', 'person_b']]
        indexes = [
            models.Index(fields=['person_a', 'person_b']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.person_a.get_full_name()} ({self.get_relationship_a_to_b_display()}) - {self.person_b.get_full_name()}"

    def clean(self):
        # Only validate if both persons are set
        if not self.person_a_id or not self.person_b_id:
            return

        # Prevent self-relationships
        if self.person_a_id == self.person_b_id:
            raise ValidationError("En person kan inte ha en relation med sig själv.")

        # Ensure both persons belong to same user
        if self.person_a.user_id != self.person_b.user_id:
            raise ValidationError("Båda personerna måste tillhöra samma användare.")

        if not self.user_id:
            self.user_id = self.person_a.user_id

        # Ensure canonical ordering (person_a.id < person_b.id)
        if self.person_a_id > self.person_b_id:
            self.person_a_id, self.person_b_id = self.person_b_id, self.person_a_id
            self.relationship_a_to_b, self.relationship_b_to_a = self.relationship_b_to_a, self.relationship_a_to_b

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class ChecklistCategory(models.TextChoices):
    """Kategorier för att organisera checklistobjekt"""
    RESEARCH = 'RESEARCH', 'Forskning'
    DOCUMENTS = 'DOCUMENTS', 'Dokument'
    SOURCES = 'SOURCES', 'Källor'
    VERIFICATION = 'VERIFICATION', 'Verifiering'
    OTHER = 'OTHER', 'Övrigt'


class ChecklistPriority(models.TextChoices):
    """Prioritetsnivåer för checklistobjekt"""
    LOW = 'LOW', 'Låg'
    MEDIUM = 'MEDIUM', 'Medel'
    HIGH = 'HIGH', 'Hög'
    CRITICAL = 'CRITICAL', 'Kritisk'


class ChecklistTemplate(models.Model):
    """Mall för checklistor"""
    name = models.CharField(max_length=200, unique=True, verbose_name="Namn")
    description = models.TextField(blank=True, verbose_name="Beskrivning")
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktiv",
        help_text="Om aktiv synkas ändringar automatiskt till alla personer"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Skapad")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Uppdaterad")

    class Meta:
        verbose_name = "Checklistmall"
        verbose_name_plural = "Checklistmallar"
        ordering = ['name']

    def __str__(self):
        return self.name


class ChecklistTemplateItem(models.Model):
    """Objekt i en checklistmall"""
    template = models.ForeignKey(
        ChecklistTemplate,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Mall"
    )
    title = models.CharField(max_length=200, verbose_name="Titel")
    description = models.TextField(blank=True, verbose_name="Beskrivning")
    category = models.CharField(
        max_length=20,
        choices=ChecklistCategory.choices,
        default=ChecklistCategory.OTHER,
        verbose_name="Kategori"
    )
    priority = models.CharField(
        max_length=20,
        choices=ChecklistPriority.choices,
        default=ChecklistPriority.MEDIUM,
        verbose_name="Prioritet"
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordning",
        help_text="Lägre nummer visas först"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Skapad")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Uppdaterad")

    class Meta:
        verbose_name = "Checklistmallsobjekt"
        verbose_name_plural = "Checklistmallsobjekt"
        ordering = ['order', 'title']
        unique_together = [['template', 'title']]
        indexes = [
            models.Index(fields=['template', 'order']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.template.name} - {self.title}"


class PersonChecklistItem(models.Model):
    """Checklistobjekt för en specifik person - synkat från mall eller anpassat"""
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='checklist_items',
        verbose_name="Person"
    )
    template_item = models.ForeignKey(
        ChecklistTemplateItem,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='person_items',
        verbose_name="Mallsobjekt",
        help_text="Om satt är detta synkat från mallen, annars är det anpassat"
    )
    # Cachade fält från mall (för anpassade objekt eller prestanda)
    title = models.CharField(max_length=200, verbose_name="Titel")
    description = models.TextField(blank=True, verbose_name="Beskrivning")
    category = models.CharField(
        max_length=20,
        choices=ChecklistCategory.choices,
        default=ChecklistCategory.OTHER,
        verbose_name="Kategori"
    )
    priority = models.CharField(
        max_length=20,
        choices=ChecklistPriority.choices,
        default=ChecklistPriority.MEDIUM,
        verbose_name="Prioritet"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Ordning")

    # Användarspecifik data
    is_completed = models.BooleanField(default=False, verbose_name="Avklarad")
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Avklarad datum"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Anteckningar",
        help_text="Personliga anteckningar för detta objekt"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Skapad")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Uppdaterad")

    class Meta:
        verbose_name = "Personchecklistobjekt"
        verbose_name_plural = "Personchecklistobjekt"
        ordering = ['person', 'order', 'title']
        unique_together = [['person', 'template_item']]
        indexes = [
            models.Index(fields=['person', 'is_completed']),
            models.Index(fields=['person', 'category']),
            models.Index(fields=['template_item']),
            models.Index(fields=['is_completed']),
        ]

    def __str__(self):
        status = "✓" if self.is_completed else "○"
        return f"{status} {self.person.get_full_name()} - {self.title}"

    def is_custom(self):
        """Returnerar True om detta är ett anpassat objekt (inte från mall)"""
        return self.template_item is None

    def save(self, *args, **kwargs):
        """Sätt completed_at timestamp när avklarad"""
        from django.utils import timezone

        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        elif not self.is_completed and self.completed_at:
            self.completed_at = None

        super().save(*args, **kwargs)


class BookmarkedPerson(models.Model):
    """Bokmärken för personer"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Användare")
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='bookmarks',
        verbose_name="Person"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Bokmärkt datum")

    class Meta:
        verbose_name = "Bokmärkt person"
        verbose_name_plural = "Bokmärkta personer"
        ordering = ['-created_at']
        unique_together = [['user', 'person']]
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.person.get_full_name()}"

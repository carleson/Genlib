# Genlib - Databasschema

Detta dokument beskriver databasens struktur och relationer i Genlib.

## ER-diagram (Entity-Relationship)

```
┌─────────────────┐
│   Django User   │
└────────┬────────┘
         │
         │ (owns)
         │
         ▼
┌─────────────────┐         ┌──────────────────┐
│     Person      │─────────│ PersonRelationship│
└────────┬────────┘         └──────────────────┘
         │                   (många-till-många via through)
         │
         ├────────────────────┬──────────────────┐
         │                    │                  │
         ▼                    ▼                  ▼
┌─────────────────┐  ┌─────────────────┐  ┌───────────────────┐
│    Document     │  │PersonChecklist  │  │  (relationer)     │
│                 │  │      Item       │  │                   │
└────────┬────────┘  └────────┬────────┘  └───────────────────┘
         │                    │
         │                    │
         ▼                    ▼
┌─────────────────┐  ┌─────────────────────┐
│  DocumentType   │  │ChecklistTemplateItem│
└─────────────────┘  └──────────┬──────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │  ChecklistTemplate   │
                     └──────────────────────┘


┌─────────────────────┐         ┌─────────────────┐
│   SystemConfig      │         │    Template     │
│   (singleton)       │         │  (katalogmallar)│
└─────────────────────┘         └─────────────────┘

┌─────────────────────┐
│   SetupStatus       │
│   (singleton)       │
└─────────────────────┘
```

## Modeller och fält

### User (Django built-in)
- id (PK)
- username
- email
- password
- ...

### Person
- **id** (PK)
- **user_id** (FK → User)
- firstname
- surname
- birth_date
- death_date
- age (calculated)
- notes
- directory_name (unique per user)
- template_used_id (FK → Template, nullable)
- created_at
- updated_at

**Unique constraint:** (user_id, directory_name)

### PersonRelationship
- **id** (PK)
- **user_id** (FK → User)
- **person_a_id** (FK → Person) - lägre ID
- **person_b_id** (FK → Person) - högre ID
- relationship_a_to_b (PARENT|CHILD|SPOUSE|SIBLING)
- relationship_b_to_a (PARENT|CHILD|SPOUSE|SIBLING)
- notes
- created_at
- updated_at

**Unique constraint:** (person_a_id, person_b_id)
**Enforced rule:** person_a.id < person_b.id

### DocumentType
- **id** (PK)
- name (unique)
- target_directory
- filename
- description
- created_at
- updated_at

### Document
- **id** (PK)
- **person_id** (FK → Person)
- **document_type_id** (FK → DocumentType)
- filename
- file (FileField)
- relative_path
- file_size
- file_type
- tags (comma-separated)
- created_at
- updated_at
- file_modified_at

**Index:** (person_id, document_type_id), (file_type)

### Template
- **id** (PK)
- name (unique)
- description
- directories (newline-separated)
- created_at
- updated_at

### ChecklistTemplate
- **id** (PK)
- name (unique)
- description
- is_active
- created_at
- updated_at

### ChecklistTemplateItem
- **id** (PK)
- **template_id** (FK → ChecklistTemplate)
- title
- description
- category (RESEARCH|DOCUMENTS|SOURCES|VERIFICATION|OTHER)
- priority (LOW|MEDIUM|HIGH|CRITICAL)
- order
- created_at
- updated_at

**Unique constraint:** (template_id, title)

### PersonChecklistItem
- **id** (PK)
- **person_id** (FK → Person)
- **template_item_id** (FK → ChecklistTemplateItem, nullable)
- title (cached from template)
- description (cached from template)
- category (cached from template)
- priority (cached from template)
- order (cached from template)
- is_completed
- completed_at
- notes (personal notes)
- created_at
- updated_at

**Unique constraint:** (person_id, template_item_id)
**Index:** (person_id, is_completed), (person_id, category)

### SystemConfig (Singleton)
- **id** (PK = 1, always)
- media_directory_path
- media_directory_name
- backup_directory_path

### SetupStatus (Singleton)
- **id** (PK = 1, always)
- is_completed
- completed_at

## Relationer

### 1:N (One-to-Many)

```
User ──< Person
        Person ──< Document
        Person ──< PersonChecklistItem
DocumentType ──< Document
Template ──< Person (nullable)
ChecklistTemplate ──< ChecklistTemplateItem
ChecklistTemplateItem ──< PersonChecklistItem (nullable)
```

### M:N (Many-to-Many)

```
Person >──< Person (via PersonRelationship)
```

## Kardinaliteter

```
User (1) ──────< (N) Person
   - En användare kan ha många personer
   - En person tillhör en användare

Person (1) ─────< (N) Document
   - En person kan ha många dokument
   - Ett dokument tillhör en person

DocumentType (1) ──< (N) Document
   - En dokumenttyp kan användas av många dokument
   - Ett dokument har en dokumenttyp

Person (1) ─────< (N) PersonChecklistItem
   - En person kan ha många checklistobjekt
   - Ett checklistobjekt tillhör en person

ChecklistTemplateItem (0..1) ──< (N) PersonChecklistItem
   - Ett mallobjekt kan användas av många personobjekt
   - Ett personobjekt kan vara kopplat till ett mallobjekt (eller null om anpassat)

Person (N) ─────< PersonRelationship >──── (N) Person
   - Många-till-många via through-table
   - Självrefererande relation
```

## Kaskadbeteende (on_delete)

```
User
  └─> Person: CASCADE
       ├─> Document: CASCADE
       ├─> PersonChecklistItem: CASCADE
       └─> PersonRelationship: CASCADE

DocumentType
  └─> Document: CASCADE

Template
  └─> Person: SET_NULL (nullable)

ChecklistTemplate
  └─> ChecklistTemplateItem: CASCADE
       └─> PersonChecklistItem: CASCADE

ChecklistTemplateItem
  └─> PersonChecklistItem: CASCADE (if not null)
```

## Queries - Exempel

### Hämta alla dokument för en person

```python
person = Person.objects.get(id=1)
documents = person.documents.all()

# Eller med filter
documents = Document.objects.filter(person=person)
```

### Hämta alla relationer för en person

```python
person = Person.objects.get(id=1)
relationships = person.get_all_relationships()

# Manuellt
from django.db.models import Q
relationships = PersonRelationship.objects.filter(
    Q(person_a=person) | Q(person_b=person)
)
```

### Hämta alla personer för en användare med dokumentantal

```python
from django.db.models import Count

persons = Person.objects.filter(user=request.user).annotate(
    document_count=Count('documents')
)

for person in persons:
    print(f"{person.get_full_name()}: {person.document_count} dokument")
```

### Hämta checklistprogress för en person

```python
person = Person.objects.get(id=1)
total = person.checklist_items.count()
completed = person.checklist_items.filter(is_completed=True).count()
percentage = (completed / total * 100) if total > 0 else 0
```

### Hämta alla dokument av viss typ för en användare

```python
doc_type = DocumentType.objects.get(name="Personbevis")
user_persons = Person.objects.filter(user=request.user)
documents = Document.objects.filter(
    person__in=user_persons,
    document_type=doc_type
)
```

### Skapa relation mellan två personer

```python
parent = Person.objects.get(id=1)
child = Person.objects.get(id=2)

rel = PersonRelationship.objects.create(
    user=request.user,
    person_a=parent,  # Ordningen fixas automatiskt i clean()
    person_b=child,
    relationship_a_to_b=RelationshipType.PARENT,
    relationship_b_to_a=RelationshipType.CHILD
)
```

### Hämta alla föräldrar för en person

```python
person = Person.objects.get(id=1)
parents = person.get_relationships_by_type(RelationshipType.PARENT)

for parent, relationship in parents:
    print(f"Förälder: {parent.get_full_name()}")
```

## Index-strategi

### Befintliga index

1. **Person:**
   - (surname, firstname) - för sortering och sökning
   - (directory_name) - för filsystemsoperationer

2. **Document:**
   - (person_id, document_type_id) - för filtrering per person och typ
   - (file_type) - för statistik och gruppering

3. **PersonChecklistItem:**
   - (person_id, is_completed) - för progressstatistik
   - (person_id, category) - för filtrering per kategori

4. **PersonRelationship:**
   - (person_a_id, person_b_id) - för unique constraint
   - (user_id) - för användarfiltrering

5. **ChecklistTemplateItem:**
   - (template_id, order) - för sortering
   - (category) - för filtrering

## Migrationer

### Hantera migrationer

```bash
# Skapa nya migrationer
uv run python manage.py makemigrations

# Applicera migrationer
uv run python manage.py migrate

# Visa migrationsstatus
uv run python manage.py showmigrations

# Visa SQL för en migration
uv run python manage.py sqlmigrate persons 0001
```

### Viktiga migrationer

- `persons/0001_initial.py` - Skapar Person-modellen
- `persons/0002_*.py` - Lägger till birth_date/death_date
- `persons/0003_*.py` - Lägger till PersonRelationship
- `persons/0004_*.py` - Lägger till ChecklistTemplate och ChecklistTemplateItem
- `persons/0005_*.py` - Lägger till age-fältet
- `documents/0001_initial.py` - Skapar DocumentType och Document
- `core/0001_initial.py` - Skapar SystemConfig, Template, SetupStatus

## Dataintegrity

### Constraints som enforcar integritet

1. **Unique constraints:**
   - Person: (user_id, directory_name)
   - PersonRelationship: (person_a_id, person_b_id)
   - DocumentType: name
   - Template: name
   - ChecklistTemplate: name
   - ChecklistTemplateItem: (template_id, title)
   - PersonChecklistItem: (person_id, template_item_id)

2. **Kanonisk ordning (PersonRelationship):**
   - Enforced via `clean()`: person_a.id < person_b.id
   - Förhindrar duplicerade relationer

3. **Singleton-modeller:**
   - SystemConfig och SetupStatus: pk=1 enforced via `save()`
   - `delete()` disabled

4. **Validering:**
   - Person: Minst förnamn eller efternamn
   - Person: Dödsdatum inte före födelsedatum
   - PersonRelationship: Inga självrelationer

## Prestandaoptimering

### Select Related / Prefetch Related

```python
# Optimera för att undvika N+1 queries

# För ForeignKey (select_related)
persons = Person.objects.select_related('template_used', 'user').all()

# För reverse ForeignKey och M2M (prefetch_related)
persons = Person.objects.prefetch_related('documents', 'checklist_items').all()

# Kombinera
persons = Person.objects.select_related('user').prefetch_related(
    'documents__document_type',
    'checklist_items__template_item'
).all()
```

### Annotate för aggregering

```python
from django.db.models import Count, Sum

persons = Person.objects.annotate(
    doc_count=Count('documents'),
    total_size=Sum('documents__file_size'),
    completed_checklist=Count('checklist_items', filter=Q(checklist_items__is_completed=True))
).filter(user=request.user)
```

---

**Se även:**
- [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) - Komplett teknisk guide
- [README.md](README.md) - Projektöversikt

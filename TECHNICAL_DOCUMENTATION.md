# Genlib - Teknisk Dokumentation

Detta dokument innehåller en komplett teknisk översikt över Genlib-projektet för att underlätta utveckling och underhåll.

## Innehållsförteckning

1. [Projektöversikt](#projektöversikt)
2. [Arkitektur](#arkitektur)
3. [Databasmodeller](#databasmodeller)
4. [Apps och Funktionalitet](#apps-och-funktionalitet)
5. [URL-struktur](#url-struktur)
6. [Filsystemstruktur](#filsystemstruktur)
7. [Viktiga Koncept](#viktiga-koncept)
8. [Arbetsflöden](#arbetsflöden)
9. [Management Commands](#management-commands)

---

## Projektöversikt

**Genlib** är ett Django-baserat dokumenthanteringssystem för släktforskning. Systemet lagrar dokumentmetadata i en databas medan faktiska filer lagras i filsystemet enligt en konfigurerbar struktur.

### Teknisk Stack
- **Framework:** Django 6.0
- **Python:** 3.12+
- **Databas:** SQLite3 (produktionsklar för PostgreSQL)
- **Frontend:** Django Templates + Bootstrap 5
- **Pakethanterare:** uv

### Nyckelprinciper
1. **Filsystembaserad lagring:** Dokument lagras som filer, databasen innehåller endast metadata
2. **Användarbaserad isolering:** Varje användare ser endast sina egna data
3. **Mallbaserad struktur:** Katalogstrukturer definieras via mallar
4. **Konfigurerbar media root:** Media-katalogen kan placeras var som helst

---

## Arkitektur

### Django Apps-struktur

```
genlib/
├── accounts/          # Användarautentisering och profiler
├── core/              # Gemensam funktionalitet, dashboard, setup
├── documents/         # Dokumenthantering och dokumenttyper
├── persons/           # Personhantering, relationer, checklistor
├── config/            # Django-projektkonfiguration
├── templates/         # Globala och app-specifika templates
├── static/            # Statiska filer (CSS, JS, bilder)
└── media/             # Användaruppladdade filer (dynamisk plats)
```

### App-beroenden

```
┌──────────┐
│ config   │ (URL root, settings)
└────┬─────┘
     │
     ├──────────────┬──────────────┬──────────────┐
     │              │              │              │
┌────▼────┐    ┌───▼────┐    ┌───▼──────┐  ┌───▼─────┐
│ accounts│    │  core  │    │ persons  │  │documents│
└─────────┘    └────────┘    └─────┬────┘  └────┬────┘
                                    │            │
                                    └────────────┘
                                         ▲
                                    (documents refererar persons)
```

### Request Flow

```
Användare → Django URL Router → View → Model/Form → Template → Användare
                    │                      │
                    │                      ▼
                    │              Filsystem (för filer)
                    │                      │
                    └──────────────────────┘
                           (media files)
```

---

## Databasmodeller

### 1. core.SystemConfig (Singleton)

Systemkonfiguration med dynamisk media root.

**Fält:**
- `media_directory_path`: Absolut eller relativ sökväg till media
- `media_directory_name`: Namn på katalogen (för URL)
- `backup_directory_path`: Sökväg till backup-katalog

**Metoder:**
- `load()`: Hämta eller skapa singleton-instans
- `get_media_root()`: Returnera absolut sökväg till media
- `get_backup_root()`: Returnera absolut sökväg till backups

**Användning:**
```python
from core.utils import get_media_root
media_path = get_media_root()  # Använd detta istället för settings.MEDIA_ROOT
```

### 2. core.Template

Mallar för katalogstrukturer.

**Fält:**
- `name`: Unikt namn (ex: "default", "extended")
- `description`: Beskrivning av mallen
- `directories`: Newline-separerad lista av kataloger

**Metoder:**
- `get_directories_list()`: Returnera lista av kataloger

**Fördefinierade mallar:**
- `default`: dokument/, bilder/, anteckningar/, media/, källor/
- `extended`: Utökad struktur med underkategorier
- `minimal`: dokument/, anteckningar/

### 3. core.SetupStatus (Singleton)

Spårar om initial setup är genomförd.

**Fält:**
- `is_completed`: Boolean, om setup är klar
- `completed_at`: När setup slutfördes

**Metoder:**
- `load()`: Hämta singleton
- `is_setup_complete()`: Statisk metod för att kontrollera status

### 4. persons.Person

Huvudmodell för personer i släktforskningen.

**Fält:**
- `user`: ForeignKey till Django User (ägandeskap)
- `firstname`: Förnamn
- `surname`: Efternamn
- `birth_date`: Födelsedatum (optional)
- `death_date`: Dödsdatum (optional)
- `age`: Beräknad ålder (auto-uppdateras)
- `notes`: Fritextanteckningar
- `directory_name`: Katalognamn i filsystemet (unikt per användare)
- `template_used`: ForeignKey till Template (optional)
- `created_at`, `updated_at`: Timestamps

**Metoder:**
- `get_full_name()`: Returnera fullständigt namn
- `get_years_display()`: Format: "1950-2020 (70 år)"
- `calculate_age()`: Beräkna ålder (endast om <100 år sedan eller död)
- `get_directory_path()`: Relativ sökväg: "persons/{directory_name}"
- `get_full_directory_path()`: Absolut sökväg till personens katalog
- `get_all_relationships()`: Hämta alla relationer
- `get_relationships_by_type(type)`: Hämta relationer av viss typ

**Validering:**
- Minst förnamn eller efternamn måste anges
- Dödsdatum kan inte vara före födelsedatum

**Unika constraints:**
- `(user, directory_name)` måste vara unikt

### 5. persons.PersonRelationship

Symmetriska relationer mellan personer.

**Fält:**
- `user`: ForeignKey till User
- `person_a`: ForeignKey till Person (lägre ID)
- `person_b`: ForeignKey till Person (högre ID)
- `relationship_a_to_b`: RelationshipType (A's relation till B)
- `relationship_b_to_a`: RelationshipType (B's relation till A)
- `notes`: Anteckningar

**RelationshipType:**
- `PARENT` ↔ `CHILD`
- `SPOUSE` ↔ `SPOUSE`
- `SIBLING` ↔ `SIBLING`

**Viktigt:**
- Kanonisk ordning: `person_a.id < person_b.id` (enforced i `clean()`)
- En relation representerar båda riktningarna

**Exempel:**
```python
# Person A (id=1) är förälder till Person B (id=2)
PersonRelationship(
    person_a=person_1,  # Lägre ID
    person_b=person_2,  # Högre ID
    relationship_a_to_b=RelationshipType.PARENT,
    relationship_b_to_a=RelationshipType.CHILD
)
```

### 6. persons.ChecklistTemplate & ChecklistTemplateItem

Mallar för checklistor som kan synkas till personer.

**ChecklistTemplate:**
- `name`: Namn på mallen
- `description`: Beskrivning
- `is_active`: Om mallen är aktiv (synkas automatiskt)

**ChecklistTemplateItem:**
- `template`: ForeignKey till ChecklistTemplate
- `title`: Titel på checklistobjekt
- `description`: Beskrivning
- `category`: ChecklistCategory (RESEARCH, DOCUMENTS, SOURCES, etc.)
- `priority`: ChecklistPriority (LOW, MEDIUM, HIGH, CRITICAL)
- `order`: Sorteringsordning

### 7. persons.PersonChecklistItem

Person-specifika checklistobjekt (synkade från mall eller anpassade).

**Fält:**
- `person`: ForeignKey till Person
- `template_item`: ForeignKey till ChecklistTemplateItem (null om anpassat)
- `title`, `description`, `category`, `priority`, `order`: Cachade från mall
- `is_completed`: Boolean
- `completed_at`: Timestamp när avklarad
- `notes`: Personliga anteckningar

**Metoder:**
- `is_custom()`: Returnerar True om inte kopplad till mall

### 8. documents.DocumentType

Definierar typer av dokument och var de ska lagras.

**Fält:**
- `name`: Namn/ID (ex: "Personbevis", "Folkräkning 1950")
- `target_directory`: Relativ katalog (ex: "dokument/personbevis")
- `filename`: Standardfilnamn (ex: "personbevis.pdf")
- `description`: Beskrivning

**Användning:**
Används för att matcha och kategorisera dokument i filsystemet.

**Exempel:**
```python
DocumentType(
    name="Personbevis",
    target_directory="dokument/personbevis",
    filename="personbevis.pdf"
)
```

### 9. documents.Document

Metadata för dokument kopplade till personer.

**Fält:**
- `person`: ForeignKey till Person
- `document_type`: ForeignKey till DocumentType
- `filename`: Filnamn
- `file`: FileField (sökväg i media)
- `relative_path`: Relativ sökväg från personens katalog
- `file_size`: Storlek i bytes
- `file_type`: Filtillägg (ex: "pdf", "txt")
- `tags`: Kommaseparerade taggar
- `file_modified_at`: Timestamp för filmodifiering

**Filsökväg i filsystemet:**
```
{media_root}/persons/{person.directory_name}/{document_type.target_directory}/{filename}
```

**Metoder:**
- `get_tags_list()`: Returnera lista av taggar
- `get_file_size_display()`: Formaterad storlek (KB, MB, GB)

**Relationer:**
```
User → Person → Document → DocumentType
              ↓
        PersonChecklistItem
        PersonRelationship
```

---

## Apps och Funktionalitet

### 1. accounts

**Ansvar:** Användarautentisering och registrering

**Vyer:**
- `signup`: Registrera ny användare
- Django's inbyggda vyer för login, logout, password reset

**URL-er:**
- `/accounts/signup/`
- `/accounts/login/`
- `/accounts/logout/`

**Templates:**
- `accounts/signup.html`
- `accounts/login.html`

### 2. core

**Ansvar:** Gemensam funktionalitet, dashboard, setup, system config

**Vyer:**

#### Dashboard (`dashboard`)
- Visar översikt för inloggad användare
- Statistik: antal personer, dokument, total storlek
- Senaste personer och dokument
- Filtypsfördelning

#### Initial Setup (`initial_setup`)
- Wizard för första gången applikationen startas
- Skapar superuser
- Konfigurerar media och backup-kataloger
- Markerar setup som klar

#### Backup & Restore
- `backup_database`: Skapar ZIP-backup av databas + media
- `restore_database`: Återställer från backup
- `download_backup`: Ladda ner backup-fil

**URL-er:**
- `/` - Dashboard (kräver login)
- `/setup/` - Initial setup
- `/system/backup/` - Backup
- `/system/restore/` - Restore

**Management Commands:**
- `setup_initial_data`: Skapar fördefinierade mallar och dokumenttyper
- `backup`: CLI-backup
- `restore`: CLI-restore

### 3. persons

**Ansvar:** Hantering av personer, relationer, checklistor

**Vyer:**

#### PersonListView
- Lista alla personer för användaren
- Sök och filtrera
- Sortering

#### PersonDetailView (`persons/views.py:61-127`)
- Detaljvy för person
- Visar personuppgifter, statistik
- Dokument grupperade per typ
- Relationer grupperade per typ (föräldrar, barn, make/maka, syskon)
- Checklistprogress

**Verktygsmenyn i PersonDetailView:**
- Döp om person (modal)
- Duplicera person
- **Ladda om dokument** (synkronisera från filsystem) ← NY FUNKTION
- Exportera data (JSON/CSV)
- Kronologisk rapport

#### PersonCreateView & PersonUpdateView
- Formulär för att skapa/redigera person
- Validering av namn och datum

#### PersonDeleteView
- Ta bort person

#### PersonRelationshipCreateView
- Skapa relation mellan två personer
- Automatisk kanonisk ordning (person_a.id < person_b.id)

#### PersonChecklistView
- Visa och filtrera checklistobjekt per kategori/status
- Gruppering per kategori
- Framstegsstatistik

#### ChecklistItemToggleView (AJAX)
- Bocka av/på checklistobjekt
- Returnerar JSON

#### PersonRenameView (`persons/views.py:473-556`)
- Döp om person och flytta katalog atomärt
- Använder transaction för säkerhet
- Validerar att ny katalog inte finns

#### PersonDuplicateView (`persons/views.py:558-674`)
- Duplicera person med relationer och checklista
- Skapar unikt directory_name med "_kopia" suffix

#### PersonExportView (`persons/views.py:676-861`)
- Exportera persondata till JSON eller CSV
- Valfria delar: relationer, checklista, dokument

#### PersonChronologicalReportView
- Kronologisk rapport över alla dokument
- Grupperat per år

#### PersonDocumentSyncView (`persons/views.py:906-1053`) ← NY
**Viktig funktion för att synkronisera filsystem med databas**

**Logik:**
1. Skannar personens katalog rekursivt (`person_dir.rglob('*')`)
2. Matchar filer mot DocumentType-definitioner
3. **Lägger till** nya dokument som hittas i filsystemet
4. **Uppdaterar** metadata för befintliga (storlek, modifieringstid)
5. **Tar bort** dokument som inte längre finns i filsystemet
6. Visar statistik: X tillagda, Y uppdaterade, Z borttagna

**Filmatching:**
- Filer matchas mot `(target_directory, filename)` från DocumentType
- Endast filer som matchar en DocumentType läggs till
- Andra filer ignoreras

**Användning:**
- POST till `/persons/<pk>/sync-documents/`
- Bekräftelsedialog i UI
- Redirect tillbaka till PersonDetailView

**URL-er:**
- `/persons/` - Lista
- `/persons/<pk>/` - Detalj
- `/persons/create/` - Skapa
- `/persons/<pk>/edit/` - Redigera
- `/persons/<pk>/delete/` - Ta bort
- `/persons/<pk>/relationships/add/` - Lägg till relation
- `/persons/<pk>/checklist/` - Checklista
- `/persons/<pk>/rename/` - Döp om
- `/persons/<pk>/duplicate/` - Duplicera
- `/persons/<pk>/export/` - Exportera
- `/persons/<pk>/sync-documents/` - Synkronisera dokument ← NY

### 4. documents

**Ansvar:** Hantering av dokument och dokumenttyper

**Vyer:**

#### DocumentTypeListView, CreateView, UpdateView, DeleteView
- CRUD för dokumenttyper
- Endast tillgängligt för inloggade användare

#### DocumentCreateView (`documents/views.py:62-182`)
**Två sätt att skapa dokument:**

1. **Ladda upp fil:**
   - Användare väljer fil
   - Fil sparas till: `{media_root}/persons/{person.directory_name}/{doc_type.target_directory}/{filename}`
   - Metadata (storlek, typ) extraheras automatiskt

2. **Skapa textfil:**
   - Användare skriver text direkt i formulär
   - Text sparas som .txt/.md fil

**Viktiga steg:**
- Katalogstruktur skapas automatiskt (`os.makedirs`)
- `relative_path` sätts från `doc_type.target_directory + filename`
- `file.name` sätts till sökväg i media

#### DocumentUpdateView
- Redigera dokumentmetadata
- För textfiler: redigera innehåll direkt

#### DocumentDeleteView
- Ta bort dokument från databas och filsystem

#### DocumentViewUpdateView (`documents/views.py:286-357`)
- Förenklad vy för att visa och redigera dokument
- Stöd för textfiler (txt, md): visa och redigera innehåll
- Stöd för PDF: visa inline
- Stöd för bilder: visa inline
- Uppdatera källinformation

#### document_download
- Ladda ner dokument
- Content-Disposition header för filnamn
- MIME-type detection

**URL-er:**
- `/documents/types/` - Lista dokumenttyper
- `/documents/types/create/` - Skapa dokumenttyp
- `/documents/create/` - Skapa dokument
- `/documents/<pk>/view/` - Visa/redigera dokument
- `/documents/<pk>/download/` - Ladda ner dokument
- `/documents/<pk>/delete/` - Ta bort dokument

---

## URL-struktur

### Komplett URL-mappning

```
/                                    → core:dashboard
/setup/                              → core:initial_setup

/accounts/signup/                    → accounts:signup
/accounts/login/                     → accounts:login
/accounts/logout/                    → accounts:logout

/persons/                            → persons:list
/persons/create/                     → persons:create
/persons/<pk>/                       → persons:detail
/persons/<pk>/edit/                  → persons:update
/persons/<pk>/delete/                → persons:delete
/persons/<pk>/relationships/add/     → persons:relationship_create
/persons/<pk>/checklist/             → persons:checklist
/persons/<pk>/rename/                → persons:rename
/persons/<pk>/duplicate/             → persons:duplicate
/persons/<pk>/export/                → persons:export
/persons/<pk>/chronological-report/  → persons:chronological_report
/persons/<pk>/sync-documents/        → persons:sync_documents

/documents/types/                    → documents:type_list
/documents/types/create/             → documents:type_create
/documents/create/                   → documents:create
/documents/<pk>/view/                → documents:view
/documents/<pk>/download/            → documents:download
/documents/<pk>/delete/              → documents:delete

/system/backup/                      → core:backup
/system/restore/                     → core:restore

/admin/                              → Django Admin
```

---

## Filsystemstruktur

### Media Root

Konfigureras via `SystemConfig.media_directory_path`. Kan vara absolut eller relativ.

```
{media_root}/
└── persons/
    ├── {person_1_directory_name}/
    │   ├── dokument/
    │   │   ├── personbevis/
    │   │   │   └── personbevis.pdf
    │   │   └── folkräkning/
    │   │       └── folkräkning_1950.txt
    │   ├── bilder/
    │   │   └── porträtt.jpg
    │   └── anteckningar/
    │       └── noter.txt
    ├── {person_2_directory_name}/
    │   └── ...
    └── ...
```

### Backups

```
{backup_root}/
├── genlib_backup_2025-01-05_16-30-00.zip
├── genlib_backup_2025-01-04_10-15-23.zip
└── safety/  (automatiska säkerhetskopior)
    └── ...
```

**Backup-innehåll:**
- `db.sqlite3` (databas)
- `media/` (alla filer)

---

## Viktiga Koncept

### 1. Dynamisk Media Root

**Problem:** Användare vill kunna placera media-katalogen var som helst (extern disk, molntjänst, etc.)

**Lösning:**
- `SystemConfig` lagrar sökväg
- `core.utils.get_media_root()` returnerar aktuell sökväg
- Används överallt istället för `settings.MEDIA_ROOT`

**Exempel:**
```python
from core.utils import get_media_root
person_dir = Path(get_media_root()) / 'persons' / person.directory_name
```

### 2. Mallbaserad Katalogstruktur

**Syfte:** Standardisera katalogstrukturer för olika forskningstyper

**Användning:**
1. Välj mall när person skapas
2. Katalogerna skapas automatiskt vid behov
3. DocumentType mappar till specifika kataloger

### 3. Dokumenttyp-mappning

**Koncept:** Koppla filtyper till platser i filsystemet

**Exempel:**
```python
DocumentType(
    name="Folkräkning 1950",
    target_directory="dokument/folkräkning",
    filename="folkräkning_1950.txt"
)
```

När man skapar dokument:
1. Välj DocumentType
2. System vet automatiskt var filen ska ligga
3. Filsökväg = `persons/{person.directory_name}/{target_directory}/{filename}`

### 4. Dokumentsynkronisering (Ny funktion)

**Syfte:** Tillåt manuell filhantering utanför applikationen

**Användningsfall:**
- Användaren lägger till filer direkt i filsystemet (via FTP, filhanterare, etc.)
- Användaren tar bort filer manuellt
- Filer uppdateras externt

**Lösning:** PersonDocumentSyncView
- Skannar filsystemet
- Jämför med databas
- Synkroniserar skillnader

**Begränsning:** Endast filer som matchar en DocumentType läggs till automatiskt

### 5. Kanonisk Relations-ordning

**Problem:** Förhindra duplicerade relationer (A→B och B→A)

**Lösning:**
- Alltid `person_a.id < person_b.id`
- `clean()` metod enforcar detta
- Båda riktningar lagras i samma post

### 6. Singleton-modeller

**SystemConfig** och **SetupStatus** är singletons:
- Endast en instans (pk=1)
- `save()` overridear pk till 1
- `delete()` förhindras
- `load()` classmethod för att hämta/skapa

### 7. Automatisk Åldersberäkning

**Regler:**
- Om död: beräkna ålder vid döden
- Om levande: beräkna nuvarande ålder
- Endast om födda inom 100 år
- Uppdateras automatiskt vid `save()`

### 8. Checklist-synkronisering

**Koncept:** Mall-baserade checklistor som synkas till personer

**Typer:**
- **Mall-synkade:** Kopplade till `ChecklistTemplateItem`
- **Anpassade:** `template_item=None`

**Funktionalitet:**
- Om mall uppdateras, synkas ändringar till personer (via signals)
- Personliga anteckningar och completion-status bevaras

---

## Arbetsflöden

### 1. Skapa ny person

```
1. Användare: Klicka "Lägg till person"
2. PersonCreateView: Visa formulär
3. Välj mall (optional)
4. Ange namn, datum, anteckningar
5. Submit
6. Person skapas i databas
7. Katalog skapas: {media_root}/persons/{directory_name}/
8. Om mall vald: Underkataloger skapas
9. Signal: Skapa checklistobjekt från aktiva mallar
10. Redirect till PersonDetailView
```

### 2. Ladda upp dokument

```
1. PersonDetailView → "Lägg till dokument"
2. DocumentCreateView: Formulär
3. Välj person (förifyllt om från PersonDetail)
4. Välj DocumentType
5. Antingen:
   a) Ladda upp fil
   b) Skriv text direkt
6. Submit
7. Fil sparas: {media_root}/persons/{person_dir}/{target_dir}/{filename}
8. Katalog skapas om den inte finns
9. Document-post skapas i DB
10. Redirect till PersonDetailView
```

### 3. Synkronisera dokument från filsystem (NY)

```
1. PersonDetailView → Verktyg → "Ladda om dokument"
2. Bekräftelsedialog
3. POST till PersonDocumentSyncView
4. Skanna {media_root}/persons/{person.directory_name}/ rekursivt
5. För varje fil:
   a) Hitta i databas via relative_path
   b) Om finns: Uppdatera metadata om ändrad
   c) Om inte finns: Matcha mot DocumentType
      - Om match: Skapa Document-post
      - Om ingen match: Ignorera
6. För varje Document i DB:
   a) Kontrollera om fil finns i filsystemet
   b) Om inte: Ta bort från DB
7. Visa statistik: X tillagda, Y uppdaterade, Z borttagna
8. Redirect till PersonDetailView
```

### 4. Skapa relation

```
1. PersonDetailView → "Lägg till relation"
2. PersonRelationshipCreateView
3. Välj andra personen
4. Välj relationstyp (förälder, barn, make/maka, syskon)
5. System beräknar reciprok relation automatiskt
6. Submit
7. Clean() enforcar kanonisk ordning
8. Relation skapas
9. Redirect till PersonDetailView
```

### 5. Initial Setup

```
1. Första besök på applikationen
2. Redirect till /setup/
3. InitialSetupForm:
   a) Skapa superuser (username, password, email)
   b) Konfigurera media_directory_path
   c) Konfigurera backup_directory_path
4. Submit
5. User skapas
6. SystemConfig uppdateras
7. SetupStatus markeras som klar
8. User loggas in automatiskt
9. Redirect till dashboard
10. Kör `python manage.py setup_initial_data` manuellt
    (skapar mallar och dokumenttyper)
```

### 6. Backup & Restore

**Backup:**
```
1. Dashboard → "Backup"
2. BackupView
3. Skapar ZIP med:
   - db.sqlite3
   - Hela media/-katalogen
4. Sparar till {backup_root}/genlib_backup_{timestamp}.zip
5. Download eller lämna på servern
```

**Restore:**
```
1. Dashboard → "Restore"
2. RestoreView: Välj backup-fil
3. Upload backup.zip
4. Extrahera till temp-katalog
5. Stoppa applikation (viktigt!)
6. Ersätt db.sqlite3
7. Ersätt media/-katalogen
8. Starta applikation
9. Redirect till dashboard
```

---

## Management Commands

### 1. setup_initial_data

**Syfte:** Skapa fördefinierade mallar och dokumenttyper

**Användning:**
```bash
uv run python manage.py setup_initial_data
```

**Skapar:**
- Mallar: default, extended, minimal
- DocumentTypes: Personbevis, Födelseattest, etc.

**När:** Efter migrationer, vid första setup

### 2. backup

**Syfte:** Skapa backup via CLI

**Användning:**
```bash
uv run python manage.py backup
```

**Output:** ZIP-fil i backup-katalogen

### 3. restore

**Syfte:** Återställa från backup via CLI

**Användning:**
```bash
uv run python manage.py restore <backup-file>
```

**Varning:** Stoppa servern först!

---

## Säkerhet

### Implementerade skydd

1. **CSRF Protection:** Django built-in
2. **XSS Protection:** Django auto-escape i templates
3. **SQL Injection:** Django ORM
4. **Authentication:** LoginRequiredMixin på alla vyer
5. **User Isolation:** Alla queries filtreras på `user=request.user`
6. **File Upload Validation:** Filtyper valideras

### Viktiga principer

- Aldrig använd `raw SQL` utan parametrar
- Alltid filtrera på `user` i querysets
- Validera all user input i forms
- Använd `@login_required` eller `LoginRequiredMixin`

---

## Felsökning

### Vanliga problem

#### 1. Media files visas inte
**Orsak:** Media root inte korrekt konfigurerad
**Lösning:** Kontrollera SystemConfig.media_directory_path

#### 2. Dokumentsynkronisering hittar inga filer
**Orsak:** Inga filer matchar DocumentType-definitioner
**Lösning:** Skapa DocumentTypes som matchar `(target_directory, filename)`

#### 3. Relation kan inte skapas
**Orsak:** Relationen finns redan
**Lösning:** Kontrollera båda riktningar (kanonisk ordning)

#### 4. Setup-wizard dyker upp igen
**Orsak:** SetupStatus.is_completed = False
**Lösning:**
```python
from core.models import SetupStatus
status = SetupStatus.load()
status.is_completed = True
status.save()
```

---

## Utvecklingsriktlinjer

### Namnkonventioner

- **Vyer:** `{Model}{Action}View` (ex: PersonCreateView)
- **Templates:** `{app}/{model}_{action}.html` (ex: persons/person_form.html)
- **URL-namn:** `{app}:{action}` (ex: persons:create)

### Kodstil

- Följ PEP 8
- Använd type hints
- Docstrings i Google-format
- Max 88 tecken per rad (Black-standard)

### Tester

```bash
# Kör alla tester
uv run pytest

# Med coverage
uv run pytest --cov=src --cov-report=term-missing
```

### Git workflow

- `main` - stabil kod
- `feature/<namn>` - nya funktioner
- `fix/<namn>` - buggfixar

**Commit-format:**
```
feat: Lägg till dokumentsynkronisering
fix: Rätta åldersberäkning för personer över 100 år
docs: Uppdatera teknisk dokumentation
test: Lägg till tester för PersonDocumentSyncView
```

---

## Snabbreferens

### Vanliga kod-snippets

#### Hämta media root
```python
from core.utils import get_media_root
media_path = get_media_root()
```

#### Skapa dokument programmatiskt
```python
from documents.models import Document, DocumentType
from persons.models import Person
from pathlib import Path

person = Person.objects.get(id=1)
doc_type = DocumentType.objects.get(name="Personbevis")

doc = Document.objects.create(
    person=person,
    document_type=doc_type,
    filename="personbevis.pdf",
    relative_path=f"{doc_type.target_directory}/personbevis.pdf",
    file_size=12345,
    file_type="pdf"
)
```

#### Skapa relation
```python
from persons.models import Person, PersonRelationship, RelationshipType

parent = Person.objects.get(id=1)
child = Person.objects.get(id=2)

# Skapa relationen (kanonisk ordning enforced automatiskt)
rel = PersonRelationship.objects.create(
    user=request.user,
    person_a=parent,  # eller child, ordningen fixas i clean()
    person_b=child,
    relationship_a_to_b=RelationshipType.PARENT,
    relationship_b_to_a=RelationshipType.CHILD
)
```

#### Synkronisera dokument programmatiskt
```python
from persons.views import PersonDocumentSyncView
from django.test import RequestFactory

factory = RequestFactory()
request = factory.post('/persons/1/sync-documents/')
request.user = user

view = PersonDocumentSyncView()
response = view.post(request, pk=1)
```

---

## Uppdateringshistorik

| Datum | Ändring | Utvecklare |
|-------|---------|------------|
| 2026-01-05 | Lagt till PersonDocumentSyncView för filsystemsynkronisering | Claude |
| 2026-01-05 | Skapade initial teknisk dokumentation | Claude |

---

**Denna dokumentation uppdateras kontinuerligt. Vid frågor, se även:**
- README.md (översikt)
- GENLIB_OVERVIEW.md (funktionsöversikt)
- INSTALLATION.md (installation)
- CLAUDE.md (utvecklingsmiljö för AI-assistenter)

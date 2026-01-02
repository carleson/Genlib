# Genlib - Systemöversikt

## Vad har implementerats?

### ✅ Komplett MVP (Minimum Viable Product)

#### 1. Användarhantering
- Registrering av nya användare
- Inloggning och utloggning
- Säker autentisering med Django's inbyggda system
- Användarspecifik data (varje användare ser endast sina egna personer och dokument)

#### 2. Personhantering (CRUD)
- **Skapa** nya personer med:
  - Förnamn och efternamn
  - Födelse- och dödsår/datum
  - Anteckningar
  - Unikt katalognamn
  - Valbara katalogstrukturmallar
- **Visa** lista över personer med:
  - Sökning i namn och katalognamn
  - Sortering (efternamn, förnamn, senast skapad)
  - Paginering (20 personer per sida)
- **Detaljvy** för person med:
  - All personinformation
  - Statistik (antal dokument, total storlek)
  - Lista över dokument grupperade per typ
- **Redigera** personuppgifter
- **Ta bort** personer (med varning om dokument)

#### 3. Dokumenttypshantering
- **Fördefinierade dokumenttyper**:
  - personbevis, födelseattest, vigselbevis, dödsbevis
  - folkräkning, kyrkbok
  - porträtt, anteckning
- **CRUD för dokumenttyper**:
  - Skapa egna dokumenttyper
  - Definiera målkatalog och standardfilnamn
  - Beskrivning för varje typ
  - Ta bort och redigera typer

#### 4. Dokumenthantering
- **Ladda upp dokument** till personer:
  - Välj person och dokumenttyp
  - Ladda upp fil (max 10MB)
  - Ange källinformation (VIKTIGT!)
  - Beskrivning och taggar
  - Automatisk filstorlek och filtypsdetektering
- **Visa dokument**:
  - Grupperat per dokumenttyp på personens detaljsida
  - Nedladdning av filer
  - Metadata (storlek, typ, källa)
- **Redigera** dokumentmetadata
- **Ta bort** dokument (från databas och filsystem)

#### 5. Katalogstrukturmallar
- **Tre fördefinierade mallar**:
  - **default**: dokument/, bilder/, anteckningar/, media/, källor/
  - **extended**: Utökad struktur med underkategorier för födelse, vigsel, död, folkräkning, etc.
  - **minimal**: dokument/, anteckningar/
- **CRUD för mallar**:
  - Skapa egna mallar via Django Admin
  - Definiera katalogstruktur (en rad per katalog)

#### 6. Dashboard
- **Statistiköversikt**:
  - Totalt antal personer
  - Totalt antal dokument
  - Total filstorlek
  - Antal olika filtyper
- **Senaste aktivitet**:
  - Senast tillagda personer
  - Senast tillagda dokument
- **Snabblänkar** till vanliga funktioner

#### 7. Sökning och filtrering
- **Personsökning**:
  - Fritextsökning i förnamn, efternamn, katalognamn, anteckningar
  - Sortering efter olika fält
- **Dokumentgruppering**:
  - Automatisk gruppering per dokumenttyp på personvyn

#### 8. Teknisk implementation

##### Backend
- Django 6.0 (senaste stabila version)
- SQLite3 databas
- Django ORM för databasoperationer
- Säker filuppladdning med validering

##### Frontend
- Django Templates
- Bootstrap 5 för styling
- Responsiv design
- Bootstrap Icons
- Intuitivt användargränssnitt på svenska

##### Databasmodeller
1. **Template** (core app):
   - Mallar för katalogstrukturer
   - Används vid skapande av personer

2. **Person** (persons app):
   - Personinformation
   - Kopplad till användare
   - Unikt katalognamn per användare
   - Relation till Template

3. **DocumentType** (documents app):
   - Konfigurerbara dokumenttyper
   - Målkatalog och standardfilnamn
   - Beskrivning

4. **Document** (documents app):
   - Dokument kopplade till personer
   - Filuppladdning
   - Metadata (källa, beskrivning, taggar)
   - Automatisk filstorlek och filtypsdetektering

##### Säkerhet
- CSRF-skydd (Django inbyggt)
- XSS-skydd (Django inbyggt)
- SQL Injection-skydd (Django ORM)
- Autentisering krävs för alla operationer
- Användare ser endast sin egen data
- Säker filuppladdning med validering

##### Filhantering
- Strukturerad katalogstruktur: `/media/users/{user_id}/persons/{directory_name}/{relative_path}`
- Stöd för: txt, pdf, jpg, png, gif
- Maximal filstorlek: 10MB per fil
- Automatisk rensning vid borttagning

### 🎨 Användargränssnitt

#### Navigation
- Toppnavigering med:
  - Hem (Dashboard)
  - Personer
  - Dokumenttyper
  - Användarmenyn (utloggning)
- Responsiv design (fungerar på mobil, tablet, desktop)

#### Färgschema
- Bootstrap 5 standard färgpalett
- Tydliga knappar och ikoner
- Färgkodad statistik på dashboard

#### Meddelanden
- Success-meddelanden (gröna)
- Warning-meddelanden (gula)
- Error-meddelanden (röda)
- Info-meddelanden (blå)

### 📋 Django Admin

Django Admin (http://localhost:8000/admin/) ger full kontroll över:
- Användare
- Personer
- Dokument
- Dokumenttyper
- Mallar

### 🚀 Management Commands

**setup_initial_data**:
- Skapar fördefinierade mallar (default, extended, minimal)
- Skapar fördefinierade dokumenttyper
- Körbar vid behov: `uv run python manage.py setup_initial_data`

## Vad är INTE implementerat än?

Följande funktioner är dokumenterade i README.md men INTE implementerade i denna MVP:

### Framtida funktioner:
1. **Relationhantering**:
   - Skapa relationer mellan personer (förälder-barn, gifta)
   - Visualisera släktträd

2. **Delning och samarbete**:
   - Dela forskning med andra användare
   - Olika behörighetsnivåer

3. **Import/Export**:
   - GEDCOM-import/export
   - PDF-rapporter
   - Backup/restore

4. **Avancerad sökning**:
   - Fulltext-sökning i dokumentinnehåll
   - Geografisk sökning
   - Tidslinjevisning

5. **AI-funktioner**:
   - OCR för skannade dokument
   - Automatisk datering
   - Namnigenkänning

6. **Textdokumentredigering**:
   - Skapa textdokument i webbgränssnitt
   - Redigera dokumentinnehåll för textfiler

7. **Avancerad filtrering**:
   - Filtrera personer på födelseår/dödsår (från-till)
   - Filtrera på mall använd
   - Filtrera på "har dokument / saknar dokument"

8. **Dokumentsökning**:
   - Söka i dokument (filnamn, beskrivning, källinformation)
   - Filtrera dokument på typ, filtyp, datum

## Arkitektur

```
genlib/
├── config/              # Django settings och huvudsakliga URL-konfiguration
│   ├── settings.py      # Alla inställningar (databas, media, static, apps)
│   ├── urls.py          # Huvudsakliga URL-routing
│   └── wsgi.py          # WSGI-konfiguration
│
├── core/                # Gemensam funktionalitet
│   ├── models.py        # Template-modellen
│   ├── views.py         # Dashboard-vy
│   ├── urls.py          # Core URLs
│   ├── admin.py         # Template admin
│   └── management/
│       └── commands/
│           └── setup_initial_data.py  # Management command
│
├── accounts/            # Användarautentisering
│   ├── views.py         # Login, Register, Logout vyer
│   └── urls.py          # Accounts URLs
│
├── persons/             # Personhantering
│   ├── models.py        # Person-modellen
│   ├── views.py         # CRUD-vyer för personer
│   ├── forms.py         # PersonForm
│   ├── urls.py          # Persons URLs
│   └── admin.py         # Person admin
│
├── documents/           # Dokumenthantering
│   ├── models.py        # DocumentType och Document modeller
│   ├── views.py         # CRUD-vyer för dokument och dokumenttyper
│   ├── forms.py         # DocumentTypeForm och DocumentForm
│   ├── urls.py          # Documents URLs
│   └── admin.py         # Document och DocumentType admin
│
├── templates/           # HTML-mallar
│   ├── base.html        # Basmall med Bootstrap 5
│   ├── accounts/        # Login, register mallar
│   ├── core/            # Dashboard mall
│   ├── persons/         # Person-mallar (list, detail, form, delete)
│   └── documents/       # Dokument-mallar
│
├── static/              # Statiska filer (tom, använder CDN för Bootstrap)
├── media/               # Uppladdade filer
└── manage.py            # Django management script
```

## Databas-relationer

```
User (Django inbyggd)
  ↓ 1:N
Person
  ↓ 1:N         ← Template (1:N)
Document
  ↓ N:1
DocumentType
```

- En användare har många personer
- En person har många dokument
- Ett dokument tillhör en person och en dokumenttyp
- En person kan ha en mall

## API-endpoints (URLs)

```
/ eller ""                           → Dashboard (requires login)
/accounts/login/                     → Login
/accounts/register/                  → Register
/accounts/logout/                    → Logout

/persons/                            → Lista personer
/persons/create/                     → Skapa person
/persons/<id>/                       → Visa person
/persons/<id>/edit/                  → Redigera person
/persons/<id>/delete/                → Ta bort person

/documents/types/                    → Lista dokumenttyper
/documents/types/create/             → Skapa dokumenttyp
/documents/types/<id>/edit/          → Redigera dokumenttyp
/documents/types/<id>/delete/        → Ta bort dokumenttyp

/documents/create/                   → Skapa dokument
/documents/<id>/edit/                → Redigera dokument
/documents/<id>/delete/              → Ta bort dokument

/admin/                              → Django Admin
```

## Sammanfattning

Detta är en fullt fungerande MVP för släktforskningshantering med:
- ✅ Alla högprioriterade MVP-funktioner implementerade
- ✅ Säker användarhantering
- ✅ Komplett CRUD för personer och dokument
- ✅ Dokumenttypshantering
- ✅ Mallar för katalogstrukturer
- ✅ Dashboard med statistik
- ✅ Sökning och filtrering
- ✅ Bootstrap 5 styling
- ✅ Responsiv design
- ✅ Svenskt gränssnitt

Systemet är redo att användas och kan enkelt utökas med fler funktioner i framtiden!

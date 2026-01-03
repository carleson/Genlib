# Genlib - Genealogy Library Management System

[🇸🇪 Svenska](#svenska) | [🇬🇧 English](#english)

---

## <a name="svenska"></a>🇸🇪 Svenska

### Översikt

**Genlib** är ett webbaserat dokumenthanteringssystem för hantering av släktforsknings dokument. Systemet hjälper dig att organisera personer, dokument och källmaterial på ett strukturerat sätt. 
Använd Genlib för att organisera dina dokument (ex personbevis, folkräkning, kyrkböcker m.m) lokalt på din dator eller i molnet.
Dokumenten lagras som filer i filsystemet och går enkelt att komma åt eller uppdateras.
Genlib är ett komplement till släktforskningsprogram.


### Huvudfunktioner

- **👥 Personhantering** - Skapa, redigera och hantera personer med detaljerad information
- **📄 Dokumenthantering** - Ladda upp och organisera dokument kopplade till personer
- **🗂️ Katalogstrukturer** - Använd fördefinierade mallar eller skapa egna för att organisera filer
- **🏷️ Dokumenttyper** - Konfigurera olika dokumenttyper (personbevis, folkräkning, kyrkböcker, etc.)
- **📊 Dashboard** - Översikt med statistik och senaste aktivitet
- **🔍 Sökning** - Sök och filtrera personer och dokument
- **🔐 Säker autentisering** - Varje användare ser endast sina egna data
- **📱 Responsiv design** - Fungerar på desktop, tablet och mobil

### Teknologi

- **Backend:** Django 6.0
- **Databas:** SQLite3 (lätt att byta till PostgreSQL)
- **Frontend:** Django Templates + Bootstrap 5
- **Python:** 3.12+
- **Pakethanterare:** uv

### Snabbstart

#### Förutsättningar

- Python 3.12 eller senare
- uv (pakethanterare)

#### Installation

```bash
# Klona repot
git clone https://github.com/ditt-användarnamn/genlib.git
cd genlib

# Installera beroenden
uv sync

# Kör migrationer
uv run python manage.py migrate

# Skapa fördefinierade mallar och dokumenttyper
uv run python manage.py setup_initial_data

# Skapa en superuser
uv run python manage.py createsuperuser

# Starta utvecklingsservern
uv run python manage.py runserver
```

Öppna din webbläsare och gå till: **http://localhost:8000**

### Dokumentation

- [Installation](INSTALLATION.md) - Detaljerad installationsguide
- [Översikt](GENLIB_OVERVIEW.md) - Fullständig funktionsöversikt
- [Bidra](CONTRIBUTING.md) - Guide för att bidra till projektet

### Projektstruktur

```
genlib/
├── accounts/         # Användarautentisering
├── persons/          # Personhantering
├── documents/        # Dokument och dokumenttyper
├── core/             # Gemensam funktionalitet (mallar, dashboard)
├── config/           # Django-konfiguration
├── templates/        # HTML-mallar
├── static/           # Statiska filer
└── media/            # Uppladdade filer (genereras automatiskt)
```

### Licens

Detta projekt är licensierat under MIT-licensen - se [LICENSE](LICENSE) för detaljer.

---

## <a name="english"></a>🇬🇧 English

### Overview

**Genlib** is a web-based genealogy research management system. It helps you organize persons, documents, and source materials in a structured way. Built with Django and Bootstrap for a modern and user-friendly experience.

### Key Features

- **👥 Person Management** - Create, edit and manage persons with detailed information
- **📄 Document Management** - Upload and organize documents linked to persons
- **🗂️ Directory Templates** - Use predefined templates or create your own for file organization
- **🏷️ Document Types** - Configure different document types (certificates, census records, church books, etc.)
- **📊 Dashboard** - Overview with statistics and recent activity
- **🔍 Search** - Search and filter persons and documents
- **🔐 Secure Authentication** - Each user sees only their own data
- **📱 Responsive Design** - Works on desktop, tablet and mobile

### Technology Stack

- **Backend:** Django 6.0
- **Database:** SQLite3 (easy to switch to PostgreSQL)
- **Frontend:** Django Templates + Bootstrap 5
- **Python:** 3.12+
- **Package Manager:** uv

### Quick Start

#### Prerequisites

- Python 3.12 or later
- uv (package manager)

#### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/genlib.git
cd genlib

# Install dependencies
uv sync

# Run migrations
uv run python manage.py migrate

# Create predefined templates and document types
uv run python manage.py setup_initial_data

# Create a superuser
uv run python manage.py createsuperuser

# Start development server
uv run python manage.py runserver
```

Open your browser and go to: **http://localhost:8000**

### Documentation

- [Installation](INSTALLATION.md) - Detailed installation guide
- [Overview](GENLIB_OVERVIEW.md) - Complete feature overview
- [Contributing](CONTRIBUTING.md) - Guide for contributing to the project

### Project Structure

```
genlib/
├── accounts/         # User authentication
├── persons/          # Person management
├── documents/        # Documents and document types
├── core/             # Shared functionality (templates, dashboard)
├── config/           # Django configuration
├── templates/        # HTML templates
├── static/           # Static files
└── media/            # Uploaded files (generated automatically)
```

### Features

#### MVP Features (Implemented)

- User registration and authentication
- Create/view/edit/delete persons
- Person details (name, birth/death dates, notes)
- Configurable document types
- Upload documents to persons
- Source information for documents
- Search functionality
- Dashboard with statistics

#### Predefined Templates

- **default**: documents/, images/, notes/, media/, sources/
- **extended**: Extended structure with subcategories for birth, marriage, death, census, etc.
- **minimal**: documents/, notes/

#### Predefined Document Types

- Personal certificates, birth certificates, marriage certificates, death certificates
- Census records, church books
- Portraits, notes

### Security

- CSRF protection (Django built-in)
- XSS protection (Django built-in)
- SQL Injection protection (Django ORM)
- Secure file upload with validation
- User authentication required for all operations
- Users only see their own data

### Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

### License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

### Support

For questions or issues, please open an issue on GitHub.

---

**Made with ❤️ for genealogy researchers**

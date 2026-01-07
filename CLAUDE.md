# CLAUDE.md

## Projektöversikt

**Genlib** är ett Django-baserat dokumenthanteringssystem för släktforskning. Systemet lagrar dokumentmetadata i databas medan filer lagras i filsystemet enligt konfigurerbar struktur.

### Snabbreferens för kodförståelse

- **Komplett teknisk dokumentation:** [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)
- **Funktionsöversikt:** [GENLIB_OVERVIEW.md](GENLIB_OVERVIEW.md)
- **README:** [README.md](README.md)

### Viktiga koncept att känna till

1. **Dynamisk Media Root:** Använd alltid `get_media_root()` från `core.utils` istället för `settings.MEDIA_ROOT`
2. **Filsystembaserad lagring:** Filer lagras i filsystemet, databas innehåller endast metadata
3. **Dokumentsynkronisering:** `PersonDocumentSyncView` synkroniserar filsystem med databas
4. **Mallbaserad struktur:** Katalogstrukturer definieras via `Template`-modellen
5. **Kanonisk relations-ordning:** PersonRelationship enforcar `person_a.id < person_b.id`

## Teknikstack
- **Språk:** Python 3.12+
- **Pakethantering:** uv
- **OS:** Linux
- **Versionshantering:** Git
- **Testramverk:** pytest

## Utvecklingsmiljö

### Sätta upp miljön
```bash
uv sync
```

### Aktivera virtuell miljö
```bash
source .venv/bin/activate
```

## Kodkonventioner

### Stil
- Följ PEP 8
- Använd type hints genomgående
- Docstrings i Google-format
- Radlängd: max 88 tecken (Black-standard)

### Namngivning
- Funktioner och variabler: `snake_case`
- Klasser: `PascalCase`
- Konstanter: `SCREAMING_SNAKE_CASE`

## Testning

### Köra tester
```bash
uv run pytest
```

### Köra med coverage
```bash
uv run pytest --cov=src --cov-report=term-missing
```

### Teststruktur
- Tester placeras i `tests/`
- Testfiler namnges `test_<modul>.py`
- Testfunktioner namnges `test_<vad_testas>`
- Använd fixtures för återanvändbar setup

## Git-workflow

### Commit-meddelanden
Använd konventionella commits:
- `feat:` ny funktionalitet
- `fix:` buggfix
- `docs:` dokumentation
- `test:` tester
- `refactor:` refaktorering utan funktionsändring

### Brancher
- `main` - stabil kod
- `feature/<namn>` - nya funktioner
- `fix/<namn>` - buggfixar

## Projektstruktur
```
.
├── src/
│   └── <paketnamn>/
│       ├── __init__.py
│       └── ...
├── tests/
│   ├── conftest.py
│   └── test_*.py
├── pyproject.toml
├── README.md
└── CLAUDE.md
```

## Vanliga kommandon
| Kommando | Beskrivning |
|----------|-------------|
| `uv sync` | Installera dependencies |
| `uv add <paket>` | Lägg till paket |
| `uv run pytest` | Kör tester |
| `uv run ruff check .` | Linta kod |
| `uv run ruff format .` | Formatera kod |

## Snabbstart för kodförståelse

### Viktigaste filer att läsa först

1. **Modeller (databasstruktur):**
   - `persons/models.py` - Person, PersonRelationship, ChecklistTemplate, PersonChecklistItem
   - `documents/models.py` - DocumentType, Document
   - `core/models.py` - SystemConfig, Template, SetupStatus

2. **Vyer (huvudfunktionalitet):**
   - `persons/views.py` - PersonDetailView, PersonDocumentSyncView
   - `documents/views.py` - DocumentCreateView, DocumentViewUpdateView
   - `core/views.py` - dashboard, initial_setup, backup/restore

3. **URL-routing:**
   - `config/urls.py` - Root URL-konfiguration
   - `persons/urls.py` - Person-relaterade URLs
   - `documents/urls.py` - Dokument-relaterade URLs

4. **Templates:**
   - `templates/persons/person_detail.html` - Huvudvy för person
   - `templates/base.html` - Bas-template med navigation

5. **Utilities:**
   - `core/utils.py` - `get_media_root()`, `get_backup_root()`

### Arkitektur snabbt

```
User → Person → Document → DocumentType
              ↓
        PersonChecklistItem → ChecklistTemplateItem
        PersonRelationship
```

**Filsökväg:**
```
{media_root}/persons/{person.directory_name}/{doc_type.target_directory}/{filename}
```

## Anteckningar för Claude
- Föreslå alltid tester vid ny funktionalitet
- Använd `pathlib.Path` istället för `os.path`
- Föredra f-strings framför `.format()`
- Hantera fel explicit med specifika exceptions
- Använd alltid `get_media_root()` från `core.utils` för media-sökvägar
- Filtrera alltid queries på `user=request.user` för säkerhet

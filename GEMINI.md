# GEMINI.md

## Projektöversikt
[Beskriv kort vad projektet gör och dess syfte]

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

## Anteckningar för Gemini
- Föreslå alltid tester vid ny funktionalitet
- Använd `pathlib.Path` istället för `os.path`
- Föredra f-strings framför `.format()`
- Hantera fel explicit med specifika exceptions

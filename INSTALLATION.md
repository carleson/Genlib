# Genlib - Installationsguide

## Snabbstart

### 1. Installera beroenden

Projektet använder `uv` som pakethanterare. Om du inte har uv installerat:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Kör migrationer och setup

```bash
# Skapa databastabeller
uv run python manage.py migrate

# Skapa fördefinierade mallar och dokumenttyper
uv run python manage.py setup_initial_data
```

### 3. Skapa en superuser

```bash
uv run python manage.py createsuperuser
```

Följ instruktionerna för att skapa ett admin-konto.

### 4. Starta utvecklingsservern

```bash
# Alternativ 1: Använd skriptet
./run_server.sh

# Alternativ 2: Direkt
uv run python manage.py runserver
```

Öppna din webbläsare och gå till: **http://localhost:8000**

## Första inloggningen

1. Gå till http://localhost:8000
2. Klicka på "Registrera" för att skapa ett användarkonto
3. Eller använd superuser-kontot du skapade

## Django Admin

Django Admin finns på: **http://localhost:8000/admin/**

Här kan du:
- Hantera användare
- Se alla personer och dokument
- Redigera mallar och dokumenttyper

## Mappstruktur

```
genlib/
├── accounts/         # Användarautentisering
├── persons/          # Personhantering
├── documents/        # Dokument och dokumenttyper
├── core/             # Gemensam funktionalitet (mallar, dashboard)
├── config/           # Django-konfiguration
├── templates/        # HTML-mallar
├── static/           # Statiska filer (CSS, JS)
├── media/            # Uppladdade filer
└── manage.py         # Django management script
```

## Funktioner

### MVP-funktioner (implementerade):
- Användarregistrering och inloggning
- Skapa/visa/redigera/ta bort personer
- Grundläggande personuppgifter
- Konfigurera dokumenttyper
- Ladda upp dokument till person
- Visa dokument för person
- Källinformation för dokument
- Grundläggande sökning i personer
- Dashboard med statistik

### Fördefinierade mallar:
- **default**: dokument/, bilder/, anteckningar/, media/, källor/
- **extended**: Utökad struktur med underkategorier
- **minimal**: dokument/, anteckningar/

### Fördefinierade dokumenttyper:
- personbevis, födelseattest, vigselbevis, dödsbevis
- folkräkning, kyrkbok
- porträtt, anteckning

## Utveckling

### Skapa nya migrationer

```bash
uv run python manage.py makemigrations
uv run python manage.py migrate
```

### Återställ databasen

```bash
rm db.sqlite3
uv run python manage.py migrate
uv run python manage.py setup_initial_data
uv run python manage.py createsuperuser
```

### Kör Python-shell

```bash
uv run python manage.py shell
```

## Teknologi

- **Backend**: Django 6.0
- **Databas**: SQLite3
- **Frontend**: Django Templates + Bootstrap 5
- **Python**: 3.12+
- **Pakethanterare**: uv

## Support

För frågor eller problem, se README.md eller kontakta utvecklaren.

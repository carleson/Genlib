# Genlib - Installationsguide

## Snabbstart (Automatisk setup)

### 1. Installera beroenden

Projektet använder `uv` som pakethanterare. Om du inte har uv installerat:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Starta servern (första gången)

```bash
./run_server.sh
```

Det är allt! Scriptet kommer automatiskt att:
- Installera beroenden
- Köra databasmigrationer
- Starta utvecklingsservern

### 3. Web-baserad initial setup

När du kör servern första gången kommer du automatiskt att omdirigeras till setup-sidan:

**http://localhost:8000/setup/**

På setup-sidan har du **två alternativ**:

#### Alternativ 1: Nytt projekt
- ✅ Skapa ditt administratörskonto (superuser)
- ✅ Konfigurera var media-filer ska lagras
  - Kan vara absolut sökväg (t.ex. `/home/user/genlib-media`)
  - Eller relativ sökväg (t.ex. `media`)
- Efter setup loggas du automatiskt in och redirectas till dashboard

#### Alternativ 2: Återställ från backup
- ✅ Ladda upp en tidigare skapad backup-fil (ZIP)
- ✅ Alla användare, personer, dokument och inställningar återställs
- ✅ Du kan sedan logga in med ditt befintliga konto
- Perfekt för att flytta installation till ny server eller återställa efter problem

### 4. Framtida körningar

När setup är klar, kör bara:

```bash
./run_server.sh
```

Du kommer direkt till inloggningssidan.

## Alternativ: Manuell setup (avancerat)

Om du föredrar att köra setup manuellt:

```bash
# Kör migrationer
uv run python manage.py migrate

# Skapa fördefinierade mallar och dokumenttyper (valfritt)
uv run python manage.py setup_initial_data

# Skapa superuser
uv run python manage.py createsuperuser

# Starta servern
uv run python manage.py runserver
```

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

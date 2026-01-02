# Docker Compose Instruktioner för Genlib

Detta dokument beskriver hur du kör Genlib med Docker Compose.

## Förutsättningar

- Docker Desktop installerat och igång
- Docker Compose (ingår i Docker Desktop)

## Snabbstart

### 1. Bygg och starta applikationen

```bash
docker-compose up --build
```

Detta kommer att:
- Bygga Docker-imagen för applikationen
- Köra migrationer (SQLite-databas skapas automatiskt)
- Samla statiska filer
- Skapa en admin-användare (om den inte finns)
- Starta utvecklingsservern på http://localhost:8000

### 2. Öppna applikationen

Öppna din webbläsare och gå till: http://localhost:8000

### 3. Logga in som admin

- **Användarnamn:** admin
- **Lösenord:** admin

## Vanliga kommandon

### Starta applikationen

```bash
docker-compose up
```

### Starta i bakgrunden

```bash
docker-compose up -d
```

### Stoppa applikationen

```bash
docker-compose down
```

### Stoppa och ta bort alla volymer (rensar databas)

```bash
docker-compose down -v
```

### Visa loggar

```bash
docker-compose logs -f
```

### Kör Django-kommandon

```bash
# Skapa migrations
docker-compose exec web python manage.py makemigrations

# Kör migrations
docker-compose exec web python manage.py migrate

# Skapa superuser
docker-compose exec web python manage.py createsuperuser

# Öppna Django shell
docker-compose exec web python manage.py shell
```

### Bygga om imagen

```bash
docker-compose build --no-cache
```

### Starta om en specifik tjänst

```bash
docker-compose restart web
```

## Felsökning

### Rensa allt och börja om

Om du vill börja med en helt tom databas:

```bash
docker-compose down -v
docker-compose up --build
```

Detta tar bort alla volymer inklusive SQLite-databasen.

### Se applikationsloggar

```bash
docker-compose logs -f web
```

## Produktionsinställningar

För produktion bör du:

1. Ändra `SECRET_KEY` till något säkert och unikt
2. Sätt `DEBUG=0`
3. Konfigurera `ALLOWED_HOSTS` korrekt
4. Överväg att byta till PostgreSQL eller MySQL för bättre prestanda
5. Använd en produktionsklar webbserver (Gunicorn + Nginx)
6. Sätt upp SSL/TLS certifikat

## Datavolymer

Docker Compose skapar följande volymer:

- `sqlite_data` - SQLite-databasfil (db.sqlite3)
- `static_volume` - Statiska filer
- `media_volume` - Uppladdade mediafiler

Dessa volymer bevaras även när containrarna stoppas.

## Lokal utveckling vs Docker

Du kan köra applikationen både lokalt och i Docker:

**Lokalt (utan Docker):**
```bash
uv run python manage.py runserver
```
Använder SQLite-databasen i projektmappen.

**Med Docker:**
```bash
docker-compose up
```
Använder SQLite-databasen i en Docker-volym (separerad från lokal databas).

## Miljövariabler

Du kan skapa en `.env` fil baserad på `.env.example` för att anpassa inställningar:

```bash
cp .env.example .env
```

Redigera sedan `.env` med dina inställningar.

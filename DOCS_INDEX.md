# Genlib - Dokumentationsindex

Snabbreferens till all projektdokumentation.

## 📚 För utvecklare

### 🚀 Kom igång snabbt
1. **[README.md](README.md)** - Projektöversikt och snabbstart
2. **[INSTALLATION.md](INSTALLATION.md)** - Detaljerad installationsguide
3. **[CLAUDE.md](CLAUDE.md)** - Utvecklingsmiljö och kodkonventioner

### 🔧 Teknisk dokumentation
4. **[TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)** ⭐ **VIKTIGAST**
   - Komplett teknisk referens
   - Arkitektur och design
   - Alla modeller, vyer, URL-er
   - Arbetsflöden och koncept
   - Kodexempel och snabbreferens

5. **[DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)** ⭐ **FÖR DATABASFÖRSTÅELSE**
   - ER-diagram
   - Modeller och relationer
   - Query-exempel
   - Indexstrategi
   - Prestandaoptimering

### 📖 Funktionsdokumentation
6. **[GENLIB_OVERVIEW.md](GENLIB_OVERVIEW.md)** - Fullständig funktionsöversikt

### 🤝 Bidra till projektet
7. **[CONTRIBUTING.md](CONTRIBUTING.md)** - Guide för bidrag
8. **[SECURITY.md](SECURITY.md)** - Säkerhetspolicy

### 📦 Deployment
9. **[DOCKER.md](DOCKER.md)** - Docker-setup
10. **[GITHUB_SETUP.md](GITHUB_SETUP.md)** - GitHub-konfiguration
11. **[GITHUB_QUICKSTART.md](GITHUB_QUICKSTART.md)** - Snabbguide för GitHub

### 📝 Versionshantering
12. **[CHANGELOG.md](CHANGELOG.md)** - Versionshistorik

---

## 🎯 Använd rätt dokument för din situation

### "Jag ska börja utveckla och behöver förstå koden snabbt"
1. Läs [CLAUDE.md](CLAUDE.md) - Sektion "Snabbstart för kodförståelse"
2. Läs [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) - Sektion "Arkitektur"
3. Läs [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - ER-diagram och queries

### "Jag ska lägga till en ny funktion"
1. Läs [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) - Sektion för relevant app
2. Läs [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Se vilka modeller som påverkas
3. Följ [CLAUDE.md](CLAUDE.md) - Kodkonventioner

### "Jag behöver förstå hur en befintlig funktion fungerar"
1. Läs [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) - Sektion "Arbetsflöden"
2. Läs relevant vy-dokumentation i samma fil
3. Kolla kod-exempel i "Snabbreferens"

### "Jag behöver förstå databasstrukturen"
1. Läs [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - ER-diagram
2. Se query-exempel för din use-case
3. Läs [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) - Modell-sektion för detaljer

### "Jag ska installera projektet"
1. Läs [README.md](README.md) - Snabbstart
2. Läs [INSTALLATION.md](INSTALLATION.md) - Detaljerad guide
3. Kör `setup_initial_data` management command

### "Jag ska deploya projektet"
1. Läs [DOCKER.md](DOCKER.md) - Docker-setup
2. Läs [GITHUB_SETUP.md](GITHUB_SETUP.md) - GitHub Actions

### "Jag ska bidra med kod"
1. Läs [CONTRIBUTING.md](CONTRIBUTING.md) - Bidragsriktlinjer
2. Läs [CLAUDE.md](CLAUDE.md) - Kodkonventioner
3. Följ git-workflow i [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)

---

## 📊 Dokumentation per app

### Core
**Filer:**
- `core/models.py` - SystemConfig, Template, SetupStatus
- `core/views.py` - dashboard, initial_setup, backup/restore
- `core/utils.py` - get_media_root(), get_backup_root()

**Dokumentation:**
- [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md#2-core) - Funktionalitet
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Modeller

### Persons
**Filer:**
- `persons/models.py` - Person, PersonRelationship, Checklists
- `persons/views.py` - CRUD, relationer, export, sync
- `persons/urls.py` - URL-routing

**Dokumentation:**
- [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md#3-persons) - Funktionalitet
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Modeller och relationer

**Viktiga funktioner:**
- PersonDetailView - Huvudvy
- PersonDocumentSyncView - Filsystemsynkronisering ⭐
- PersonRelationshipCreateView - Skapa relationer

### Documents
**Filer:**
- `documents/models.py` - DocumentType, Document
- `documents/views.py` - CRUD för dokument och typer
- `documents/urls.py` - URL-routing

**Dokumentation:**
- [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md#4-documents) - Funktionalitet
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Modeller

**Viktiga funktioner:**
- DocumentCreateView - Skapa dokument (fil eller text)
- DocumentViewUpdateView - Visa/redigera dokument

### Accounts
**Filer:**
- `accounts/views.py` - signup
- Django's inbyggda auth-vyer

**Dokumentation:**
- [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md#1-accounts)

---

## 🔍 Sökindex

### Koncept
- **Dynamisk Media Root:** [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md#1-dynamisk-media-root)
- **Mallbaserad struktur:** [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md#2-mallbaserad-katalogstruktur)
- **Dokumentsynkronisering:** [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md#4-dokumentsynkronisering-ny-funktion)
- **Kanonisk relations-ordning:** [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md#5-kanonisk-relations-ordning)
- **Singleton-modeller:** [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md#6-singleton-modeller)

### Modeller
- **Person:** [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md#person)
- **PersonRelationship:** [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md#personrelationship)
- **Document:** [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md#document)
- **DocumentType:** [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md#documenttype)
- **SystemConfig:** [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md#systemconfig-singleton)

### Arbetsflöden
- **Skapa person:** [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md#1-skapa-ny-person)
- **Ladda upp dokument:** [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md#2-ladda-upp-dokument)
- **Synkronisera dokument:** [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md#3-synkronisera-dokument-från-filsystem-ny)
- **Skapa relation:** [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md#4-skapa-relation)
- **Backup & Restore:** [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md#6-backup--restore)

### Queries
- **Hämta dokument för person:** [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md#hämta-alla-dokument-för-en-person)
- **Hämta relationer:** [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md#hämta-alla-relationer-för-en-person)
- **Hämta checklistprogress:** [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md#hämta-checklistprogress-för-en-person)

---

## 🎓 Lärresurs-ordning

### För nybörjare på projektet
1. [README.md](README.md) - Översikt
2. [INSTALLATION.md](INSTALLATION.md) - Kom igång
3. [CLAUDE.md](CLAUDE.md) - Kodkonventioner
4. [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Förstå datastrukturen
5. [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) - Djupdyk

### För erfarna Django-utvecklare
1. [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) - Arkitektur
2. [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Schema
3. [CLAUDE.md](CLAUDE.md) - Projektspecifika konventioner
4. Läs kod i `persons/views.py` och `documents/views.py`

---

## 📅 Uppdateringsschema

### Denna fil ska uppdateras när:
- Ny dokumentation läggs till
- Dokumentation flyttas eller byter namn
- Ny viktig funktion läggs till

### Andra filer som ska hållas aktuella:
- **TECHNICAL_DOCUMENTATION.md** - Vid varje större feature eller arkitekturändring
- **DATABASE_SCHEMA.md** - Vid varje modell-ändring eller migration
- **CHANGELOG.md** - Vid varje release
- **CLAUDE.md** - Vid ändring av kodkonventioner eller utvecklingsmiljö

---

**Senast uppdaterad:** 2026-01-05

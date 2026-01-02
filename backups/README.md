# Genlib Backups

Denna katalog innehåller backup-filer för Genlib-systemet.

## Backup-filer

Backup-filer namnges automatiskt med tidsstämpel:
- `genlib_backup_YYYY-MM-DD_HH-MM-SS.zip`

## Vad ingår i en backup?

Varje backup innehåller:
- ✅ **Databas** (db.sqlite3) - Alla personer, dokument, användare
- ✅ **Media-filer** (media/) - Alla uppladdade bilder och dokument
- ✅ **Konfiguration** - settings.py, pyproject.toml, .env

## Skapa backup

```bash
# Med hjälpscript
./backup.sh

# Direkt med Django-kommando
uv run python manage.py backup
```

## Återställa backup

```bash
# Med hjälpscript
./restore.sh backups/genlib_backup_2025-12-11_14-30-00.zip

# Direkt med Django-kommando
uv run python manage.py restore backups/genlib_backup_2025-12-11_14-30-00.zip
```

## Säkerhetskopiering

När du återställer en backup skapas automatiskt en säkerhetskopia av nuvarande data i:
- `backups/safety/`

## Viktig information

⚠️ **Backup-filer innehåller känslig data!**
- Förvara backups säkert
- Ta inte med backups i version control (Git)
- Överväg att kryptera backups för långtidslagring

💡 **Regelbunden backup rekommenderas!**
- Skapa backup innan större ändringar
- Schemalägga automatisk backup (t.ex. dagligen)

"""
Django management command för att skapa backup av hela systemet.
Skapar en ZIP-fil med databas, media-filer och konfiguration.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from datetime import datetime
import zipfile
import os
from pathlib import Path
import time


class Command(BaseCommand):
    help = 'Skapar en komplett backup av systemet (databas, media, konfiguration)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='backups',
            help='Katalog där backup-filen ska sparas (default: backups/)'
        )

    def handle(self, *args, **options):
        # Skapa backup-katalog om den inte finns
        backup_dir = Path(options['output_dir'])
        backup_dir.mkdir(exist_ok=True)

        # Skapa filnamn med tidsstämpel
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_filename = f'genlib_backup_{timestamp}.zip'
        backup_path = backup_dir / backup_filename

        self.stdout.write(self.style.SUCCESS(f'\n=== Skapar backup: {backup_filename} ===\n'))

        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 1. Backup av databas
                self.stdout.write('📦 Packar databas...')
                db_path = settings.BASE_DIR / 'db.sqlite3'
                if db_path.exists():
                    zipf.write(db_path, 'db.sqlite3')
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Databas: {db_path.stat().st_size} bytes'))
                else:
                    self.stdout.write(self.style.WARNING('  ⚠ Ingen databas hittades'))

                # 2. Backup av media-filer och katalogstruktur (från extern katalog)
                self.stdout.write('\n📦 Packar media-filer och katalogstruktur...')

                # Hämta media root från systemkonfiguration
                from core.utils import get_media_root
                media_root = Path(get_media_root())

                self.stdout.write(f'  📂 Media root: {media_root}')

                if media_root.exists():
                    media_count = 0
                    dir_count = 0

                    for root, dirs, files in os.walk(media_root):
                        # Spara katalogstrukturen (även tomma mappar)
                        for dir_name in dirs:
                            dir_path = Path(root) / dir_name
                            # Spara med relativ sökväg från media_root
                            arcname = 'media/' + str(dir_path.relative_to(media_root)) + '/'

                            # Skapa en ZipInfo för katalogen
                            zip_info = zipfile.ZipInfo(arcname)
                            zip_info.external_attr = 0o40775 << 16  # Unix directory permissions
                            zipf.writestr(zip_info, '')
                            dir_count += 1

                        # Spara alla filer
                        for file in files:
                            file_path = Path(root) / file
                            # Spara med relativ sökväg från media_root, prefixad med 'media/'
                            arcname = 'media/' + str(file_path.relative_to(media_root))
                            zipf.write(file_path, arcname)
                            media_count += 1

                    self.stdout.write(self.style.SUCCESS(f'  ✓ Media-filer: {media_count} filer, {dir_count} kataloger'))
                else:
                    self.stdout.write(self.style.WARNING(f'  ⚠ Media-katalog finns inte: {media_root}'))

                # 3. Backup av konfigurationsfiler
                self.stdout.write('\n📦 Packar konfiguration...')
                config_files = [
                    'config/settings.py',
                    'pyproject.toml',
                    '.env',
                ]
                config_count = 0
                for config_file in config_files:
                    config_path = settings.BASE_DIR / config_file
                    if config_path.exists():
                        zipf.write(config_path, config_file)
                        config_count += 1

                self.stdout.write(self.style.SUCCESS(f'  ✓ Konfigurationsfiler: {config_count} filer'))

                # 4. Skapa manifest-fil med metadata
                manifest_content = f"""GENLIB BACKUP
==============
Skapad: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Django version: {settings.DJANGO_VERSION if hasattr(settings, 'DJANGO_VERSION') else 'Unknown'}
Python version: {os.sys.version}
Database: SQLite3
"""
                zipf.writestr('BACKUP_INFO.txt', manifest_content)

            # Visa sammanfattning
            backup_size = backup_path.stat().st_size
            backup_size_mb = backup_size / (1024 * 1024)

            self.stdout.write(self.style.SUCCESS(f'\n✅ Backup skapad framgångsrikt!'))
            self.stdout.write(f'\n📁 Fil: {backup_path}')
            self.stdout.write(f'💾 Storlek: {backup_size_mb:.2f} MB ({backup_size:,} bytes)')
            self.stdout.write(f'\n💡 För att återställa, kör:')
            self.stdout.write(f'   python manage.py restore {backup_path}\n')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Fel vid backup: {str(e)}'))
            raise

"""
Django management command för att återställa backup av hela systemet.
Återställer databas, media-filer och konfiguration från en ZIP-fil.

Återställningslägen:
- Standard: Återställer allt (databas + media + konfiguration)
- --db-only: Återställer endast databas
- --exclude-media: Återställer databas och konfiguration, men exkluderar media-filer
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from datetime import datetime
import zipfile
import os
import shutil
from pathlib import Path


class Command(BaseCommand):
    help = 'Återställer en backup av systemet (databas, media, konfiguration)'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_file',
            type=str,
            help='Sökväg till backup-filen som ska återställas'
        )
        parser.add_argument(
            '--no-confirm',
            action='store_true',
            help='Hoppa över bekräftelse (varning: skriver över befintlig data!)'
        )
        parser.add_argument(
            '--db-only',
            action='store_true',
            help='Återställ endast databas (exkluderar media och konfiguration)'
        )
        parser.add_argument(
            '--exclude-media',
            action='store_true',
            help='Återställ databas och konfiguration, men exkludera media-filer'
        )

    def handle(self, *args, **options):
        backup_file = Path(options['backup_file'])

        # Kontrollera att backup-filen finns
        if not backup_file.exists():
            self.stdout.write(self.style.ERROR(f'\n❌ Backup-filen finns inte: {backup_file}\n'))
            return

        self.stdout.write(self.style.WARNING(f'\n=== Återställer backup: {backup_file.name} ===\n'))

        # Visa information om backup
        try:
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                file_list = zipf.namelist()
                self.stdout.write('📋 Innehåll i backup:\n')

                # Visa manifest om det finns
                if 'BACKUP_INFO.txt' in file_list:
                    manifest = zipf.read('BACKUP_INFO.txt').decode('utf-8')
                    self.stdout.write(manifest)
                    self.stdout.write('\n')

                self.stdout.write(f'📦 Totalt antal filer: {len(file_list)}\n')

        except zipfile.BadZipFile:
            self.stdout.write(self.style.ERROR('\n❌ Ogiltig ZIP-fil\n'))
            return

        # Visa vad som kommer att återställas
        db_only = options['db_only']
        exclude_media = options['exclude_media']

        if db_only:
            self.stdout.write(self.style.WARNING('\n📋 Återställningsläge: ENDAST DATABAS\n'))
        elif exclude_media:
            self.stdout.write(self.style.WARNING('\n📋 Återställningsläge: DATABAS + KONFIGURATION (utan media)\n'))
        else:
            self.stdout.write(self.style.WARNING('\n📋 Återställningsläge: FULL ÅTERSTÄLLNING (databas + media + konfiguration)\n'))

        # Bekräftelse
        if not options['no_confirm']:
            self.stdout.write(self.style.WARNING('\n⚠️  VARNING: Detta kommer att skriva över befintlig data!\n'))
            response = input('Är du säker på att du vill fortsätta? (skriv "ja" för att bekräfta): ')
            if response.lower() != 'ja':
                self.stdout.write(self.style.WARNING('\n❌ Återställning avbruten\n'))
                return

        # Skapa backup av nuvarande data innan återställning
        self.stdout.write('\n💾 Skapar säkerhetskopia av nuvarande data...')
        safety_backup_dir = settings.BASE_DIR / 'backups' / 'safety'
        safety_backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        # Backup nuvarande databas
        current_db = settings.BASE_DIR / 'db.sqlite3'
        if current_db.exists():
            safety_db = safety_backup_dir / f'db.sqlite3.before_restore_{timestamp}'
            shutil.copy2(current_db, safety_db)
            self.stdout.write(self.style.SUCCESS(f'  ✓ Säkerhetskopierat databas till: {safety_db.name}'))

        # Återställ från backup
        self.stdout.write('\n🔄 Återställer data...\n')

        # Hämta media root från systemkonfiguration
        from core.utils import get_media_root
        media_root = Path(get_media_root())
        self.stdout.write(f'  📂 Media root: {media_root}\n')

        try:
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                restored_count = 0
                skipped_count = 0

                for file_info in zipf.filelist:
                    filename = file_info.filename

                    # Hoppa över manifest
                    if filename == 'BACKUP_INFO.txt':
                        continue

                    # Kontrollera om det är en katalog (slutar med /)
                    is_directory = filename.endswith('/')

                    # Filtrera baserat på återställningsläge
                    should_restore = True

                    if db_only:
                        # Endast databas
                        if filename != 'db.sqlite3':
                            should_restore = False
                    elif exclude_media:
                        # Exkludera media-filer
                        if filename.startswith('media/'):
                            should_restore = False

                    if not should_restore:
                        skipped_count += 1
                        continue

                    # Bestäm destination
                    if filename.startswith('media/'):
                        # Media-filer går till den konfigurerade media_root
                        relative_path = filename[6:]  # Ta bort 'media/' prefix
                        dest_path = media_root / relative_path
                    else:
                        # Andra filer (databas, konfiguration) går till BASE_DIR
                        dest_path = settings.BASE_DIR / filename

                    if is_directory:
                        # Skapa katalog
                        dest_path.mkdir(parents=True, exist_ok=True)
                    else:
                        # Skapa katalog för filen om den inte finns
                        dest_path.parent.mkdir(parents=True, exist_ok=True)

                        # Extrahera filen
                        with zipf.open(filename) as source, open(dest_path, 'wb') as target:
                            shutil.copyfileobj(source, target)

                    restored_count += 1

                    # Visa framsteg
                    if restored_count % 10 == 0:
                        self.stdout.write(f'  📦 Återställt {restored_count} filer...', ending='\r')

                self.stdout.write(f'\n  ✓ Återställt {restored_count} filer/kataloger totalt')
                if skipped_count > 0:
                    self.stdout.write(f'  ⊘ Hoppade över {skipped_count} filer/kataloger')

            # Visa sammanfattning
            self.stdout.write(self.style.SUCCESS(f'\n✅ Backup återställd framgångsrikt!\n'))
            self.stdout.write(f'📁 Från: {backup_file}')
            self.stdout.write(f'📊 Återställda filer: {restored_count}')
            self.stdout.write(f'\n💡 Säkerhetskopia av gamla data finns i:')
            self.stdout.write(f'   {safety_backup_dir}\n')
            self.stdout.write(self.style.WARNING('\n⚠️  Starta om servern för att ladda nya data!\n'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Fel vid återställning: {str(e)}'))
            self.stdout.write(self.style.WARNING(f'\n💡 Säkerhetskopia finns i: {safety_backup_dir}\n'))
            raise

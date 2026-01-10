"""Management command för att fixa file.name för bilder"""
from django.core.management.base import BaseCommand
from documents.models import Document


class Command(BaseCommand):
    help = 'Fixar file.name för alla bilder så att URL:er blir korrekta'

    def handle(self, *args, **options):
        # Hitta alla bilder
        images = Document.objects.filter(
            file_type__in=['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
        )

        total = images.count()
        self.stdout.write(f'Hittade {total} bilder att kontrollera...')

        fixed_count = 0
        for img in images:
            # Konstruera korrekt file.name
            correct_name = f"persons/{img.person.directory_name}/{img.relative_path}"

            # Kontrollera om file.name behöver fixas
            if img.file.name != correct_name:
                old_name = img.file.name
                img.file.name = correct_name
                img.save(update_fields=['file'])

                self.stdout.write(
                    self.style.SUCCESS(
                        f'  Fixade: {img.person.get_full_name()} - {img.filename}'
                    )
                )
                self.stdout.write(f'    Från: {old_name}')
                self.stdout.write(f'    Till: {correct_name}')
                fixed_count += 1

        if fixed_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nKlart! Fixade {fixed_count} av {total} bilder.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nKlart! Alla {total} bilder hade redan korrekta sökvägar.'
                )
            )

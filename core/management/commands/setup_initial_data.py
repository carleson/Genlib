from django.core.management.base import BaseCommand
from core.models import Template
from documents.models import DocumentType


class Command(BaseCommand):
    help = 'Skapar fördefinierade mallar och dokumenttyper'

    def handle(self, *args, **options):
        self.stdout.write('Skapar fördefinierade mallar...')

        # Skapa mallar
        templates_data = [
            {
                'name': 'default',
                'description': 'Standardmall med grundläggande kataloger',
                'directories': 'dokument/\nbilder/\nanteckningar/\nmedia/\nkällor/'
            },
            {
                'name': 'extended',
                'description': 'Utökad mall med detaljerade underkategorier',
                'directories': '''dokument/födelse/
dokument/vigsel/
dokument/död/
dokument/folkräkning/
dokument/kyrkböcker/
bilder/porträtt/
bilder/platser/
anteckningar/
media/ljud/
media/video/
källor/
forskning/'''
            },
            {
                'name': 'minimal',
                'description': 'Minimal mall med enklaste struktur',
                'directories': 'dokument/\nanteckningar/'
            }
        ]

        for template_data in templates_data:
            template, created = Template.objects.get_or_create(
                name=template_data['name'],
                defaults={
                    'description': template_data['description'],
                    'directories': template_data['directories']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Skapade mall: {template.name}'))
            else:
                self.stdout.write(f'  Mallen {template.name} finns redan')

        self.stdout.write('\nSkapar fördefinierade dokumenttyper...')

        # Skapa dokumenttyper
        document_types_data = [
            {
                'name': 'personbevis',
                'target_directory': 'dokument',
                'filename': 'personbevis.pdf',
                'description': 'Personbevis från Skatteverket'
            },
            {
                'name': 'födelseattest',
                'target_directory': 'dokument/födelse',
                'filename': 'födelseattest.pdf',
                'description': 'Födelseattest från kyrkan'
            },
            {
                'name': 'vigselbevis',
                'target_directory': 'dokument/vigsel',
                'filename': 'vigselbevis.pdf',
                'description': 'Vigselbevis'
            },
            {
                'name': 'dödsbevis',
                'target_directory': 'dokument/död',
                'filename': 'dödsbevis.pdf',
                'description': 'Dödsbevis'
            },
            {
                'name': 'folkräkning',
                'target_directory': 'dokument/folkräkning',
                'filename': 'folkräkning.txt',
                'description': 'Folkräkningsuppgifter'
            },
            {
                'name': 'kyrkbok',
                'target_directory': 'dokument/kyrkböcker',
                'filename': 'kyrkbok.pdf',
                'description': 'Utdrag från kyrkbok'
            },
            {
                'name': 'bild',
                'target_directory': 'bilder',
                'filename': 'bild.jpg',
                'description': 'Allmän bild'
            },
            {
                'name': 'porträtt',
                'target_directory': 'bilder/porträtt',
                'filename': 'porträtt.jpg',
                'description': 'Porträttfoto'
            },
            {
                'name': 'anteckning',
                'target_directory': 'anteckningar',
                'filename': 'anteckning.txt',
                'description': 'Allmän anteckning'
            }
        ]

        for doc_type_data in document_types_data:
            doc_type, created = DocumentType.objects.get_or_create(
                name=doc_type_data['name'],
                defaults={
                    'target_directory': doc_type_data['target_directory'],
                    'filename': doc_type_data['filename'],
                    'description': doc_type_data['description']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Skapade dokumenttyp: {doc_type.name}'))
            else:
                self.stdout.write(f'  Dokumenttypen {doc_type.name} finns redan')

        self.stdout.write(self.style.SUCCESS('\nInitial data har skapats!'))

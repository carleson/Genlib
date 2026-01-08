#!/usr/bin/env python
"""
Script för att exportera dokumenttyper från en databas och importera dem till en annan.

Användning:
    # Exportera från nuvarande databas till JSON:
    python export_import_document_types.py export

    # Importera från JSON till new.db.sqlite3:
    python export_import_document_types.py import

    # Direkt kopiering från db.sqlite3 till new.db.sqlite3:
    python export_import_document_types.py copy
"""

import os
import sys
import django
import json
from pathlib import Path
from datetime import datetime

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from documents.models import DocumentType


def export_document_types(output_file='document_types_export.json'):
    """Exportera alla dokumenttyper till JSON-fil"""
    print("Exporterar dokumenttyper från nuvarande databas...")

    document_types = DocumentType.objects.all()

    if not document_types.exists():
        print("Inga dokumenttyper hittades i databasen!")
        return

    # Konvertera till lista av dictionaries
    export_data = []
    for doc_type in document_types:
        export_data.append({
            'name': doc_type.name,
            'target_directory': doc_type.target_directory,
            'filename': doc_type.filename,
            'description': doc_type.description,
        })

    # Spara till JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    print(f"✓ Exporterade {len(export_data)} dokumenttyper till {output_file}")
    print("\nExporterade dokumenttyper:")
    for i, doc_type in enumerate(export_data, 1):
        print(f"  {i}. {doc_type['name']}")
        print(f"     Katalog: {doc_type['target_directory']}")
        print(f"     Filnamn: {doc_type['filename']}")
        if doc_type['description']:
            print(f"     Beskrivning: {doc_type['description'][:60]}...")
        print()


def import_document_types(input_file='document_types_export.json', target_db='new.db.sqlite3'):
    """Importera dokumenttyper från JSON-fil till måldatabas"""
    if not os.path.exists(input_file):
        print(f"Fel: Filen {input_file} finns inte!")
        print("Kör först: python export_import_document_types.py export")
        return

    if not os.path.exists(target_db):
        print(f"Fel: Måldatabasen {target_db} finns inte!")
        return

    # Läs JSON-data
    with open(input_file, 'r', encoding='utf-8') as f:
        import_data = json.load(f)

    print(f"Läste {len(import_data)} dokumenttyper från {input_file}")
    print(f"Importerar till {target_db}...\n")

    # Byt temporärt till måldatabasen
    from django.conf import settings
    original_db = settings.DATABASES['default']['NAME']
    settings.DATABASES['default']['NAME'] = target_db

    # Stäng befintlig connection och öppna ny
    connection.close()

    try:
        # Importera varje dokumenttyp
        imported_count = 0
        updated_count = 0
        skipped_count = 0

        for doc_type_data in import_data:
            # Kontrollera om dokumenttypen redan finns
            existing = DocumentType.objects.filter(name=doc_type_data['name']).first()

            if existing:
                # Uppdatera befintlig
                existing.target_directory = doc_type_data['target_directory']
                existing.filename = doc_type_data['filename']
                existing.description = doc_type_data['description']
                existing.save()
                print(f"✓ Uppdaterade: {doc_type_data['name']}")
                updated_count += 1
            else:
                # Skapa ny
                DocumentType.objects.create(
                    name=doc_type_data['name'],
                    target_directory=doc_type_data['target_directory'],
                    filename=doc_type_data['filename'],
                    description=doc_type_data['description']
                )
                print(f"✓ Importerade: {doc_type_data['name']}")
                imported_count += 1

        print(f"\n{'='*60}")
        print(f"Import klar!")
        print(f"  Nya dokumenttyper: {imported_count}")
        print(f"  Uppdaterade dokumenttyper: {updated_count}")
        print(f"  Totalt bearbetade: {imported_count + updated_count}")
        print(f"{'='*60}")

    finally:
        # Återställ till original databas
        connection.close()
        settings.DATABASES['default']['NAME'] = original_db


def copy_document_types(source_db='db.sqlite3', target_db='new.db.sqlite3'):
    """Direkt kopiering från källdatabas till måldatabas"""
    if not os.path.exists(source_db):
        print(f"Fel: Källdatabasen {source_db} finns inte!")
        return

    if not os.path.exists(target_db):
        print(f"Fel: Måldatabasen {target_db} finns inte!")
        return

    # Exportera från källdatabas
    print("Steg 1: Exporterar från källdatabas...")
    export_document_types('document_types_temp.json')

    # Importera till måldatabas
    print("\nSteg 2: Importerar till måldatabas...")
    import_document_types('document_types_temp.json', target_db)

    # Ta bort temporär fil
    if os.path.exists('document_types_temp.json'):
        os.remove('document_types_temp.json')
        print("\n✓ Temporär fil borttagen")


def show_usage():
    """Visa användningsinstruktioner"""
    print(__doc__)
    print("\nTillgängliga kommandon:")
    print("  export  - Exportera dokumenttyper från nuvarande databas till JSON")
    print("  import  - Importera dokumenttyper från JSON till new.db.sqlite3")
    print("  copy    - Kopiera direkt från db.sqlite3 till new.db.sqlite3")
    print("\nExempel:")
    print("  python export_import_document_types.py export")
    print("  python export_import_document_types.py import")
    print("  python export_import_document_types.py copy")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        show_usage()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'export':
        export_document_types()
    elif command == 'import':
        import_document_types()
    elif command == 'copy':
        copy_document_types()
    else:
        print(f"Okänt kommando: {command}")
        show_usage()
        sys.exit(1)

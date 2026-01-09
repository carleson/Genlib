"""EXIF-hantering för bilder"""
from PIL import Image
from PIL.ExifTags import TAGS
from pathlib import Path
from typing import Dict, Optional


def read_exif_data(image_path: Path) -> Dict[str, str]:
    """
    Läs EXIF-data från en bild.

    Returns:
        Dict med EXIF-data där nycklarna är läsbara tagnamn
    """
    exif_data = {}

    try:
        image = Image.open(image_path)
        exifdata = image.getexif()

        if exifdata:
            for tag_id, value in exifdata.items():
                # Hämta tagnamn
                tag = TAGS.get(tag_id, tag_id)

                # Konvertera värdet till sträng
                if isinstance(value, bytes):
                    try:
                        value = value.decode('utf-8', errors='ignore')
                    except:
                        value = str(value)
                else:
                    value = str(value)

                exif_data[tag] = value

    except Exception as e:
        print(f"Fel vid läsning av EXIF: {e}")

    return exif_data


def get_common_exif_fields(exif_data: Dict[str, str]) -> Dict[str, str]:
    """
    Extrahera vanliga EXIF-fält som användaren vill se/redigera.

    Returns:
        Dict med vanliga EXIF-fält
    """
    common_fields = {
        'DateTime': exif_data.get('DateTime', ''),
        'DateTimeOriginal': exif_data.get('DateTimeOriginal', ''),
        'Make': exif_data.get('Make', ''),
        'Model': exif_data.get('Model', ''),
        'Artist': exif_data.get('Artist', ''),
        'Copyright': exif_data.get('Copyright', ''),
        'ImageDescription': exif_data.get('ImageDescription', ''),
        'Software': exif_data.get('Software', ''),
    }

    return common_fields


def write_exif_data(image_path: Path, exif_updates: Dict[str, str]) -> bool:
    """
    Skriv/uppdatera EXIF-data i en bild.

    Args:
        image_path: Sökväg till bilden
        exif_updates: Dict med EXIF-fält att uppdatera

    Returns:
        True om lyckad, False annars
    """
    try:
        image = Image.open(image_path)

        # Hämta befintlig EXIF-data
        exifdata = image.getexif()

        # Omvänd mappning: tagnamn -> tag_id
        tag_to_id = {v: k for k, v in TAGS.items()}

        # Uppdatera EXIF-data
        for tag_name, value in exif_updates.items():
            if value:  # Endast uppdatera om värdet inte är tomt
                tag_id = tag_to_id.get(tag_name)
                if tag_id:
                    exifdata[tag_id] = value

        # Spara bilden med uppdaterad EXIF
        image.save(image_path, exif=exifdata)
        return True

    except Exception as e:
        print(f"Fel vid skrivning av EXIF: {e}")
        return False

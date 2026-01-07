"""
Context processors för att göra variabler tillgängliga i alla templates.
"""
from pathlib import Path
from django.conf import settings


def version(request):
    """
    Läser versionsnummer från VERSION-filen och gör den tillgänglig i alla templates.

    Returns:
        dict: Dictionary med 'version' som nyckel
    """
    version_file = Path(settings.BASE_DIR) / 'VERSION'
    try:
        if version_file.exists():
            version_number = version_file.read_text().strip()
        else:
            version_number = 'dev'
    except Exception:
        version_number = 'unknown'

    return {
        'genlib_version': version_number
    }

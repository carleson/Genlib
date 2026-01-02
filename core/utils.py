"""Hjälpfunktioner för core-appen"""
from django.conf import settings


def get_media_root():
    """
    Hämta media root från systemkonfiguration.
    Använder standardvärdet från settings om konfiguration inte finns.
    """
    try:
        from .models import SystemConfig
        config = SystemConfig.load()
        return config.get_media_root()
    except Exception:
        # Fallback till settings om något går fel (t.ex. vid migrationer)
        return settings.MEDIA_ROOT


def get_media_url():
    """
    Hämta media URL från systemkonfiguration.
    Använder standardvärdet från settings om konfiguration inte finns.
    """
    try:
        from .models import SystemConfig
        config = SystemConfig.load()
        return f"/{config.media_directory_name}/"
    except Exception:
        # Fallback till settings om något går fel
        return settings.MEDIA_URL

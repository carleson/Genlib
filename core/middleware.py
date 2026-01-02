"""Middleware för core-appen"""
from django.shortcuts import redirect
from django.urls import reverse
from django.db import connection
from django.db.utils import OperationalError


class SetupCheckMiddleware:
    """
    Middleware som kontrollerar om initial setup är genomförd.
    Om inte, redirectar till setup-sidan.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Lista över URL-paths som ska vara tillåtna även utan setup
        allowed_paths = [
            reverse('core:initial_setup'),
            '/admin/',  # Tillåt admin-panelen för manuell konfiguration
            '/static/',  # Tillåt statiska filer
            '/media/',  # Tillåt media-filer
        ]

        # Kolla om nuvarande path är tillåten
        path_allowed = any(
            request.path.startswith(path) for path in allowed_paths
        )

        if not path_allowed:
            # Kontrollera om setup är klar
            try:
                from .models import SetupStatus

                # Kolla om tabellen finns genom att försöka göra en query
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT name FROM sqlite_master "
                        "WHERE type='table' AND name='core_setupstatus'"
                    )
                    table_exists = cursor.fetchone() is not None

                if table_exists:
                    setup_status = SetupStatus.load()
                    if not setup_status.is_completed:
                        # Setup inte klar, redirect
                        return redirect('core:initial_setup')
                else:
                    # Tabellen finns inte, setup behövs
                    return redirect('core:initial_setup')

            except (OperationalError, Exception):
                # Om något går fel (t.ex. DB inte initierad), redirect till setup
                return redirect('core:initial_setup')

        response = self.get_response(request)
        return response

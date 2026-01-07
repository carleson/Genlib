from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.db.models import Count, Sum
from django.utils import timezone
from django.contrib import messages
from django.http import FileResponse, HttpResponse
from persons.models import Person
from documents.models import Document
from .models import SetupStatus, SystemConfig
from .forms import InitialSetupForm
from pathlib import Path
from datetime import datetime
import os


@login_required
def dashboard(request):
    """Dashboard med översikt"""
    # Hämta statistik för inloggad användare
    total_persons = Person.objects.filter(user=request.user).count()

    # Hämta dokument för användarens personer
    user_persons = Person.objects.filter(user=request.user)
    documents = Document.objects.filter(person__in=user_persons)

    total_documents = documents.count()
    total_size = documents.aggregate(total=Sum('file_size'))['total'] or 0

    # Fördelning av filtyper
    file_types = documents.values('file_type').annotate(
        count=Count('id')
    ).order_by('-count')[:5]

    # Senast tillagda personer
    recent_persons = Person.objects.filter(user=request.user).order_by('-created_at')[:5]

    # Senast tillagda dokument
    recent_documents = documents.order_by('-created_at')[:5]

    # Formatera total storlek
    size_display = format_file_size(total_size)

    context = {
        'total_persons': total_persons,
        'total_documents': total_documents,
        'total_size': total_size,
        'size_display': size_display,
        'file_types': file_types,
        'recent_persons': recent_persons,
        'recent_documents': recent_documents,
    }

    return render(request, 'core/dashboard.html', context)


def format_file_size(size):
    """Formatera filstorlek till läsbart format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def initial_setup(request):
    """Initial setup-wizard för ny installation"""
    # Om setup redan är klar, redirect till login
    if SetupStatus.is_setup_complete():
        return redirect('accounts:login')

    if request.method == 'POST':
        form = InitialSetupForm(request.POST, request.FILES)
        if form.is_valid():
            setup_type = form.cleaned_data['setup_type']

            try:
                if setup_type == 'new':
                    # Nytt projekt - skapa superuser och konfigurera
                    user = User.objects.create_superuser(
                        username=form.cleaned_data['username'],
                        email=form.cleaned_data['email'],
                        password=form.cleaned_data['password']
                    )

                    # Konfigurera media-katalog och backup-katalog
                    config = SystemConfig.load()
                    config.media_directory_path = form.cleaned_data['media_directory_path']
                    config.backup_directory_path = form.cleaned_data.get('backup_directory_path', 'backups')
                    config.save()

                    # Importera GEDCOM-fil om uppladdad
                    gedcom_file = form.cleaned_data.get('gedcom_file')
                    if gedcom_file:
                        from .gedcom_importer import GedcomImporter
                        try:
                            importer = GedcomImporter(user)
                            stats = importer.import_file(gedcom_file)

                            # Bygg resultatmeddelande
                            result_msg = f"GEDCOM-import klar: {stats['persons_created']} personer och {stats['relationships_created']} relationer importerade."

                            if stats['errors']:
                                result_msg += f" {len(stats['errors'])} varningar (se logg för detaljer)."
                                messages.warning(request, result_msg)
                            else:
                                messages.success(request, result_msg)

                        except Exception as e:
                            messages.error(
                                request,
                                f'Fel vid GEDCOM-import: {str(e)}. Installationen fortsätter utan GEDCOM-data.'
                            )

                    # Markera setup som klar
                    setup_status = SetupStatus.load()
                    setup_status.is_completed = True
                    setup_status.completed_at = timezone.now()
                    setup_status.save()

                    # Logga in användaren automatiskt
                    login(request, user)

                    messages.success(
                        request,
                        'Installationen är klar! Välkommen till Genlib.'
                    )

                    return redirect('core:dashboard')

                elif setup_type == 'restore':
                    # Återställ från backup
                    from django.conf import settings
                    from pathlib import Path
                    import zipfile
                    import shutil
                    import tempfile

                    backup_file = request.FILES['backup_file']

                    # Spara temporärt
                    temp_dir = Path(tempfile.gettempdir()) / 'genlib_restore'
                    temp_dir.mkdir(exist_ok=True)
                    temp_backup_path = temp_dir / backup_file.name

                    with open(temp_backup_path, 'wb+') as destination:
                        for chunk in backup_file.chunks():
                            destination.write(chunk)

                    # Validera att det är en giltig backup
                    try:
                        with zipfile.ZipFile(temp_backup_path, 'r') as zipf:
                            file_list = zipf.namelist()
                            if 'db.sqlite3' not in file_list:
                                messages.error(
                                    request,
                                    'Ogiltig backup-fil: databas saknas'
                                )
                                temp_backup_path.unlink()
                                return render(request, 'core/initial_setup.html', {'form': form})
                    except zipfile.BadZipFile:
                        messages.error(request, 'Ogiltig ZIP-fil')
                        temp_backup_path.unlink()
                        return render(request, 'core/initial_setup.html', {'form': form})

                    # Kör restore med management command
                    from django.core.management import call_command
                    from io import StringIO

                    # Capture output
                    out = StringIO()
                    try:
                        call_command(
                            'restore',
                            str(temp_backup_path),
                            '--no-confirm',
                            stdout=out
                        )

                        # Städa upp temporär fil
                        temp_backup_path.unlink()

                        # Markera setup som klar
                        setup_status = SetupStatus.load()
                        setup_status.is_completed = True
                        setup_status.completed_at = timezone.now()
                        setup_status.save()

                        messages.success(
                            request,
                            'Backup återställd! Du kan nu logga in med ditt befintliga konto.'
                        )

                        return redirect('accounts:login')

                    except Exception as restore_error:
                        messages.error(
                            request,
                            f'Fel vid återställning: {restore_error}'
                        )
                        # Städa upp
                        if temp_backup_path.exists():
                            temp_backup_path.unlink()

            except Exception as e:
                messages.error(
                    request,
                    f'Ett fel uppstod vid installation: {e}'
                )
    else:
        form = InitialSetupForm()

    context = {
        'form': form,
    }

    return render(request, 'core/initial_setup.html', context)


@login_required
def backup_list(request):
    """Visa lista över backuper och skapa ny backup"""
    from .utils import get_backup_root

    backup_root = Path(get_backup_root())
    backup_root.mkdir(parents=True, exist_ok=True)

    # Hämta alla backup-filer
    backups = []
    if backup_root.exists():
        for backup_file in sorted(backup_root.glob('genlib_backup_*.zip'), reverse=True):
            backups.append({
                'name': backup_file.name,
                'path': backup_file,
                'size': backup_file.stat().st_size,
                'size_display': format_file_size(backup_file.stat().st_size),
                'created': datetime.fromtimestamp(backup_file.stat().st_mtime),
            })

    context = {
        'backups': backups,
        'backup_directory': str(backup_root),
    }

    return render(request, 'core/backup_list.html', context)


@login_required
def create_backup(request):
    """Skapa en ny backup"""
    from django.core.management import call_command
    from io import StringIO
    from .utils import get_backup_root

    if request.method == 'POST':
        try:
            backup_root = Path(get_backup_root())
            backup_root.mkdir(parents=True, exist_ok=True)

            # Kör backup-kommandot
            out = StringIO()
            call_command('backup', output_dir=str(backup_root), stdout=out)

            messages.success(request, 'Backup skapad framgångsrikt!')
            return redirect('core:backup_list')

        except Exception as e:
            messages.error(request, f'Fel vid skapande av backup: {e}')
            return redirect('core:backup_list')

    return redirect('core:backup_list')


@login_required
def download_backup(request, filename):
    """Ladda ner en backup-fil"""
    from .utils import get_backup_root

    backup_root = Path(get_backup_root())
    backup_file = backup_root / filename

    # Säkerhetskontroll: verifiera att filen finns och är inom backup-katalogen
    if not backup_file.exists() or not backup_file.is_relative_to(backup_root):
        messages.error(request, 'Backup-filen hittades inte')
        return redirect('core:backup_list')

    # Returnera filen som nedladdning
    response = FileResponse(open(backup_file, 'rb'), as_attachment=True)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def delete_backup(request, filename):
    """Ta bort en backup-fil"""
    from .utils import get_backup_root

    if request.method == 'POST':
        backup_root = Path(get_backup_root())
        backup_file = backup_root / filename

        # Säkerhetskontroll
        if backup_file.exists() and backup_file.is_relative_to(backup_root):
            try:
                backup_file.unlink()
                messages.success(request, f'Backup {filename} har tagits bort')
            except Exception as e:
                messages.error(request, f'Kunde inte ta bort backup: {e}')
        else:
            messages.error(request, 'Backup-filen hittades inte')

    return redirect('core:backup_list')


@login_required
def restore_backup(request):
    """Återställ från en backup"""
    from django.core.management import call_command
    from io import StringIO
    from .utils import get_backup_root

    if request.method == 'POST':
        filename = request.POST.get('filename')

        if not filename:
            messages.error(request, 'Ingen backup-fil vald')
            return redirect('core:backup_list')

        backup_root = Path(get_backup_root())
        backup_file = backup_root / filename

        # Säkerhetskontroll
        if not backup_file.exists() or not backup_file.is_relative_to(backup_root):
            messages.error(request, 'Backup-filen hittades inte')
            return redirect('core:backup_list')

        try:
            # Kör restore-kommandot
            out = StringIO()
            call_command('restore', str(backup_file), '--no-confirm', stdout=out)

            messages.success(
                request,
                'Backup återställd framgångsrikt! Starta om servern för att ladda nya data.'
            )
            return redirect('core:backup_list')

        except Exception as e:
            messages.error(request, f'Fel vid återställning av backup: {e}')
            return redirect('core:backup_list')

    return redirect('core:backup_list')

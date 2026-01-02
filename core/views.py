from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.db.models import Count, Sum
from django.utils import timezone
from django.contrib import messages
from persons.models import Person
from documents.models import Document
from .models import SetupStatus, SystemConfig
from .forms import InitialSetupForm


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

                    # Konfigurera media-katalog
                    config = SystemConfig.load()
                    config.media_directory_path = form.cleaned_data['media_directory_path']
                    config.save()

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

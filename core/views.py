from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from persons.models import Person
from documents.models import Document


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

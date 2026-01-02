from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ChecklistTemplateItem, PersonChecklistItem, Person


@receiver(post_save, sender=ChecklistTemplateItem)
def sync_template_item_to_persons(sender, instance, created, **kwargs):
    """
    När ett mallsobjekt skapas eller uppdateras, synka till alla personer.
    Bevarar användarens avklaradstatus.
    """
    if not instance.template.is_active:
        return

    if created:
        # Nytt mallsobjekt - lägg till i alla befintliga personer
        persons = Person.objects.all()
        person_items = []

        for person in persons:
            # Kontrollera om det redan finns (borde inte, men var säker)
            if not PersonChecklistItem.objects.filter(
                person=person,
                template_item=instance
            ).exists():
                person_items.append(PersonChecklistItem(
                    person=person,
                    template_item=instance,
                    title=instance.title,
                    description=instance.description,
                    category=instance.category,
                    priority=instance.priority,
                    order=instance.order,
                ))

        PersonChecklistItem.objects.bulk_create(person_items, ignore_conflicts=True)
    else:
        # Befintligt mallsobjekt uppdaterat - synka metadata men bevara avklaradstatus
        PersonChecklistItem.objects.filter(template_item=instance).update(
            title=instance.title,
            description=instance.description,
            category=instance.category,
            priority=instance.priority,
            order=instance.order,
            # Observera: is_completed, completed_at, notes uppdateras INTE
        )


@receiver(post_delete, sender=ChecklistTemplateItem)
def remove_template_item_from_persons(sender, instance, **kwargs):
    """
    När ett mallsobjekt raderas, ta bort från alla personer.
    """
    PersonChecklistItem.objects.filter(template_item=instance).delete()


@receiver(post_save, sender=Person)
def initialize_person_checklist(sender, instance, created, **kwargs):
    """
    När en ny person skapas, initiera deras checklista från aktiva mallar.
    """
    if not created:
        return

    # Hämta alla objekt från aktiva mallar
    active_template_items = ChecklistTemplateItem.objects.filter(
        template__is_active=True
    )

    person_items = []
    for template_item in active_template_items:
        person_items.append(PersonChecklistItem(
            person=instance,
            template_item=template_item,
            title=template_item.title,
            description=template_item.description,
            category=template_item.category,
            priority=template_item.priority,
            order=template_item.order,
        ))

    PersonChecklistItem.objects.bulk_create(person_items, ignore_conflicts=True)

from django.apps import AppConfig


class PersonsConfig(AppConfig):
    name = "persons"

    def ready(self):
        import persons.signals  # noqa

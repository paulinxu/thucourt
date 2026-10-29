from django.apps import AppConfig


class CoachingConfig(AppConfig):
    name = "coaching"

    def ready(self):
        from . import signals  # noqa: F401

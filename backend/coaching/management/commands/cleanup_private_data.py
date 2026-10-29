from datetime import timedelta

from coaching.models import CoachingTurn, MediaAsset
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Dry-run private media retention; --execute deletes expired files and observations, and marks stale jobs failed."

    def add_arguments(self, parser):
        parser.add_argument("--execute", action="store_true")

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=settings.MEDIA_RETENTION_DAYS)
        qs = MediaAsset.objects.filter(created_at__lt=cutoff)
        self.stdout.write(f"Expired media: {qs.count()}")
        if options["execute"]:
            qs.delete()
            stale = timezone.now() - timedelta(minutes=15)
            for model in [MediaAsset, CoachingTurn]:
                model.objects.filter(
                    state__in=["queued", "processing"], created_at__lt=stale
                ).update(state="failed", error="任务超时，可重试。")
            self.stdout.write(
                self.style.SUCCESS(
                    "Retention cleanup completed. Saved advice remains historical output."
                )
            )

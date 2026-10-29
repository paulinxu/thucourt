from courts.models import Posting
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Persist expired posting states; discovery already excludes past slots without this job."

    def handle(self, *args, **options):
        count = Posting.objects.filter(status="active", starts_at__lte=timezone.now()).update(
            status="expired"
        )
        self.stdout.write(f"Expired {count} postings.")

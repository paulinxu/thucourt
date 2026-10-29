from django.conf import settings
from django.db import models
from django.utils import timezone


class Area(models.Model):
    code = models.SlugField(unique=True)
    name = models.CharField(max_length=30)
    court_count = models.PositiveSmallIntegerField()
    reference_price = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.name


class Slot(models.Model):
    start = models.TimeField(unique=True)
    end = models.TimeField()

    class Meta:
        ordering = ["start"]

    def __str__(self):
        return f"{self.start:%H:%M}–{self.end:%H:%M}"


class Posting(models.Model):
    KINDS = [(x, x) for x in ["buy", "sell", "trade", "game"]]
    STATES = [(x, x) for x in ["active", "fulfilled", "cancelled", "expired"]]
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="postings"
    )
    kind = models.CharField(max_length=8, choices=KINDS)
    area = models.ForeignKey(Area, on_delete=models.PROTECT)
    date = models.DateField(db_index=True)
    slot = models.ForeignKey(Slot, on_delete=models.PROTECT)
    court = models.PositiveSmallIntegerField(null=True, blank=True)
    # Trades deliberately have no court number. Desired options are validated by the service.
    desired = models.JSONField(default=list, blank=True)
    mode = models.CharField(
        max_length=8, choices=[("singles", "singles"), ("doubles", "doubles")], blank=True
    )
    players_needed = models.PositiveSmallIntegerField(null=True, blank=True)
    min_level = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)
    max_level = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)
    note = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=12, choices=STATES, default="active")
    starts_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "slot__start", "-created_at"]
        indexes = [models.Index(fields=["area", "date", "kind", "status"])]

    @property
    def effective_status(self):
        return (
            "expired"
            if self.status == "active" and self.starts_at <= timezone.now()
            else self.status
        )

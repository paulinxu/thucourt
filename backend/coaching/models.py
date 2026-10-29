import uuid

from django.conf import settings
from django.db import models


def private_path(instance, filename):
    return f"{instance.owner_id}/{uuid.uuid4().hex}"


class MediaAsset(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(upload_to=private_path)
    name = models.CharField(max_length=150)
    kind = models.CharField(max_length=8)
    subject = models.CharField(max_length=200)
    size = models.PositiveIntegerField()
    state = models.CharField(max_length=12, default="queued")
    observations = models.JSONField(default=dict)
    error = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class CoachingSession(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


class CoachingTurn(models.Model):
    session = models.ForeignKey(CoachingSession, on_delete=models.CASCADE, related_name="turns")
    question = models.CharField(max_length=2000)
    media_ids = models.JSONField(default=list)
    state = models.CharField(max_length=12, default="queued")
    answer = models.TextField(blank=True)
    plan = models.JSONField(default=dict)
    evidence_ids = models.JSONField(default=list)
    provider = models.CharField(max_length=32, blank=True)
    model = models.CharField(max_length=100, blank=True)
    prompt_version = models.CharField(max_length=20, default="coach-v1")
    usage = models.JSONField(default=dict)
    latency_ms = models.PositiveIntegerField(default=0)
    error = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class TrainingPlan(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    source = models.OneToOneField(CoachingTurn, on_delete=models.SET_NULL, null=True)
    content = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)


class DailyQuota(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "date"], name="unique_daily_quota")]


class ProviderBudget(models.Model):
    # One global counter; reserved atomically before every paid HTTP attempt.
    key = models.CharField(primary_key=True, max_length=20, default="remote")
    calls = models.PositiveIntegerField(default=0)

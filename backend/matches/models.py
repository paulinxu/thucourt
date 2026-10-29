from django.conf import settings
from django.db import models


class Match(models.Model):
    submitter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    mode = models.CharField(max_length=8, choices=[("singles", "singles"), ("doubles", "doubles")])
    played_on = models.DateField()
    sets = models.JSONField()
    winner = models.PositiveSmallIntegerField(choices=[(0, "draw"), (1, "team1"), (2, "team2")])
    status = models.CharField(
        max_length=12,
        default="pending",
        choices=[(x, x) for x in ["pending", "confirmed", "rejected"]],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True)

    class Meta:
        ordering = ["-played_on", "-id"]


class Participant(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    team = models.PositiveSmallIntegerField(choices=[(1, "team1"), (2, "team2")])
    decision = models.CharField(
        max_length=10,
        default="pending",
        choices=[(x, x) for x in ["pending", "confirmed", "rejected"]],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["match", "user"], name="unique_match_participant")
        ]


class RatingEvent(models.Model):
    match = models.ForeignKey(Match, on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    track = models.CharField(max_length=8)
    delta = models.SmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["match", "user"], name="one_rating_event_per_player")
        ]

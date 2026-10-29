from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Friendship(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="friend_sent"
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="friend_received"
    )
    pair_key = models.CharField(max_length=64, unique=True)
    status = models.CharField(
        max_length=10,
        default="pending",
        choices=[(x, x) for x in ["pending", "accepted", "declined"]],
    )
    created_at = models.DateTimeField(auto_now_add=True)


class Block(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocks"
    )
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocked_by"
    )

    class Meta:
        constraints = [models.UniqueConstraint(fields=["owner", "target"], name="unique_block")]


class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages"
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_messages"
    )
    body = models.CharField(max_length=2000)
    client_id = models.UUIDField()
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(fields=["sender", "client_id"], name="idempotent_message")
        ]
        indexes = [models.Index(fields=["recipient", "read_at"])]


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    kind = models.CharField(max_length=20)
    text = models.CharField(max_length=200)
    object_id = models.PositiveBigIntegerField(null=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]


class BehaviorRating(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="behavior_given"
    )
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="behavior_received"
    )
    stars = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["author", "target"], name="one_behavior_rating"),
            models.CheckConstraint(
                condition=models.Q(stars__gte=1, stars__lte=5), name="behavior_range"
            ),
        ]


class TennisFeedback(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feedback_given"
    )
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feedback_received"
    )
    comment = models.CharField(max_length=2000)
    strokes = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

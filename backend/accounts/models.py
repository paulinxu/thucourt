from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class User(AbstractUser):
    display_name = models.CharField(max_length=40)
    wechat_id = models.CharField(max_length=128, unique=True, null=True, blank=True)
    verification = models.CharField(
        max_length=12,
        default="unsubmitted",
        choices=[(x, x) for x in ["unsubmitted", "pending", "approved", "rejected"]],
    )
    level = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=2.5,
        validators=[MinValueValidator(1), MaxValueValidator(5.5)],
    )
    bio = models.CharField(max_length=300, blank=True)
    singles_rating = models.IntegerField(default=1000)
    doubles_rating = models.IntegerField(default=1000)
    ai_consent = models.BooleanField(default=False)

    def __str__(self):
        return self.display_name or self.username


class VerificationRequest(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="identity_request")
    real_name = models.CharField(max_length=60)
    student_id = models.CharField(max_length=20)
    status = models.CharField(
        max_length=12,
        default="pending",
        choices=[(x, x) for x in ["pending", "approved", "rejected"]],
    )
    reviewer = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="reviews"
    )
    note = models.CharField(max_length=300, blank=True)
    submitted_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student_id"],
                condition=models.Q(status="approved"),
                name="unique_approved_student",
            )
        ]

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from rest_framework.exceptions import ValidationError

from .models import User, VerificationRequest
from .services import review_verification


@admin.register(User)
class PlayerAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "网球资料",
            {
                "fields": (
                    "display_name",
                    "level",
                    "bio",
                    "verification",
                    "singles_rating",
                    "doubles_rating",
                    "ai_consent",
                )
            },
        ),
    )
    readonly_fields = ("verification", "singles_rating", "doubles_rating")
    list_display = ("username", "display_name", "verification", "is_active")


@admin.register(VerificationRequest)
class VerificationAdmin(admin.ModelAdmin):
    list_display = ("user", "student_id", "status", "submitted_at", "reviewer")
    list_filter = ("status",)
    readonly_fields = (
        "user",
        "real_name",
        "student_id",
        "status",
        "reviewer",
        "reviewed_at",
        "submitted_at",
    )
    actions = ["approve", "reject"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def review(self, request, queryset, decision):
        for item in queryset:
            try:
                review_verification(item.pk, request.user, decision, item.note)
            except ValidationError as exc:
                self.message_user(request, str(exc.detail), level=messages.ERROR)

    @admin.action(description="通过学生身份审核")
    def approve(self, request, queryset):
        self.review(request, queryset, "approved")

    @admin.action(description="拒绝学生身份审核（请先填写说明）")
    def reject(self, request, queryset):
        self.review(request, queryset, "rejected")

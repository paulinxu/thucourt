from community.models import Notification
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import User, VerificationRequest


@transaction.atomic
def review_verification(request_id, reviewer, decision, note=""):
    if decision not in {"approved", "rejected"}:
        raise ValidationError("审核结果必须是 approved 或 rejected。")
    # Serialize reviews to prevent two accounts claiming the same student ID.
    User.objects.select_for_update().get(pk=reviewer.pk)
    request = VerificationRequest.objects.select_for_update().get(pk=request_id)
    if request.status != "pending":
        raise ValidationError("此申请已审核。")
    if (
        decision == "approved"
        and VerificationRequest.objects.filter(student_id=request.student_id, status="approved")
        .exclude(pk=request.pk)
        .exists()
    ):
        raise ValidationError("该学号已有认证账号。")
    request.status, request.note, request.reviewer = decision, note, reviewer
    request.reviewed_at = timezone.now()
    request.save()
    User.objects.filter(pk=request.user_id).update(verification=decision)
    Notification.objects.create(
        user_id=request.user_id,
        kind="verification",
        text="身份审核已通过"
        if decision == "approved"
        else "身份审核未通过，请检查个人中心的说明。",
    )
    return request

from django.conf import settings
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, Throttled

from .models import DailyQuota


def consume_quota(user):
    if settings.AI_PROVIDER == "remote" and not user.ai_consent:
        raise PermissionDenied("请先在个人中心同意由所选模型服务商处理私有教练数据。")
    quota, _ = DailyQuota.objects.get_or_create(user=user, date=timezone.localdate())
    if not DailyQuota.objects.filter(pk=quota.pk, count__lt=settings.AI_DAILY_LIMIT).update(
        count=F("count") + 1
    ):
        raise Throttled(detail="今日教练与媒体分析额度已用完，请明天再来。")


def enqueue(task, obj):
    try:
        task.delay(obj.pk)
    except Exception:
        type(obj).objects.filter(pk=obj.pk).update(
            state="failed", error="后台队列暂时不可用，请稍后重试。"
        )

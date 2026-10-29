import tempfile
from pathlib import Path

from django.core.files.base import ContentFile
from django.db import transaction
from django.http import FileResponse
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .media import MAX_SIZE, clean_image, video_duration
from .models import CoachingSession, CoachingTurn, MediaAsset, TrainingPlan
from .provider import ProviderError
from .serializers import (
    MediaSerializer,
    PlanSerializer,
    QuestionSerializer,
    SessionSerializer,
    TurnSerializer,
)
from .services import consume_quota, enqueue
from .tasks import process_media, process_turn


class MediaViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = MediaSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return MediaAsset.objects.filter(owner=self.request.user).order_by("-id")

    def create(self, request):
        upload = request.FILES.get("file")
        subject = str(request.data.get("subject", "")).strip()
        if not upload or upload.size == 0 or upload.size > MAX_SIZE:
            raise ValidationError("请选择不超过 100 MB 的照片或短视频。")
        if not 1 <= len(subject) <= 200:
            raise ValidationError("请描述需要分析的球员（例如：近端蓝衣球员），最多 200 字。")
        name = Path(upload.name).name[:150]
        extension = Path(name).suffix.lower()
        try:
            if extension in {".jpg", ".jpeg", ".png", ".webp"}:
                kind = "image"
                content = ContentFile(clean_image(upload.read()), name="photo.jpg")
            elif extension in {".mp4", ".mov", ".webm"}:
                kind = "video"
                with tempfile.NamedTemporaryFile(suffix=extension) as temp:
                    for chunk in upload.chunks():
                        temp.write(chunk)
                    temp.flush()
                    video_duration(temp.name)
                upload.seek(0)
                content = upload
            else:
                raise ValidationError("支持 JPEG、PNG、WebP 图片及 MP4、MOV、WebM 视频。")
        except ProviderError as exc:
            raise ValidationError(str(exc)) from exc
        consume_quota(request.user)
        item = MediaAsset(
            owner=request.user, name=name, kind=kind, subject=subject, size=content.size
        )
        try:
            item.file.save(name, content, save=False)
            item.save()
        except Exception:
            if item.file:
                item.file.delete(save=False)
            raise
        enqueue(process_media, item)
        item.refresh_from_db()
        return Response(MediaSerializer(item).data, status=201)

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        asset = self.get_object()
        try:
            response = FileResponse(
                asset.file.open("rb"),
                as_attachment=True,
                filename="photo.jpg" if asset.kind == "image" else asset.name,
            )
        except OSError as exc:
            raise ValidationError("文件已过期或不可读取。") from exc
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response

    @action(detail=True, methods=["post"])
    def retry(self, request, pk=None):
        asset = self.get_object()
        if asset.state != "failed":
            raise ValidationError("仅失败任务可以重试。")
        consume_quota(request.user)
        if not MediaAsset.objects.filter(pk=asset.pk, state="failed").update(
            state="queued", error=""
        ):
            raise ValidationError("该任务已经重试。")
        enqueue(process_media, asset)
        asset.refresh_from_db()
        return Response(MediaSerializer(asset).data)


class SessionViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SessionSerializer

    def get_queryset(self):
        return (
            CoachingSession.objects.filter(owner=self.request.user)
            .prefetch_related("turns")
            .order_by("-id")
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"])
    def ask(self, request, pk=None):
        session = self.get_object()
        data = QuestionSerializer(data=request.data, context={"request": request})
        data.is_valid(raise_exception=True)
        consume_quota(request.user)
        with transaction.atomic():
            CoachingSession.objects.select_for_update().get(pk=session.pk)
            if session.turns.filter(state__in=["queued", "processing"]).exists():
                raise ValidationError("请等待当前回答完成。")
            turn = CoachingTurn.objects.create(session=session, **data.validated_data)
        enqueue(process_turn, turn)
        turn.refresh_from_db()
        return Response(TurnSerializer(turn).data, status=201)


class TurnViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = TurnSerializer

    def get_queryset(self):
        return CoachingTurn.objects.filter(session__owner=self.request.user)

    @action(detail=True, methods=["post"])
    def retry(self, request, pk=None):
        turn = self.get_object()
        if turn.state != "failed":
            raise ValidationError("仅失败任务可以重试。")
        consume_quota(request.user)
        if not CoachingTurn.objects.filter(pk=turn.pk, state="failed").update(
            state="queued", error=""
        ):
            raise ValidationError("该任务已经重试。")
        enqueue(process_turn, turn)
        turn.refresh_from_db()
        return Response(TurnSerializer(turn).data)

    @action(detail=True, methods=["post"])
    def save_plan(self, request, pk=None):
        turn = self.get_object()
        if turn.state != "ready" or not turn.plan:
            raise ValidationError("此回答没有可保存的训练计划。")
        plan, created = TrainingPlan.objects.get_or_create(
            source=turn, defaults={"owner": request.user, "content": turn.plan}
        )
        return Response(PlanSerializer(plan).data, status=201 if created else 200)


class PlanViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = PlanSerializer

    def get_queryset(self):
        return TrainingPlan.objects.filter(owner=self.request.user).order_by("-id")

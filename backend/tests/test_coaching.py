import io
import json
import subprocess
from unittest.mock import Mock, patch

import httpx
import imageio_ffmpeg
import pytest
from coaching.evidence import collect_evidence
from coaching.models import CoachingSession, CoachingTurn, MediaAsset, ProviderBudget, TrainingPlan
from coaching.provider import ProviderError, remote_json
from coaching.schemas import validate_plan
from community.models import TennisFeedback
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.exceptions import ValidationError

pytestmark = pytest.mark.django_db


def image_upload():
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), color="green").save(buffer, format="JPEG", exif=b"")
    return SimpleUploadedFile("swing.jpg", buffer.getvalue(), content_type="image/jpeg")


def create_session(client):
    response = client.post("/api/coach/sessions/", {"title": "训练计划"})
    assert response.status_code == 201
    return response.data["id"]


def test_evidence_is_owner_scoped_and_anonymous(users):
    TennisFeedback.objects.create(
        author=users[1], target=users[0], comment="my feedback", strokes={"backhand": 2}
    )
    TennisFeedback.objects.create(
        author=users[0], target=users[1], comment="private-other-player", strokes={"serve": 2}
    )
    evidence, ids = collect_evidence(users[0].pk, [])
    encoded = json.dumps(evidence)
    assert "my feedback" in encoded and "private-other-player" not in encoded
    assert all(
        key not in encoded for key in ["student_id", "real_name", "author", "username", "wechat_id"]
    )
    assert len(ids) == 2


def test_offline_plan_save_and_session_privacy(client, other_client):
    sid = create_session(client)
    response = client.post(f"/api/coach/sessions/{sid}/ask/", {"question": "制定两周反手训练计划"})
    assert response.status_code == 201, response.data
    assert response.data["state"] == "ready", response.data
    assert response.data["provider"] == "demo" and "离线" in response.data["answer"]
    tid = response.data["id"]
    assert TrainingPlan.objects.count() == 0
    assert other_client.get(f"/api/coach/sessions/{sid}/").status_code == 404
    assert other_client.get(f"/api/coach/turns/{tid}/").status_code == 404
    assert other_client.post(f"/api/coach/turns/{tid}/save_plan/").status_code == 404
    for _ in range(2):
        assert client.post(f"/api/coach/turns/{tid}/save_plan/").status_code in [200, 201]
    assert TrainingPlan.objects.count() == 1
    pid = TrainingPlan.objects.get().pk
    assert other_client.get(f"/api/coach/plans/{pid}/").status_code == 404
    assert client.delete(f"/api/coach/sessions/{sid}/").status_code == 204
    assert TrainingPlan.objects.get().source is None
    assert client.delete(f"/api/coach/plans/{pid}/").status_code == 204


def test_photo_validation_owner_download_and_delete(
    client, other_client, django_capture_on_commit_callbacks
):
    response = client.post(
        "/api/coach/media/", {"file": image_upload(), "subject": "近端蓝衣球员"}, format="multipart"
    )
    assert response.status_code == 201, response.data
    assert response.data["state"] == "ready"
    assert response.data["observations"]["observations"] == []
    mid = response.data["id"]
    asset = MediaAsset.objects.get(pk=mid)
    path = asset.file.path
    assert other_client.get(f"/api/coach/media/{mid}/download/").status_code == 404
    own = client.get(f"/api/coach/media/{mid}/download/")
    assert own.status_code == 200 and own["Cache-Control"] == "private, no-store"
    own.close()
    sid = create_session(other_client)
    assert (
        other_client.post(
            f"/api/coach/sessions/{sid}/ask/", {"question": "分析", "media_ids": [mid]}
        ).status_code
        == 400
    )
    sid = create_session(client)
    answer = client.post(
        f"/api/coach/sessions/{sid}/ask/", {"question": "结合影像", "media_ids": [mid]}
    )
    assert answer.data["state"] == "ready"
    assert f"media:{mid}" in answer.data["evidence_ids"]
    with django_capture_on_commit_callbacks(execute=True):
        assert client.delete(f"/api/coach/media/{mid}/").status_code == 204
    from pathlib import Path

    assert not Path(path).exists()


@pytest.mark.parametrize(
    "name,content",
    [("fake.jpg", b"not an image"), ("script.svg", b"<svg/>"), ("fake.mp4", b"not a video")],
)
def test_reject_disguised_upload(client, name, content):
    response = client.post(
        "/api/coach/media/",
        {"file": SimpleUploadedFile(name, content), "subject": "本人"},
        format="multipart",
    )
    assert response.status_code == 400
    assert not MediaAsset.objects.exists()


def test_video_real_decode_and_frame_bound(client, tmp_path):
    path = tmp_path / "clip.mp4"
    subprocess.run(
        [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=green:s=64x64:d=1",
            "-c:v",
            "libx264",
            "-threads",
            "1",
            str(path),
        ],
        check=True,
        timeout=20,
    )
    response = client.post(
        "/api/coach/media/",
        {
            "file": SimpleUploadedFile("clip.mp4", path.read_bytes(), content_type="video/mp4"),
            "subject": "合成测试画面，无人物",
        },
        format="multipart",
    )
    assert response.status_code == 201, response.data
    assert response.data["state"] == "ready", response.data
    assert 1 <= len(response.data["observations"]["frames"]) <= 8


def test_video_duration_limit(client, tmp_path):
    path = tmp_path / "long.mp4"
    subprocess.run(
        [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=green:s=32x32:r=1:d=61",
            "-c:v",
            "libx264",
            "-threads",
            "1",
            str(path),
        ],
        check=True,
        timeout=20,
    )
    response = client.post(
        "/api/coach/media/",
        {"file": SimpleUploadedFile("long.mp4", path.read_bytes()), "subject": "合成"},
        format="multipart",
    )
    assert response.status_code == 400
    assert not MediaAsset.objects.exists()


def test_quota_and_consent(client, settings, users):
    sid = create_session(client)
    settings.AI_PROVIDER = "remote"
    assert client.post(f"/api/coach/sessions/{sid}/ask/", {"question": "hello"}).status_code == 403
    settings.AI_PROVIDER = "demo"
    settings.AI_DAILY_LIMIT = 1
    assert client.post(f"/api/coach/sessions/{sid}/ask/", {"question": "hello"}).status_code == 201
    assert client.post(f"/api/coach/sessions/{sid}/ask/", {"question": "again"}).status_code == 429


def test_remote_failure_and_retry_never_fabricates(client, settings, users):
    sid = create_session(client)
    settings.AI_PROVIDER = "remote"
    users[0].ai_consent = True
    users[0].save()
    with patch("coaching.tasks.coach", side_effect=ProviderError("模型服务超时")):
        result = client.post(f"/api/coach/sessions/{sid}/ask/", {"question": "training"})
    assert result.data["state"] == "failed" and result.data["plan"] == {}
    settings.AI_PROVIDER = "demo"
    retried = client.post(f"/api/coach/turns/{result.data['id']}/retry/")
    assert retried.data["state"] == "ready"


def test_reject_invented_evidence_and_invalid_lengths(client):
    sid = create_session(client)
    result = client.post(f"/api/coach/sessions/{sid}/ask/", {"question": "计划"})
    plan = result.data["plan"]
    with pytest.raises(ValidationError):
        validate_plan({**plan, "evidence_ids": ["feedback:999999"]}, ["profile:self"])
    with pytest.raises(ValidationError):
        validate_plan({**plan, "session_minutes": 119}, result.data["evidence_ids"])
    with patch(
        "coaching.tasks.coach",
        return_value=({"answer": "test", "plan": {**plan, "evidence_ids": ["media:999999"]}}, {}),
    ):
        bad = client.post(f"/api/coach/sessions/{sid}/ask/", {"question": "bad"})
    assert bad.data["state"] == "failed"
    assert client.post(f"/api/coach/turns/{bad.data['id']}/save_plan/").status_code == 400


def test_remote_retries_and_global_budget(settings):
    settings.AI_API_KEY, settings.AI_MODEL = "test-key", "test-model"
    settings.AI_REMOTE_CALL_LIMIT = 2
    request = httpx.Request("POST", "https://example.test/chat/completions")
    failure = httpx.Response(503, request=request)
    with (
        patch("coaching.provider.httpx.post", return_value=failure),
        patch("coaching.provider.time.sleep"),
    ):
        with pytest.raises(ProviderError):
            remote_json([])
    assert ProviderBudget.objects.get().calls == 2


def test_remote_json_success(settings):
    settings.AI_API_KEY, settings.AI_MODEL = "test-key", "test-model"
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "choices": [{"message": {"content": '{"answer":"ok","plan":null}'}}],
        "usage": {"total_tokens": 25},
    }
    with patch("coaching.provider.httpx.post", return_value=response) as request:
        data, usage = remote_json([{"role": "user", "content": "hi"}])
    assert data["answer"] == "ok" and usage["total_tokens"] == 25
    assert request.call_args.kwargs["timeout"] == 35


def test_deleted_session_job_noop(client, users):
    from coaching.tasks import process_turn

    sid = create_session(client)
    turn = CoachingTurn.objects.create(session_id=sid, question="hi")
    tid = turn.pk
    CoachingSession.objects.filter(pk=sid).delete()
    process_turn(tid)
    assert not CoachingTurn.objects.exists()

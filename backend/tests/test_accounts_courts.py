from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from accounts.models import VerificationRequest
from courts.models import Posting
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "path",
    [
        "/api/players/",
        "/api/postings/",
        "/api/matches/",
        "/api/messages/1/",
        "/api/coach/media/",
        "/api/feedback/",
        "/api/config/",
    ],
)
def test_member_routes_deny_anonymous_and_pending(path, users):
    client = APIClient()
    assert client.get(path).status_code == 403
    users[0].verification = "pending"
    users[0].save()
    client.force_authenticate(users[0])
    assert client.get(path).status_code == 403


def test_verification_requires_manual_admin_review(client, users):
    users[0].verification = "unsubmitted"
    users[0].save()
    result = client.post(
        "/api/me/verification/", {"real_name": "测试同学", "student_id": "2026000001"}
    )
    assert result.status_code == 201
    users[0].refresh_from_db()
    assert users[0].verification == "pending"
    assert (
        client.post(f"/api/reviews/{result.data['id']}/", {"decision": "approved"}).status_code
        == 403
    )
    users[1].is_staff = True
    users[1].save()
    client.force_authenticate(users[1])
    assert (
        client.post(f"/api/reviews/{result.data['id']}/", {"decision": "approved"}).status_code
        == 200
    )
    users[0].refresh_from_db()
    assert users[0].verification == "approved"
    public = client.get(f"/api/players/{users[0].pk}/").data
    assert not {"student_id", "real_name", "username", "wechat_id", "ai_consent"} & set(public)
    assert client.get("/api/me/verification/").data is None


def test_one_approved_account_per_student(users):
    VerificationRequest.objects.create(
        user=users[0], real_name="a", student_id="2026000001", status="approved"
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        VerificationRequest.objects.create(
            user=users[1], real_name="b", student_id="2026000001", status="approved"
        )


def test_profile_cannot_set_verified_or_ratings(client, users):
    assert (
        client.patch(
            "/api/me/", {"verification": "approved", "singles_rating": 9999, "is_staff": True}
        ).status_code
        == 200
    )
    users[0].refresh_from_db()
    assert users[0].singles_rating == 1000 and not users[0].is_staff
    assert client.patch("/api/me/", {"level": "3.1"}).status_code == 400
    assert client.patch("/api/me/", {"level": "5.5"}).status_code == 200


def test_login_csrf_and_demo_disable(users, settings):
    client = APIClient(enforce_csrf_checks=True)
    login = {"username": users[0].username, "password": "test-password-2026"}
    assert client.post("/api/auth/login/", login).status_code == 403
    token = client.get("/api/auth/session/").data["csrf_token"]
    assert client.post("/api/auth/login/", login, HTTP_X_CSRFTOKEN=token).status_code == 200
    fresh = client.get("/api/auth/session/").data["csrf_token"]
    assert client.patch("/api/me/", {"bio": "hello"}).status_code == 403
    assert client.post("/api/auth/logout/", HTTP_X_CSRFTOKEN=fresh).status_code == 200
    settings.DEMO_MODE = False
    token = client.get("/api/auth/session/").data["csrf_token"]
    assert client.post("/api/auth/login/", login, HTTP_X_CSRFTOKEN=token).status_code == 403


def test_wechat_state_replay_and_exchange(settings):
    settings.WECHAT_APP_ID = "test-app"
    settings.WECHAT_APP_SECRET = "test-secret"
    settings.WECHAT_REDIRECT_URI = "https://court.example/api/auth/wechat/callback/"
    client = APIClient()
    assert client.get("/api/auth/wechat/start/").status_code == 302
    state = client.session["wechat_state"]["value"]
    response = Mock()
    response.json.return_value = {"openid": "test-wechat-identity"}
    with patch("accounts.views.httpx.get", return_value=response):
        result = client.get("/api/auth/wechat/callback/", {"state": state, "code": "one-time-code"})
    assert result.status_code == 302
    assert client.get("/api/auth/session/").data["user"]["verification"] == "unsubmitted"
    assert (
        client.get(
            "/api/auth/wechat/callback/", {"state": state, "code": "one-time-code"}
        ).status_code
        == 400
    )


def test_config_and_exact_grids(client, config):
    data = client.get("/api/config/").data
    assert len(data["dates"]) == 4 and len(data["slots"]) == 14
    assert data["slots"][0]["start"] == "08:00:00" and data["slots"][-1]["end"] == "22:00:00"
    for code, count in [("area", 14), ("indoor", 4)]:
        grid = client.get(
            "/api/postings/grid/", {"area": config[code].pk, "date": config["date"]}
        ).data
        assert len(grid["rows"]) == 14 and grid["columns"] == count
        assert all(len(r["cells"]) == count for r in grid["rows"])
    grid = client.get("/api/postings/grid/", {"area": config["area"].pk, "kind": "game"}).data
    assert len(grid["rows"]) == 14 and grid["columns"] == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"court": 15},
        {"court": 0},
        {"date": "2020-01-01"},
        {"date": "2099-01-01"},
        {"slot": 9999},
        {"area": 9999},
        {"kind": "fake"},
    ],
)
def test_bad_booking_inputs(client, booking, changes):
    assert client.post("/api/postings/", {**booking, **changes}).status_code == 400


def test_shanghai_boundary_and_started_slot(client, booking, config):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    boundary = datetime(2026, 10, 30, 16, 1, tzinfo=ZoneInfo("UTC"))  # Shanghai Oct 31 00:01
    with patch("django.utils.timezone.now", return_value=boundary):
        data = client.get("/api/config/").data
        assert data["dates"][0] == "2026-10-31"
        assert client.post("/api/postings/", {**booking, "date": "2026-10-30"}).status_code == 400
        assert client.post("/api/postings/", {**booking, "date": "2026-11-03"}).status_code == 201
    later = datetime(2026, 10, 31, 18, 1, tzinfo=ZoneInfo("Asia/Shanghai"))
    with patch("django.utils.timezone.now", return_value=later):
        assert client.post("/api/postings/", {**booking, "date": "2026-10-31"}).status_code == 400


def test_lifecycle_owner_delete_and_grid(client, other_client, config, posting):
    args = {"area": config["area"].pk, "date": config["date"]}
    grid = client.get("/api/postings/grid/", args).data
    assert sum(c["sell"] for r in grid["rows"] for c in r["cells"]) == 1
    assert other_client.delete(f"/api/postings/{posting.pk}/").status_code == 403
    assert (
        other_client.patch(f"/api/postings/{posting.pk}/", {"status": "fulfilled"}).status_code
        == 403
    )
    assert client.patch(f"/api/postings/{posting.pk}/", {"status": "fulfilled"}).status_code == 200
    assert client.get("/api/postings/").data["count"] == 0
    assert client.get("/api/postings/", {"mine": True}).data["count"] == 1
    assert client.delete(f"/api/postings/{posting.pk}/").status_code == 204


@pytest.mark.parametrize("state", ["active", "fulfilled", "cancelled", "expired"])
def test_delete_any_lifecycle(client, posting, state):
    posting.status = state
    posting.save()
    assert client.delete(f"/api/postings/{posting.pk}/").status_code == 204


def test_expired_items_excluded_without_cron(client, posting):
    posting.starts_at = timezone.now() - timedelta(hours=1)
    posting.save()
    assert client.get("/api/postings/").data["count"] == 0
    assert client.get("/api/postings/", {"mine": True}).data["results"][0]["status"] == "expired"
    assert client.patch(f"/api/postings/{posting.pk}/", {"status": "fulfilled"}).status_code == 400


def test_trade_roundtrip_no_court_and_filters(client, other_client, booking, config):
    payload = {
        **booking,
        "kind": "trade",
        "court": None,
        "desired": [
            {
                "area": config["indoor"].pk,
                "date": config["date"].isoformat(),
                "slot": config["slot"].pk,
            }
        ],
    }
    response = client.post("/api/postings/", payload)
    assert response.status_code == 201, response.data
    assert response.data["desired"] == payload["desired"]
    assert client.get("/api/postings/", {"kind": "trade"}).data["count"] == 0
    assert other_client.get("/api/postings/", {"kind": "trade"}).data["count"] == 1
    assert client.post("/api/postings/", {**payload, "court": 1}).status_code == 400
    assert client.post("/api/postings/", {**payload, "desired": []}).status_code == 400


def test_games_have_booking_and_level_constraints(client, booking):
    payload = {
        **booking,
        "kind": "game",
        "mode": "doubles",
        "players_needed": 3,
        "min_level": "2.5",
        "max_level": "4.0",
    }
    assert client.post("/api/postings/", payload).status_code == 201
    assert client.get("/api/postings/", {"kind": "game", "level": "2.0"}).data["count"] == 0
    assert client.get("/api/postings/", {"kind": "game", "level": "3.5"}).data["count"] == 1
    for changes in [
        {"players_needed": 4},
        {"min_level": 5},
        {"court": None},
        {"mode": "singles", "players_needed": 2},
    ]:
        assert client.post("/api/postings/", {**payload, **changes}).status_code == 400
    assert Posting.objects.count() == 1

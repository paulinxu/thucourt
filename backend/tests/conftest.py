from datetime import datetime, timedelta

import pytest
from accounts.models import User
from courts.models import Area, Posting, Slot
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def isolated_settings(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    settings.AI_PROVIDER = "demo"
    settings.AI_DAILY_LIMIT = 100
    settings.DEMO_MODE = True
    settings.CELERY_TASK_ALWAYS_EAGER = True
    cache.clear()


@pytest.fixture
def users(db):
    return [
        User.objects.create_user(
            username=f"player{i}",
            display_name=f"球友{i}",
            password="test-password-2026",
            verification="approved",
        )
        for i in range(6)
    ]


@pytest.fixture
def client(users):
    api = APIClient()
    api.force_authenticate(users[0])
    return api


@pytest.fixture
def other_client(users):
    api = APIClient()
    api.force_authenticate(users[1])
    return api


@pytest.fixture
def config(db):
    return {
        "area": Area.objects.get(code="zijing"),
        "indoor": Area.objects.get(code="beiguan"),
        "slot": Slot.objects.get(start="18:00"),
        "date": timezone.localdate() + timedelta(days=1),
    }


@pytest.fixture
def booking(config):
    return {
        "kind": "sell",
        "area": config["area"].pk,
        "date": config["date"].isoformat(),
        "slot": config["slot"].pk,
        "court": 1,
        "note": "测试场地",
    }


@pytest.fixture
def posting(users, config):
    return Posting.objects.create(
        owner=users[0],
        kind="sell",
        area=config["area"],
        date=config["date"],
        slot=config["slot"],
        court=1,
        starts_at=timezone.make_aware(datetime.combine(config["date"], config["slot"].start)),
    )


@pytest.fixture
def match_payload(users):
    return {
        "mode": "singles",
        "team1": [users[0].pk],
        "team2": [users[1].pk],
        "played_on": timezone.localdate().isoformat(),
        "sets": [{"a": 6, "b": 4}],
        "winner": 1,
    }

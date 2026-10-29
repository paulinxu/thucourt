from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import uuid4

import pytest
from accounts.models import User
from community.models import BehaviorRating, Friendship, Message, TennisFeedback
from community.services import pair_key
from django.db import close_old_connections, connection
from django.utils import timezone
from matches.models import Match, RatingEvent
from matches.services import decide_match

pytestmark = pytest.mark.django_db


def test_messaging_without_friendship_idempotency_and_read(client, other_client, users):
    payload = {"body": "下课一起打球吗？", "client_id": str(uuid4())}
    path = f"/api/messages/{users[1].pk}/"
    first = client.post(path, payload)
    assert first.status_code == 201
    assert client.post(path, payload).status_code == 200
    assert Message.objects.count() == 1
    assert client.post(path, {**payload, "body": "different"}).status_code == 400
    assert client.post(f"/api/messages/{users[2].pk}/", payload).status_code == 400
    messages = other_client.get(f"/api/messages/{users[0].pk}/").data
    assert messages["messages"][0]["body"] == payload["body"]
    assert (
        other_client.post(
            f"/api/messages/{users[0].pk}/read/", {"through": first.data["id"]}
        ).status_code
        == 200
    )
    assert Message.objects.get().read_at
    client.force_authenticate(users[2])
    assert client.get(f"/api/messages/{users[0].pk}/").data["messages"] == []


def test_block_bidirectional_contact(client, other_client, users):
    assert other_client.post("/api/blocks/", {"target": users[0].pk}).status_code == 200
    for sender, target in [(client, users[1]), (other_client, users[0])]:
        assert (
            sender.post(
                f"/api/messages/{target.pk}/", {"body": "hello", "client_id": str(uuid4())}
            ).status_code
            == 403
        )
        assert sender.post("/api/friends/", {"target": target.pk}).status_code == 403
    assert other_client.delete(f"/api/blocks/{users[0].pk}/").status_code == 204
    assert (
        client.post(
            f"/api/messages/{users[1].pk}/", {"body": "hello", "client_id": str(uuid4())}
        ).status_code
        == 201
    )


def test_friend_requests_and_private_feedback(client, other_client, users):
    assert client.post(f"/api/behavior/{users[1].pk}/", {"stars": 5}).status_code == 403
    response = client.post("/api/friends/", {"target": users[1].pk})
    assert response.status_code == 201
    pk = response.data["id"]
    assert client.post(f"/api/friends/{pk}/", {"decision": "accepted"}).status_code == 404
    assert other_client.post(f"/api/friends/{pk}/", {"decision": "accepted"}).status_code == 200
    assert client.post("/api/friends/", {"target": users[1].pk}).status_code == 400
    for value in [2, 5]:
        assert client.post(f"/api/behavior/{users[1].pk}/", {"stars": value}).status_code == 200
    assert BehaviorRating.objects.count() == 1
    public = other_client.get(f"/api/players/{users[1].pk}/").data
    assert public["behavior"] == {"average": 5.0, "count": 1}
    assert "author" not in str(public)
    payload = {
        "target": users[1].pk,
        "comment": "反手可以更稳定。",
        "strokes": {"backhand": 2, "serve": 4},
    }
    assert client.post("/api/feedback/", payload).status_code == 201
    assert client.get("/api/feedback/").data["count"] == 0
    received = other_client.get("/api/feedback/").data
    assert received["count"] == 1
    assert not {"author", "target"} & set(received["results"][0])
    client.force_authenticate(users[2])
    assert client.get("/api/feedback/", {"target": users[1].pk}).data["count"] == 0
    assert client.get(f"/api/behavior/{users[1].pk}/").status_code == 403
    assert TennisFeedback.objects.count() == 1


@pytest.mark.parametrize(
    "strokes",
    [{}, {"unknown": 3}, {"serve": 0}, {"serve": 6}, {"serve": True}, {"serve": 2.5}, [1, 2]],
)
def test_feedback_validation(client, users, strokes):
    Friendship.objects.create(
        sender=users[0],
        recipient=users[1],
        pair_key=pair_key(users[0].pk, users[1].pk),
        status="accepted",
    )
    assert (
        client.post(
            "/api/feedback/", {"target": users[1].pk, "comment": "good", "strokes": strokes}
        ).status_code
        == 400
    )


def test_singles_confirm_once_immutable_and_private_pending(
    client, other_client, users, match_payload
):
    result = client.post("/api/matches/", match_payload)
    assert result.status_code == 201, result.data
    mid = result.data["id"]
    client.force_authenticate(users[2])
    assert client.get("/api/matches/").data["count"] == 0
    assert client.get(f"/api/matches/{mid}/").status_code == 404
    assert client.post(f"/api/matches/{mid}/confirm/", {"decision": "confirmed"}).status_code == 404
    client.force_authenticate(users[0])
    assert client.post(f"/api/matches/{mid}/confirm/", {"decision": "confirmed"}).status_code == 403
    assert RatingEvent.objects.count() == 0
    for _ in range(3):
        assert (
            other_client.post(f"/api/matches/{mid}/confirm/", {"decision": "confirmed"}).status_code
            == 200
        )
    users[0].refresh_from_db()
    users[1].refresh_from_db()
    assert (users[0].singles_rating, users[1].singles_rating) == (1010, 990)
    assert (users[0].doubles_rating, users[1].doubles_rating) == (1000, 1000)
    assert RatingEvent.objects.count() == 2
    assert (
        other_client.post(f"/api/matches/{mid}/confirm/", {"decision": "rejected"}).status_code
        == 400
    )
    assert client.patch(f"/api/matches/{mid}/", {"winner": 2}).status_code == 405
    assert client.delete(f"/api/matches/{mid}/").status_code == 405
    client.force_authenticate(users[2])
    assert client.get("/api/matches/").data["count"] == 1


def test_doubles_all_three_and_independent_ratings(client, users, match_payload):
    data = {
        **match_payload,
        "mode": "doubles",
        "team1": [users[0].pk, users[1].pk],
        "team2": [users[2].pk, users[3].pk],
    }
    result = client.post("/api/matches/", data)
    assert result.status_code == 201
    mid = result.data["id"]
    for i in [1, 2]:
        client.force_authenticate(users[i])
        assert (
            client.post(f"/api/matches/{mid}/confirm/", {"decision": "confirmed"}).status_code
            == 200
        )
        assert Match.objects.get(pk=mid).status == "pending"
        assert RatingEvent.objects.count() == 0
    client.force_authenticate(users[3])
    assert client.post(f"/api/matches/{mid}/confirm/", {"decision": "confirmed"}).status_code == 200
    for index, user in enumerate(users[:4]):
        user.refresh_from_db()
        assert user.doubles_rating == (1010 if index < 2 else 990)
        assert user.singles_rating == 1000
    assert RatingEvent.objects.count() == 4


def test_draw_and_rejection(client, other_client, users, match_payload):
    result = client.post(
        "/api/matches/",
        {**match_payload, "winner": 0, "sets": [{"a": 6, "b": 4}, {"a": 3, "b": 6}]},
    )
    assert result.status_code == 201
    assert (
        other_client.post(
            f"/api/matches/{result.data['id']}/confirm/", {"decision": "confirmed"}
        ).status_code
        == 200
    )
    assert not RatingEvent.objects.exclude(delta=0).exists()
    result = client.post("/api/matches/", match_payload)
    mid = result.data["id"]
    assert (
        other_client.post(f"/api/matches/{mid}/confirm/", {"decision": "rejected"}).status_code
        == 200
    )
    assert Match.objects.get(pk=mid).status == "rejected"
    assert (
        other_client.post(f"/api/matches/{mid}/confirm/", {"decision": "confirmed"}).status_code
        == 400
    )
    assert RatingEvent.objects.count() == 2


@pytest.mark.parametrize(
    "sets,winner,valid",
    [
        ([{"a": 6, "b": 0}], 1, True),
        ([{"a": 5, "b": 7}], 2, True),
        ([{"a": 7, "b": 6, "tiebreak_a": 8, "tiebreak_b": 6}], 1, True),
        ([{"a": 6, "b": 7, "tiebreak_a": 6, "tiebreak_b": 8}], 2, True),
        (
            [{"a": 6, "b": 1}, {"a": 1, "b": 6}, {"a": 12, "b": 10, "kind": "match_tiebreak"}],
            1,
            True,
        ),
        ([{"a": 7, "b": 6}], 1, False),
        ([{"a": 6, "b": 5}], 1, False),
        ([{"a": 6, "b": 4}], 2, False),
        ([{"a": 6, "b": 4}], 0, False),
        ([{"a": 6, "b": 6}], 0, False),
        ([{"a": -1, "b": 6}], 2, False),
        ([{"a": 7, "b": 6, "tiebreak_a": 7, "tiebreak_b": 6}], 1, False),
        ([{"a": 7, "b": 6, "tiebreak_a": 5, "tiebreak_b": 7}], 1, False),
        ([{"a": 10, "b": 5, "kind": "match_tiebreak"}], 1, False),
        ([{"a": 6, "b": 0}] * 3, 1, False),
        ([], 0, False),
    ],
)
def test_score_rules(client, match_payload, sets, winner, valid):
    response = client.post("/api/matches/", {**match_payload, "sets": sets, "winner": winner})
    assert response.status_code == (201 if valid else 400), response.data


def test_participant_and_date_validation(client, users, match_payload):
    for changes in [
        {"team2": [users[0].pk]},
        {"team1": [users[2].pk]},
        {"team2": [99999]},
        {"played_on": (timezone.localdate() + timedelta(days=1)).isoformat()},
    ]:
        assert client.post("/api/matches/", {**match_payload, **changes}).status_code == 400


@pytest.mark.django_db(transaction=True)
def test_postgres_concurrent_confirmation(client, users, match_payload):
    if connection.vendor != "postgresql":
        pytest.skip(
            "Real row-lock race is exercised by the PostgreSQL CI job; SQLite cannot emulate it."
        )
    result = client.post("/api/matches/", match_payload)
    mid, uid = result.data["id"], users[1].pk

    def confirm():
        close_old_connections()
        try:
            decide_match(mid, User.objects.get(pk=uid), "confirmed")
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda _: confirm(), range(4)))
    assert RatingEvent.objects.filter(match_id=mid).count() == 2
    users[0].refresh_from_db()
    assert users[0].singles_rating == 1010

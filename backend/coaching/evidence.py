from accounts.models import User
from community.models import TennisFeedback
from matches.models import Match

from .models import MediaAsset, TrainingPlan


def get_my_profile(user):
    # Explicit allowlist: no real name, student ID, messages, or rating authors.
    return {
        "id": "profile:self",
        "level": str(user.level),
        "singles_rating": user.singles_rating,
        "doubles_rating": user.doubles_rating,
    }


def get_my_feedback(user):
    return [
        {
            "id": f"feedback:{x.pk}",
            "comment": x.comment,
            "strokes": x.strokes,
            "date": x.created_at.isoformat(),
            "source": "anonymous_peer_opinion",
        }
        for x in TennisFeedback.objects.filter(target=user).order_by("-id")[:20]
    ]


def get_my_match_summary(user):
    result = []
    for match in (
        Match.objects.filter(participants__user=user, status="confirmed")
        .prefetch_related("participants")
        .order_by("-played_on", "-id")[:10]
    ):
        own = next(p for p in match.participants.all() if p.user_id == user.pk)
        result.append(
            {
                "id": f"match:{match.pk}",
                "mode": match.mode,
                "date": match.played_on.isoformat(),
                "sets": match.sets,
                "outcome": "draw"
                if match.winner == 0
                else "win"
                if own.team == match.winner
                else "loss",
                "source": "confirmed_match",
            }
        )
    return result


def get_my_training_plans(user):
    return [
        {"id": f"plan:{x.pk}", "content": x.content, "source": "historical_saved_advice"}
        for x in TrainingPlan.objects.filter(owner=user).order_by("-id")[:3]
    ]


def get_my_media_analysis(user, media_ids):
    return [
        {
            "id": f"media:{x.pk}",
            "observations": x.observations,
            "source": "generated_interpretation",
        }
        for x in MediaAsset.objects.filter(owner=user, id__in=media_ids, state="ready").order_by(
            "id"
        )[:4]
    ]


def collect_evidence(user_id, media_ids):
    user = User.objects.get(pk=user_id)
    evidence = {
        "profile": get_my_profile(user),
        "feedback": get_my_feedback(user),
        "matches": get_my_match_summary(user),
        "plans": get_my_training_plans(user),
        "media": get_my_media_analysis(user, media_ids),
    }
    ids = [evidence["profile"]["id"]] + [
        x["id"] for key in ["feedback", "matches", "plans", "media"] for x in evidence[key]
    ]
    return evidence, ids

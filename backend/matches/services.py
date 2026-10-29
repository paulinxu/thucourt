from accounts.models import User
from community.models import Notification
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Match, Participant, RatingEvent


@transaction.atomic
def submit_match(user, data):
    teams = [data.pop("team1"), data.pop("team2")]
    match = Match.objects.create(submitter=user, **data)
    for team, ids in enumerate(teams, start=1):
        for uid in ids:
            Participant.objects.create(
                match=match,
                user_id=uid,
                team=team,
                decision="confirmed" if uid == user.pk else "pending",
            )
            if uid != user.pk:
                Notification.objects.create(
                    user_id=uid,
                    kind="match",
                    text=f"{user.display_name} 提交了比赛 #{match.pk}，请确认比分",
                    object_id=match.pk,
                )
    return match


@transaction.atomic
def decide_match(match_id, user, decision):
    if decision not in {"confirmed", "rejected"}:
        raise ValidationError("请选择确认或拒绝。")
    # One row lock per match makes final confirmation and rating settlement indivisible.
    match = Match.objects.select_for_update().get(pk=match_id)
    participant = Participant.objects.filter(match=match, user=user).first()
    if participant is None or match.submitter_id == user.pk:
        raise PermissionDenied("仅其他参赛者可以确认。")
    if match.status != "pending":
        if participant.decision == decision:
            return match  # A retried confirmation never applies ratings again.
        raise ValidationError("比赛已结束确认，不可修改。")
    if participant.decision != "pending":
        if participant.decision == decision:
            return match
        raise ValidationError("已提交的确认决定不可修改。")
    participant.decision = decision
    participant.save(update_fields=["decision"])
    if decision == "rejected":
        match.status = "rejected"
        match.save(update_fields=["status"])
        Notification.objects.create(
            user=match.submitter,
            kind="match",
            text=f"比赛 #{match.pk} 被拒绝，请核对比分后重新提交",
            object_id=match.pk,
        )
        return match
    participants = list(match.participants.order_by("user_id"))
    if any(p.decision != "confirmed" for p in participants):
        return match
    # Stable ordering avoids deadlocks between different matches sharing players.
    list(
        User.objects.select_for_update()
        .filter(pk__in=[p.user_id for p in participants])
        .order_by("pk")
    )
    field = f"{match.mode}_rating"
    for p in participants:
        delta = 0 if match.winner == 0 else (10 if p.team == match.winner else -10)
        RatingEvent.objects.create(match=match, user_id=p.user_id, track=match.mode, delta=delta)
        User.objects.filter(pk=p.user_id).update(**{field: F(field) + delta})
        Notification.objects.create(
            user_id=p.user_id,
            kind="match",
            text=f"比赛 #{match.pk} 已生效，{match.mode} 积分 {delta:+d}",
            object_id=match.pk,
        )
    match.status, match.confirmed_at = "confirmed", timezone.now()
    match.save(update_fields=["status", "confirmed_at"])
    return match

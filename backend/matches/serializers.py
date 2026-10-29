from accounts.models import User
from accounts.serializers import PublicUserSerializer
from django.utils import timezone
from rest_framework import serializers

from .models import Match, Participant


def integer(value, minimum=0, maximum=30):
    return type(value) is int and minimum <= value <= maximum


def legal_tiebreak(a, b, target):
    if not integer(a) or not integer(b):
        return False
    hi, lo = max(a, b), min(a, b)
    return (hi == target and lo <= target - 2) or (hi > target and hi - lo == 2)


def validate_scores(sets, winner):
    if not isinstance(sets, list) or not 1 <= len(sets) <= 3:
        raise serializers.ValidationError("请输入 1–3 盘结构化比分。")
    wins = [0, 0]
    for index, score in enumerate(sets):
        if not isinstance(score, dict) or set(score) - {
            "a",
            "b",
            "kind",
            "tiebreak_a",
            "tiebreak_b",
        }:
            raise serializers.ValidationError("比分字段无效。")
        a, b, kind = score.get("a"), score.get("b"), score.get("kind", "set")
        if not integer(a) or not integer(b) or a == b or max(wins) >= 2:
            raise serializers.ValidationError("比分无效，或比赛已结束。")
        hi, lo = max(a, b), min(a, b)
        if kind == "match_tiebreak":
            if (
                index != 2
                or wins != [1, 1]
                or not legal_tiebreak(a, b, 10)
                or "tiebreak_a" in score
                or "tiebreak_b" in score
            ):
                raise serializers.ValidationError(
                    "抢十仅用于各胜一盘后的决胜盘，至少 10 分且净胜两分。"
                )
        elif kind == "set":
            if not ((hi == 6 and lo <= 4) or (hi == 7 and lo in {5, 6})):
                raise serializers.ValidationError("普通盘支持 6:0–4、7:5 或 7:6。")
            if (hi, lo) == (7, 6):
                ta, tb = score.get("tiebreak_a"), score.get("tiebreak_b")
                if not legal_tiebreak(ta, tb, 7) or (ta > tb) != (a > b):
                    raise serializers.ValidationError("7:6 必须填写同胜方的合法抢七比分。")
            elif "tiebreak_a" in score or "tiebreak_b" in score:
                raise serializers.ValidationError("仅 7:6 盘需要附加抢七比分。")
        else:
            raise serializers.ValidationError("不支持的盘类型。")
        wins[0 if a > b else 1] += 1
    expected = 0 if wins[0] == wins[1] else (1 if wins[0] > wins[1] else 2)
    if winner != expected:
        raise serializers.ValidationError("胜方或平局与盘比分不一致。")
    return sets


class MatchInputSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=["singles", "doubles"])
    team1 = serializers.ListField(
        child=serializers.IntegerField(min_value=1), min_length=1, max_length=2
    )
    team2 = serializers.ListField(
        child=serializers.IntegerField(min_value=1), min_length=1, max_length=2
    )
    played_on = serializers.DateField()
    sets = serializers.JSONField()
    winner = serializers.ChoiceField(choices=[0, 1, 2])

    def validate(self, attrs):
        size = 1 if attrs["mode"] == "singles" else 2
        ids = attrs["team1"] + attrs["team2"]
        if len(attrs["team1"]) != size or len(attrs["team2"]) != size or len(set(ids)) != 2 * size:
            raise serializers.ValidationError("参赛人数或队伍无效，球员不能重复。")
        if self.context["request"].user.pk not in ids:
            raise serializers.ValidationError("提交者必须参加比赛。")
        if User.objects.filter(pk__in=ids, verification="approved", is_active=True).count() != len(
            ids
        ):
            raise serializers.ValidationError("所有参赛者必须通过认证。")
        if attrs["played_on"] > timezone.localdate():
            raise serializers.ValidationError("不能提交未来的比赛。")
        if attrs["played_on"].year < 2000:
            raise serializers.ValidationError("比赛日期不能早于 2000 年。")
        validate_scores(attrs["sets"], attrs["winner"])
        return attrs


class ParticipantSerializer(serializers.ModelSerializer):
    user = PublicUserSerializer(read_only=True)

    class Meta:
        model = Participant
        fields = ["user", "team", "decision"]


class MatchSerializer(serializers.ModelSerializer):
    participants = ParticipantSerializer(many=True, read_only=True)

    class Meta:
        model = Match
        fields = [
            "id",
            "submitter",
            "mode",
            "played_on",
            "sets",
            "winner",
            "status",
            "participants",
            "created_at",
            "confirmed_at",
        ]
        read_only_fields = fields

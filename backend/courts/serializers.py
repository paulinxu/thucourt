from datetime import datetime, timedelta
from decimal import Decimal

from accounts.serializers import PublicUserSerializer
from django.utils import timezone
from rest_framework import serializers

from .models import Area, Posting, Slot


class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ["id", "code", "name", "court_count", "reference_price"]


class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = ["id", "start", "end"]


def validate_booking(area, date, slot, court=None, require_court=True):
    today = timezone.localdate()
    if not today <= date <= today + timedelta(days=3):
        raise serializers.ValidationError("日期必须是上海时区的今天至未来三天。")
    start = timezone.make_aware(datetime.combine(date, slot.start))
    if start <= timezone.now():
        raise serializers.ValidationError("不能发布已经开始的时段。")
    if require_court and (court is None or not 1 <= court <= area.court_count):
        raise serializers.ValidationError(f"场地编号应为 1–{area.court_count}。")
    return start


class DesiredSerializer(serializers.Serializer):
    area = serializers.PrimaryKeyRelatedField(queryset=Area.objects.all())
    date = serializers.DateField()
    slot = serializers.PrimaryKeyRelatedField(queryset=Slot.objects.all())

    def validate(self, attrs):
        validate_booking(**attrs, require_court=False)
        return attrs

    def to_representation(self, instance):
        return dict(instance)


class PostingSerializer(serializers.ModelSerializer):
    owner = PublicUserSerializer(read_only=True)
    status = serializers.CharField(source="effective_status", read_only=True)
    desired = DesiredSerializer(many=True, required=False)
    area_name = serializers.CharField(source="area.name", read_only=True)
    area_code = serializers.CharField(source="area.code", read_only=True)
    price = serializers.IntegerField(source="area.reference_price", read_only=True)
    start = serializers.TimeField(source="slot.start", read_only=True)
    end = serializers.TimeField(source="slot.end", read_only=True)

    class Meta:
        model = Posting
        fields = [
            "id",
            "owner",
            "kind",
            "area",
            "area_name",
            "area_code",
            "date",
            "slot",
            "start",
            "end",
            "court",
            "price",
            "desired",
            "mode",
            "players_needed",
            "min_level",
            "max_level",
            "note",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        kind = attrs["kind"]
        attrs["starts_at"] = validate_booking(
            attrs["area"],
            attrs["date"],
            attrs["slot"],
            attrs.get("court"),
            require_court=kind != "trade",
        )
        if kind == "trade":
            if attrs.get("court") is not None:
                raise serializers.ValidationError("换场不需要场地编号。")
            desired = attrs.get("desired", [])
            if not 1 <= len(desired) <= 8:
                raise serializers.ValidationError("请填写 1–8 个期望时段。")
            if any(
                d["area"] == attrs["area"]
                and d["date"] == attrs["date"]
                and d["slot"] == attrs["slot"]
                for d in desired
            ):
                raise serializers.ValidationError("期望时段不能与持有时段完全相同。")
            attrs["desired"] = [
                {"area": d["area"].pk, "date": d["date"].isoformat(), "slot": d["slot"].pk}
                for d in desired
            ]
        elif attrs.get("desired"):
            raise serializers.ValidationError("只有换场可以填写期望时段。")
        if kind == "game":
            mode, needed = attrs.get("mode"), attrs.get("players_needed")
            low, high = attrs.get("min_level"), attrs.get("max_level")
            if (
                mode not in {"singles", "doubles"}
                or needed is None
                or not 1 <= needed <= (1 if mode == "singles" else 3)
            ):
                raise serializers.ValidationError(
                    "请正确填写比赛形式与缺少人数（单打 1 人，双打 1–3 人）。"
                )
            if (
                low is None
                or high is None
                or not Decimal("1") <= low <= high <= Decimal("5.5")
                or low * 2 != int(low * 2)
                or high * 2 != int(high * 2)
            ):
                raise serializers.ValidationError("水平范围应在 1.0–5.5 之间，以 0.5 为步长。")
        else:
            attrs.update(mode="", players_needed=None, min_level=None, max_level=None)
        return attrs

from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Area, Posting, Slot
from .serializers import AreaSerializer, PostingSerializer, SlotSerializer


class DiscoveryFilter(serializers.Serializer):
    area = serializers.IntegerField(min_value=1, required=False)
    date = serializers.DateField(required=False)
    slot = serializers.IntegerField(min_value=1, required=False)
    court = serializers.IntegerField(min_value=1, required=False)
    level = serializers.DecimalField(
        max_digits=2, decimal_places=1, min_value=1, max_value=Decimal("5.5"), required=False
    )
    kind = serializers.ChoiceField(
        choices=["buy", "sell", "trade", "game", "market"], required=False
    )
    mine = serializers.BooleanField(default=False)


def active_postings():
    return Posting.objects.filter(
        status="active",
        starts_at__gt=timezone.now(),
        owner__verification="approved",
        owner__is_active=True,
    )


class ConfigurationView(APIView):
    def get(self, request):
        return Response(
            {
                "areas": AreaSerializer(Area.objects.order_by("id"), many=True).data,
                "slots": SlotSerializer(Slot.objects.all(), many=True).data,
                "dates": [(timezone.localdate() + timedelta(days=i)).isoformat() for i in range(4)],
                "timezone": "Asia/Shanghai",
                "now": timezone.now(),
            }
        )


class PostingViewSet(viewsets.ModelViewSet):
    serializer_class = PostingSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        if self.action != "list":
            return Posting.objects.select_related("owner", "area", "slot").all()
        params = DiscoveryFilter(data=self.request.query_params)
        params.is_valid(raise_exception=True)
        filters = params.validated_data
        qs = (
            Posting.objects.filter(owner=self.request.user)
            if filters["mine"]
            else active_postings()
        )
        for field in ["area", "date", "slot", "court"]:
            if field in filters:
                qs = qs.filter(**{field: filters[field]})
        kind = filters.get("kind")
        if kind == "market":
            qs = qs.filter(kind__in=["buy", "sell"])
        elif kind:
            qs = qs.filter(kind=kind)
        if kind == "trade" and not filters["mine"]:
            qs = qs.exclude(owner=self.request.user)
        if "level" in filters:
            qs = qs.filter(min_level__lte=filters["level"], max_level__gte=filters["level"])
        return qs.select_related("owner", "area", "slot")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        item = self.get_object()
        if item.owner_id != request.user.pk:
            raise PermissionDenied("只能管理自己发布的需求。")
        state = request.data.get("status")
        if set(request.data) != {"status"} or state not in {"fulfilled", "cancelled"}:
            raise ValidationError("只能将需求标记为 fulfilled 或 cancelled。")
        if item.effective_status != "active":
            raise ValidationError("只有有效需求可以变更状态；仍可删除此记录。")
        item.status = state
        item.save(update_fields=["status"])
        return Response(self.get_serializer(item).data)

    def perform_destroy(self, instance):
        if instance.owner_id != self.request.user.pk:
            raise PermissionDenied("只能删除自己发布的需求。")
        instance.delete()

    @action(detail=False, methods=["get"])
    def grid(self, request):
        params = DiscoveryFilter(data=request.query_params)
        params.is_valid(raise_exception=True)
        args = params.validated_data
        try:
            area = Area.objects.get(pk=args.get("area"))
        except Area.DoesNotExist as exc:
            raise ValidationError("请选择场地区域。") from exc
        date = args.get("date", timezone.localdate())
        if not timezone.localdate() <= date <= timezone.localdate() + timedelta(days=3):
            raise ValidationError("网格仅展示今天至未来三天。")
        is_game = args.get("kind") == "game"
        qs = (
            active_postings()
            .filter(area=area, date=date, kind__in=["game"] if is_game else ["buy", "sell"])
            .select_related("slot")
        )
        if args.get("kind") in {"buy", "sell"}:
            qs = qs.filter(kind=args["kind"])
        if "level" in args:
            qs = qs.filter(min_level__lte=args["level"], max_level__gte=args["level"])
        if "slot" in args:
            qs = qs.filter(slot_id=args["slot"])
        items = list(qs)
        rows = []
        for slot in Slot.objects.all():
            cells = []
            for court in [None] if is_game else range(1, area.court_count + 1):
                subset = [
                    x for x in items if x.slot_id == slot.pk and (is_game or x.court == court)
                ]
                cells.append(
                    {
                        "court": court,
                        "buy": sum(x.kind == "buy" for x in subset),
                        "sell": sum(x.kind == "sell" for x in subset),
                        "game": len(subset) if is_game else 0,
                        "ids": [x.pk for x in subset],
                    }
                )
            rows.append({"slot": slot.pk, "start": slot.start, "end": slot.end, "cells": cells})
        return Response(
            {
                "area": AreaSerializer(area).data,
                "date": date,
                "columns": 1 if is_game else area.court_count,
                "rows": rows,
            }
        )

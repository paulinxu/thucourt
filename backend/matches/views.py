from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import Match
from .serializers import MatchInputSerializer, MatchSerializer
from .services import decide_match, submit_match


class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MatchSerializer

    def get_queryset(self):
        qs = Match.objects.filter(
            Q(status="confirmed") | Q(participants__user=self.request.user)
        ).distinct()
        if self.request.query_params.get("mine") == "true":
            qs = qs.filter(participants__user=self.request.user)
        if self.request.query_params.get("status"):
            qs = qs.filter(status=self.request.query_params["status"])
        mode = self.request.query_params.get("mode")
        if mode:
            if mode not in {"singles", "doubles"}:
                raise ValidationError("比赛形式无效。")
            qs = qs.filter(mode=mode)
        return qs.prefetch_related("participants__user")

    def create(self, request):
        data = MatchInputSerializer(data=request.data, context={"request": request})
        data.is_valid(raise_exception=True)
        match = submit_match(request.user, dict(data.validated_data))
        return Response(MatchSerializer(match).data, status=201)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        get_object_or_404(self.get_queryset(), pk=pk)
        match = decide_match(pk, request.user, request.data.get("decision"))
        return Response(MatchSerializer(match).data)

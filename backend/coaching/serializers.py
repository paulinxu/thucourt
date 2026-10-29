from rest_framework import serializers

from .models import CoachingSession, CoachingTurn, MediaAsset, TrainingPlan


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaAsset
        fields = [
            "id",
            "name",
            "kind",
            "subject",
            "size",
            "state",
            "observations",
            "error",
            "created_at",
        ]
        read_only_fields = fields


class TurnSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachingTurn
        fields = [
            "id",
            "question",
            "media_ids",
            "state",
            "answer",
            "plan",
            "evidence_ids",
            "provider",
            "model",
            "prompt_version",
            "usage",
            "latency_ms",
            "error",
            "created_at",
        ]
        read_only_fields = fields


class SessionSerializer(serializers.ModelSerializer):
    turns = TurnSerializer(many=True, read_only=True)

    class Meta:
        model = CoachingSession
        fields = ["id", "title", "turns", "created_at"]
        read_only_fields = ["id", "created_at"]


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingPlan
        fields = ["id", "source", "content", "created_at"]
        read_only_fields = fields


class QuestionSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=2000)
    media_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1), max_length=4, default=list
    )

    def validate_media_ids(self, value):
        if len(set(value)) != len(value):
            raise serializers.ValidationError("媒体不能重复选择。")
        if MediaAsset.objects.filter(
            owner=self.context["request"].user, pk__in=value, state="ready"
        ).count() != len(value):
            raise serializers.ValidationError("只能引用自己已完成分析的媒体。")
        return value

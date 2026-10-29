from django.db.models import Avg, Count
from rest_framework import serializers

from .models import User, VerificationRequest


class PublicUserSerializer(serializers.ModelSerializer):
    behavior = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "display_name",
            "level",
            "bio",
            "singles_rating",
            "doubles_rating",
            "behavior",
        ]
        read_only_fields = fields

    def get_behavior(self, obj) -> dict:
        stats = obj.behavior_received.aggregate(average=Avg("stars"), count=Count("id"))
        if stats["average"] is not None:
            stats["average"] = round(stats["average"], 2)
        return stats


class MeSerializer(PublicUserSerializer):
    class Meta(PublicUserSerializer.Meta):
        fields = PublicUserSerializer.Meta.fields + [
            "username",
            "verification",
            "is_staff",
            "ai_consent",
        ]
        read_only_fields = fields


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["display_name", "level", "bio", "ai_consent"]

    def validate_level(self, value):
        if value * 2 != int(value * 2):
            raise serializers.ValidationError("水平以 0.5 为步长。")
        return value

    def validate_display_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("昵称不能为空。")
        return value.strip()


class VerificationSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(source="user.display_name", read_only=True)

    class Meta:
        model = VerificationRequest
        fields = [
            "id",
            "user",
            "display_name",
            "real_name",
            "student_id",
            "status",
            "note",
            "submitted_at",
            "reviewed_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "display_name",
            "status",
            "note",
            "submitted_at",
            "reviewed_at",
        ]

    def validate_student_id(self, value):
        if not value.isascii() or not value.isdigit() or not 8 <= len(value) <= 12:
            raise serializers.ValidationError("学号应为 8–12 位数字。")
        return value

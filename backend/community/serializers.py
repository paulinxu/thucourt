from accounts.serializers import PublicUserSerializer
from rest_framework import serializers

from .models import Friendship, Message, Notification, TennisFeedback

STROKES = ["forehand", "backhand", "serve", "slice", "volley", "movement"]


class FriendshipSerializer(serializers.ModelSerializer):
    sender = PublicUserSerializer(read_only=True)
    recipient = PublicUserSerializer(read_only=True)

    class Meta:
        model = Friendship
        fields = ["id", "sender", "recipient", "status", "created_at"]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "sender", "recipient", "body", "client_id", "read_at", "created_at"]
        read_only_fields = ["id", "sender", "recipient", "read_at", "created_at"]


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = TennisFeedback
        # Intentionally exclude author and target: received feedback is target-only.
        fields = ["id", "comment", "strokes", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_strokes(self, value):
        if not isinstance(value, dict) or not value or set(value) - set(STROKES):
            raise serializers.ValidationError("请选择正手、反手、发球、切削、截击或移动。")
        if any(type(v) is not int or not 1 <= v <= 5 for v in value.values()):
            raise serializers.ValidationError("各项技术评分应为 1–5 的整数。")
        return value


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "kind", "text", "object_id", "read", "created_at"]

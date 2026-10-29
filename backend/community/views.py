from accounts.models import User
from accounts.serializers import PublicUserSerializer
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import BehaviorRating, Block, Friendship, Message, Notification, TennisFeedback
from .serializers import (
    FeedbackSerializer,
    FriendshipSerializer,
    MessageSerializer,
    NotificationSerializer,
)
from .services import check_block, check_friend, get_peer, pair_key


class FriendsView(APIView):
    serializer_class = FriendshipSerializer

    def get(self, request):
        qs = (
            Friendship.objects.filter(Q(sender=request.user) | Q(recipient=request.user))
            .exclude(status="declined")
            .select_related("sender", "recipient")
            .order_by("-id")
        )
        return Response(FriendshipSerializer(qs, many=True).data)

    @transaction.atomic
    def post(self, request):
        peer = get_peer(request.user, request.data.get("target"))
        check_block(request.user, peer)
        # Lock both users in stable order, also serializes opposite-direction requests.
        list(
            User.objects.select_for_update()
            .filter(pk__in=[request.user.pk, peer.pk])
            .order_by("pk")
        )
        item, created = Friendship.objects.get_or_create(
            pair_key=pair_key(request.user.pk, peer.pk),
            defaults={"sender": request.user, "recipient": peer},
        )
        if not created:
            if item.status != "declined":
                raise ValidationError("已是好友或存在待处理的申请。")
            item.sender, item.recipient, item.status = request.user, peer, "pending"
            item.save()
        Notification.objects.create(
            user=peer,
            kind="friend",
            text=f"{request.user.display_name} 请求成为好友",
            object_id=item.pk,
        )
        return Response(FriendshipSerializer(item).data, status=201)


class FriendDetailView(APIView):
    @transaction.atomic
    def post(self, request, pk):
        item = get_object_or_404(
            Friendship.objects.select_for_update(), pk=pk, recipient=request.user
        )
        if item.status != "pending":
            raise ValidationError("此申请已处理。")
        state = request.data.get("decision")
        if state not in {"accepted", "declined"}:
            raise ValidationError("请选择接受或拒绝。")
        check_block(request.user, item.sender)
        item.status = state
        item.save(update_fields=["status"])
        Notification.objects.create(
            user=item.sender,
            kind="friend",
            text=f"{request.user.display_name} 已处理好友申请",
            object_id=item.pk,
        )
        return Response(FriendshipSerializer(item).data)

    def delete(self, request, pk):
        item = get_object_or_404(
            Friendship.objects.filter(Q(sender=request.user) | Q(recipient=request.user)), pk=pk
        )
        item.delete()
        return Response(status=204)


class BlockView(APIView):
    def get(self, request):
        users = User.objects.filter(blocked_by__owner=request.user)
        return Response(PublicUserSerializer(users, many=True).data)

    def post(self, request):
        peer = get_peer(request.user, request.data.get("target"))
        Block.objects.get_or_create(owner=request.user, target=peer)
        return Response({"ok": True})

    def delete(self, request, pk):
        Block.objects.filter(owner=request.user, target_id=pk).delete()
        return Response(status=204)


class ConversationsView(APIView):
    def get(self, request):
        # Latest message per peer, bounded by distinct peers, not a global message slice.
        messages = (
            Message.objects.filter(Q(sender=request.user) | Q(recipient=request.user))
            .select_related("sender", "recipient")
            .order_by("-id")
        )
        seen, result = set(), []
        for msg in messages.iterator(chunk_size=200):
            peer = msg.recipient if msg.sender_id == request.user.pk else msg.sender
            if peer.pk in seen:
                continue
            seen.add(peer.pk)
            result.append(
                {
                    "peer": PublicUserSerializer(peer).data,
                    "last_message": MessageSerializer(msg).data,
                    "unread": Message.objects.filter(
                        sender=peer, recipient=request.user, read_at=None
                    ).count(),
                }
            )
            if len(result) >= 100:
                break
        return Response(result)


class MessageView(APIView):
    serializer_class = MessageSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "messages"

    def get(self, request, pk):
        peer = get_peer(request.user, pk)
        qs = Message.objects.filter(
            Q(sender=request.user, recipient=peer) | Q(sender=peer, recipient=request.user)
        )
        after = request.query_params.get("after")
        if after is not None:
            if not after.isdigit():
                raise ValidationError("after 必须是消息编号。")
            rows = list(qs.filter(id__gt=int(after)).order_by("id")[:100])
        else:
            rows = list(reversed(list(qs.order_by("-id")[:100])))
        return Response(
            {
                "messages": MessageSerializer(rows, many=True).data,
                "next_after": rows[-1].pk if rows else int(after or 0),
            }
        )

    def post(self, request, pk):
        peer = get_peer(request.user, pk)
        check_block(request.user, peer)
        data = MessageSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                msg, created = Message.objects.get_or_create(
                    sender=request.user,
                    client_id=data.validated_data["client_id"],
                    defaults={"recipient": peer, "body": data.validated_data["body"]},
                )
        except IntegrityError:
            msg = Message.objects.get(
                sender=request.user, client_id=data.validated_data["client_id"]
            )
            created = False
        if msg.recipient_id != peer.pk or msg.body != data.validated_data["body"]:
            raise ValidationError("请求编号已被其他消息使用。")
        return Response(MessageSerializer(msg).data, status=201 if created else 200)


class MessageReadView(APIView):
    def post(self, request, pk):
        class ReadInput(serializers.Serializer):
            through = serializers.IntegerField(min_value=1)

        data = ReadInput(data=request.data)
        data.is_valid(raise_exception=True)
        Message.objects.filter(
            sender_id=pk,
            recipient=request.user,
            read_at=None,
            id__lte=data.validated_data["through"],
        ).update(read_at=timezone.now())
        return Response({"ok": True})


class BehaviorView(APIView):
    def get(self, request, pk):
        peer = get_peer(request.user, pk)
        check_friend(request.user, peer)
        own = BehaviorRating.objects.filter(author=request.user, target=peer).first()
        return Response({"stars": own.stars if own else None})

    def post(self, request, pk):
        peer = get_peer(request.user, pk)
        check_friend(request.user, peer)
        stars = request.data.get("stars")
        if type(stars) is not int or not 1 <= stars <= 5:
            raise ValidationError("行为评分应为 1–5 的整数。")
        BehaviorRating.objects.update_or_create(
            author=request.user, target=peer, defaults={"stars": stars}
        )
        return Response({"ok": True})


class FeedbackView(generics.ListAPIView):
    serializer_class = FeedbackSerializer

    def get_queryset(self):
        return TennisFeedback.objects.filter(target=self.request.user)

    def post(self, request):
        peer = get_peer(request.user, request.data.get("target"))
        check_friend(request.user, peer)
        data = FeedbackSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        data.save(author=request.user, target=peer)
        return Response({"ok": True}, status=201)


class NotificationsView(APIView):
    serializer_class = NotificationSerializer

    def get(self, request):
        qs = Notification.objects.filter(user=request.user)
        return Response(
            {
                "items": NotificationSerializer(qs[:50], many=True).data,
                "unread": qs.filter(read=False).count(),
                "unread_messages": Message.objects.filter(
                    recipient=request.user, read_at=None
                ).count(),
            }
        )

    def post(self, request):
        Notification.objects.filter(user=request.user, read=False).update(read=True)
        return Response({"ok": True})

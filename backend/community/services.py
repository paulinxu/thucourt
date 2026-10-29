from accounts.models import User
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Block, Friendship


def pair_key(a, b):
    return ":".join(map(str, sorted([a, b])))


def get_peer(user, peer_id):
    if isinstance(peer_id, bool) or not str(peer_id).isdigit():
        raise ValidationError("请选择有效的球友。")
    try:
        peer = User.objects.get(pk=int(peer_id), verification="approved", is_active=True)
    except User.DoesNotExist as exc:
        raise ValidationError("球友不存在或尚未认证。") from exc
    if peer.pk == user.pk:
        raise ValidationError("请选择其他球友。")
    return peer


def check_block(user, peer):
    if Block.objects.filter(Q(owner=user, target=peer) | Q(owner=peer, target=user)).exists():
        raise PermissionDenied("当前无法联系此球友。")


def check_friend(user, peer):
    check_block(user, peer)
    if not Friendship.objects.filter(
        pair_key=pair_key(user.pk, peer.pk), status="accepted"
    ).exists():
        raise PermissionDenied("只有好友可以提交评价。")

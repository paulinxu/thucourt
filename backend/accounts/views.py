import secrets
import time
from urllib.parse import urlencode

import httpx
from common.errors import ServiceUnavailable
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import generics, serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import User, VerificationRequest
from .serializers import (
    MeSerializer,
    ProfileUpdateSerializer,
    PublicUserSerializer,
    VerificationSerializer,
)
from .services import review_verification


class SessionView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "user": MeSerializer(request.user).data if request.user.is_authenticated else None,
                "csrf_token": get_token(request),
                "demo_mode": settings.DEMO_MODE,
                "wechat_enabled": bool(settings.WECHAT_APP_ID and settings.WECHAT_APP_SECRET),
                "ai_provider": settings.AI_PROVIDER,
                "ai_processor": settings.AI_PROCESSOR_LABEL,
            }
        )


class LoginInput(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, trim_whitespace=False)


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"
    serializer_class = LoginInput

    def post(self, request):
        if not settings.DEMO_MODE:
            raise PermissionDenied("演示登录已关闭，请使用微信登录。")
        data = LoginInput(data=request.data)
        data.is_valid(raise_exception=True)
        user = authenticate(request, **data.validated_data)
        if user is None:
            raise ValidationError("用户名或密码错误。")
        login(request, user)
        return Response(MeSerializer(user).data)


@method_decorator(csrf_protect, name="dispatch")
class RegisterView(LoginView):
    def post(self, request):
        if not settings.DEMO_MODE:
            raise PermissionDenied("仅演示环境允许本地注册。")
        data = LoginInput(data=request.data)
        data.is_valid(raise_exception=True)
        user = User(
            username=data.validated_data["username"], display_name=data.validated_data["username"]
        )
        try:
            user.full_clean(exclude=["password"])
            validate_password(data.validated_data["password"], user)
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages) from exc
        user.set_password(data.validated_data["password"])
        try:
            user.save()
        except IntegrityError as exc:
            raise ValidationError("用户名已存在。") from exc
        login(request, user)
        return Response(MeSerializer(user).data, status=201)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"ok": True})


class MeView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileUpdateSerializer

    def get(self, request):
        return Response(MeSerializer(request.user).data)

    def patch(self, request):
        data = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        data.is_valid(raise_exception=True)
        data.save()
        return Response(MeSerializer(request.user).data)


class VerificationView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VerificationSerializer

    def get(self, request):
        item = VerificationRequest.objects.filter(user=request.user).first()
        return Response(VerificationSerializer(item).data if item else None)

    @transaction.atomic
    def post(self, request):
        user = User.objects.select_for_update().get(pk=request.user.pk)
        if user.verification in {"approved", "pending"}:
            raise ValidationError("已有已认证或待审核的申请。")
        data = VerificationSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        item, _ = VerificationRequest.objects.update_or_create(
            user=user,
            defaults={
                **data.validated_data,
                "status": "pending",
                "note": "",
                "reviewer": None,
                "reviewed_at": None,
            },
        )
        user.verification = "pending"
        user.save(update_fields=["verification"])
        return Response(VerificationSerializer(item).data, status=201)


class ReviewListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = VerificationSerializer
    queryset = (
        VerificationRequest.objects.filter(status="pending")
        .select_related("user")
        .order_by("submitted_at")
    )


class ReviewView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        get_object_or_404(VerificationRequest, pk=pk)
        if len(str(request.data.get("note", ""))) > 300:
            raise ValidationError("审核说明不能超过 300 字。")
        item = review_verification(
            pk, request.user, request.data.get("decision"), str(request.data.get("note", ""))
        )
        return Response(VerificationSerializer(item).data)


class PlayerListView(generics.ListAPIView):
    serializer_class = PublicUserSerializer

    def get_queryset(self):
        qs = User.objects.filter(verification="approved", is_active=True)
        if self.request.query_params.get("q"):
            qs = qs.filter(display_name__icontains=self.request.query_params["q"][:40])
        track = self.request.query_params.get("track", "singles")
        if track not in {"singles", "doubles"}:
            raise ValidationError("排行榜类型无效。")
        return qs.order_by(f"-{track}_rating", "id")


class PlayerDetailView(generics.RetrieveAPIView):
    serializer_class = PublicUserSerializer
    queryset = User.objects.filter(verification="approved", is_active=True)


class WechatStartView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if (
            not settings.WECHAT_APP_ID
            or not settings.WECHAT_APP_SECRET
            or not settings.WECHAT_REDIRECT_URI
        ):
            raise ServiceUnavailable("尚未配置微信开放平台网站登录。")
        state = secrets.token_urlsafe(32)
        request.session["wechat_state"] = {"value": state, "at": time.time()}
        query = urlencode(
            {
                "appid": settings.WECHAT_APP_ID,
                "redirect_uri": settings.WECHAT_REDIRECT_URI,
                "response_type": "code",
                "scope": "snsapi_login",
                "state": state,
            }
        )
        return HttpResponseRedirect(
            "https://open.weixin.qq.com/connect/qrconnect?" + query + "#wechat_redirect"
        )


class WechatCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        expected = request.session.pop("wechat_state", None)
        if (
            not expected
            or time.time() - expected["at"] > 600
            or not secrets.compare_digest(expected["value"], request.query_params.get("state", ""))
        ):
            raise ValidationError("微信登录状态已过期，请重新登录。")
        code = request.query_params.get("code")
        if not code:
            raise ValidationError("微信未返回授权码。")
        try:
            response = httpx.get(
                "https://api.weixin.qq.com/sns/oauth2/access_token",
                params={
                    "appid": settings.WECHAT_APP_ID,
                    "secret": settings.WECHAT_APP_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                },
                timeout=15,
            )
            response.raise_for_status()
            payload = response.json()
            openid = payload.get("openid")
            if not isinstance(openid, str) or not openid or payload.get("errcode"):
                raise ValueError("invalid exchange")
        except (httpx.HTTPError, ValueError) as exc:
            raise ServiceUnavailable("微信授权失败，请重新尝试。") from exc
        with transaction.atomic():
            user, created = User.objects.get_or_create(
                wechat_id=openid,
                defaults={"username": "wx_" + secrets.token_hex(16), "display_name": "新球友"},
            )
            if created:
                user.set_unusable_password()
                user.save(update_fields=["password"])
        if not user.is_active:
            raise PermissionDenied("账号已停用。")
        login(request, user)
        return HttpResponseRedirect("/profile")

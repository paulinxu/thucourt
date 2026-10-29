from accounts import views as accounts
from coaching import views as coaching
from community import views as community
from courts.views import ConfigurationView, PostingViewSet
from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from matches.views import MatchViewSet
from rest_framework.permissions import IsAdminUser
from rest_framework.routers import DefaultRouter


def health(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return JsonResponse({"status": "ok", "service": "thucourt"})


router = DefaultRouter()
router.register("postings", PostingViewSet, basename="posting")
router.register("matches", MatchViewSet, basename="match")
router.register("coach/media", coaching.MediaViewSet, basename="media")
router.register("coach/sessions", coaching.SessionViewSet, basename="coach-session")
router.register("coach/turns", coaching.TurnViewSet, basename="coach-turn")
router.register("coach/plans", coaching.PlanViewSet, basename="plan")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path(
        "api/schema/", SpectacularAPIView.as_view(permission_classes=[IsAdminUser]), name="schema"
    ),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema", permission_classes=[IsAdminUser]),
        name="swagger-ui",
    ),
    path("api/auth/session/", accounts.SessionView.as_view()),
    path("api/auth/login/", accounts.LoginView.as_view()),
    path("api/auth/register/", accounts.RegisterView.as_view()),
    path("api/auth/logout/", accounts.LogoutView.as_view()),
    path("api/auth/wechat/start/", accounts.WechatStartView.as_view()),
    path("api/auth/wechat/callback/", accounts.WechatCallbackView.as_view()),
    path("api/me/", accounts.MeView.as_view()),
    path("api/me/verification/", accounts.VerificationView.as_view()),
    path("api/reviews/", accounts.ReviewListView.as_view()),
    path("api/reviews/<int:pk>/", accounts.ReviewView.as_view()),
    path("api/players/", accounts.PlayerListView.as_view()),
    path("api/players/<int:pk>/", accounts.PlayerDetailView.as_view()),
    path("api/config/", ConfigurationView.as_view()),
    path("api/friends/", community.FriendsView.as_view()),
    path("api/friends/<int:pk>/", community.FriendDetailView.as_view()),
    path("api/blocks/", community.BlockView.as_view()),
    path("api/blocks/<int:pk>/", community.BlockView.as_view()),
    path("api/conversations/", community.ConversationsView.as_view()),
    path("api/messages/<int:pk>/", community.MessageView.as_view()),
    path("api/messages/<int:pk>/read/", community.MessageReadView.as_view()),
    path("api/behavior/<int:pk>/", community.BehaviorView.as_view()),
    path("api/feedback/", community.FeedbackView.as_view()),
    path("api/notifications/", community.NotificationsView.as_view()),
    path("api/", include(router.urls)),
]

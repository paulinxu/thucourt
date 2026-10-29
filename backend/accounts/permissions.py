from rest_framework.permissions import BasePermission


class IsVerified(BasePermission):
    message = "请先登录并完成管理员的学生身份审核。"

    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and request.user.is_active
            and request.user.verification == "approved"
        )

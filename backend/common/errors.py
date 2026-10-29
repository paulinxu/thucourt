from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler as drf_exception_handler


class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = "服务暂时不可用，请稍后重试。"


def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is not None:
        response.data = {"error": response.data}
    return response

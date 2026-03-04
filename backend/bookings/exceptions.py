"""
統一例外處理模組 (Custom Exception Handler)。
將 DRF 及 Django 的例外統一轉換為標準化的 JSON error 結構，
讓前端可以用一致的格式來解析所有 API 的錯誤回應。
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError


def custom_exception_handler(exc, context):
    """
    自訂的例外處理函數，取代 DRF 預設的 exception_handler。
    會將所有錯誤包裝成以下統一格式：
    {
        "error": {
            "code": "錯誤代碼 (如 VALIDATION_ERROR)",
            "message": "錯誤訊息摘要",
            "details": { ... 詳細欄位錯誤 }
        }
    }
    """
    # 先呼叫 DRF 預設的 exception_handler，取得它原本會回傳的 Response
    response = exception_handler(exc, context)

    if response is not None:
        # DRF 能處理的例外 (例如 PermissionDenied, NotFound, ValidationError 等)
        # 根據 HTTP 狀態碼，對應到我們自訂的錯誤代碼
        if response.status_code == 403:
            code = "FORBIDDEN"
        elif response.status_code == 404:
            code = "NOT_FOUND"
        elif response.status_code == 400:
            code = "VALIDATION_ERROR"
        elif response.status_code == 401:
            code = "UNAUTHORIZED"
        else:
            code = "ERROR"

        # 重新包裝成統一的 JSON 結構
        custom_response_data = {
            "error": {
                "code": code,
                "message": str(exc),
                "details": response.data if isinstance(response.data, dict) else {"detail": response.data}
            }
        }
        response.data = custom_response_data

    elif isinstance(exc, DjangoValidationError):
        # Django 原生的 ValidationError (非 DRF 的)，通常由 model.clean() 或 full_clean() 拋出
        # DRF 預設的 handler 不會處理它，所以我們要自己接住並回傳 400
        return Response({
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation failed",
                "details": exc.message_dict if hasattr(exc, 'message_dict') else {"non_field_errors": list(exc)}
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    return response

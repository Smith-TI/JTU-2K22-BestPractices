from rest_framework.exceptions import APIException


class UnauthorizedUserException(APIException):
    """Raised when user is unauthorized"""
    status_code: int = 404
    default_detail: str = "Not Found"
    default_code: str = "Records unavailable"

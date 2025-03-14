from rest_framework.exceptions import APIException, ErrorDetail
from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.response import Response

##############################################################
                        # Error Classes
##############################################################


class PaymentRequiredError(APIException):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = 'Purchase a reqeust or request pack to send or receive request.'
    default_code = 'user'
    def __init__(self, detail, code=default_code):
        # Wrap messages in ErrorDetail
        if isinstance(detail, dict):
            for key in detail:
                detail[key] = [ErrorDetail(detail[key], code)]
        self.detail = detail
        self.code = code
        super().__init__(detail=detail, code=code)

# ==============================================================

class ConflictError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'The request already processed.'
    default_code = 'user'
    def __init__(self, detail, code=default_code):
        # Wrap messages in ErrorDetail
        if isinstance(detail, dict):
            for key in detail:
                detail[key] = [ErrorDetail(detail[key], code)]
        self.detail = detail
        self.code = code
        super().__init__(detail=detail, code=code)

# ==============================================================

class TooManyRequests(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "Too many requests. Please wait before trying again."
    default_code = 'user'
    def __init__(self, detail, code=default_code):
        # Wrap messages in ErrorDetail
        if isinstance(detail, dict):
            for key in detail:
                detail[key] = [ErrorDetail(detail[key], code)]
        self.detail = detail
        self.code = code
        super().__init__(detail=detail, code=code)

# ==============================================================

class NotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Resource not found.'
    default_code = 'not_found'
    def __init__(self, detail, code=default_code):
        # Wrap messages in ErrorDetail
        if isinstance(detail, dict):
            for key in detail:
                detail[key] = [ErrorDetail(detail[key], code)]
        self.detail = detail
        self.code = code
        super().__init__(detail=detail, code=code)


# ==============================================================

class ServerError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Internal server error.'
    default_code = 'backend'
    def __init__(self, detail, code=default_code):
        # Wrap messages in ErrorDetail
        if isinstance(detail, dict):
            for key in detail:
                detail[key] = [ErrorDetail(detail[key], code)]
        self.detail = detail
        self.code = code
        super().__init__(detail=detail, code=code)



##############################################################
                        # Success Response
##############################################################


def success_ok(message="Request processed successfully.", data=None):
    return Response({
        "success": True,
        "message": message, 
        "data": data}, 
        status=status.HTTP_200_OK)

# ==============================================================

def success_created(message="Resource created successfully.", data=None):
    return Response({
        "success": True,
        "message": message, 
        "data": data}, 
        status=status.HTTP_201_CREATED)

# ==============================================================

def already_accepted(message="Your request has been accepted and is being processed."):
    return Response({
        "success": True,
        "message": message, 
        "data": None}, 
        status=status.HTTP_202_ACCEPTED)
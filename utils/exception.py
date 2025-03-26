from rest_framework.views import exception_handler
from rest_framework.exceptions import ErrorDetail

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        if response.data.get("detail"):
            response.data["message"] = response.data['detail']
            response.data.pop("detail")
        custom_response = {
            'success': False,
            'status_code': response.status_code,
            'type': get_error_type(response.data),
            'error': response.data if isinstance(response.data, dict) else {"message": response.data}
        }
        response.data = custom_response
    return response



def get_error_type(response_data):
    for field, error in response_data.items():
        # for error in error:
        if isinstance(error[0], ErrorDetail) and error[0].code in ['required', 'frontend']:  # Ensure it's an ErrorDetail object
            return "frontend"
        if isinstance(error[0], ErrorDetail) and error[0].code in ['backend']:
            return "backend"
    return "user"
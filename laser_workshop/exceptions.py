"""
Custom exception handler for Django REST Framework.
Standardizes error responses across all API endpoints.
"""
from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    """
    Custom exception handler that standardizes error responses.
    
    Returns a consistent format:
    {
        "message": "User-friendly error message",
        "detail": "Technical details (optional)",
        "errors": {}  // Field-level errors for validation
    }
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Initialize custom response data
        custom_response = {}
        
        # Handle validation errors specially
        if isinstance(exc, ValidationError):
            errors = response.data
            
            # Build a user-friendly message from validation errors
            if isinstance(errors, dict):
                # Field-specific errors
                error_messages = []
                for field, messages in errors.items():
                    if isinstance(messages, list):
                        field_errors = '. '.join(str(msg) for msg in messages)
                    else:
                        field_errors = str(messages)
                    
                    if field == 'non_field_errors':
                        error_messages.append(field_errors)
                    else:
                        error_messages.append(f"{field}: {field_errors}")
                
                custom_response['message'] = '. '.join(error_messages)
                custom_response['errors'] = errors
            elif isinstance(errors, list):
                # List of error messages
                custom_response['message'] = '. '.join(str(msg) for msg in errors)
            else:
                # Single error message
                custom_response['message'] = str(errors)
        else:
            # Non-validation errors (401, 403, 404, etc.)
            error_detail = response.data
            
            # Extract message from different possible formats
            if isinstance(error_detail, dict):
                # Try to get 'detail', 'error', or 'message' field
                message = (
                    error_detail.get('detail') or
                    error_detail.get('error') or
                    error_detail.get('message') or
                    str(error_detail)
                )
            elif isinstance(error_detail, list):
                message = '. '.join(str(msg) for msg in error_detail)
            else:
                message = str(error_detail)
            
            custom_response['message'] = message
            
            # Include original detail if different from message
            if isinstance(error_detail, dict) and error_detail.get('detail'):
                custom_response['detail'] = str(error_detail.get('detail'))
        
        # Replace response data with standardized format
        response.data = custom_response
    
    return response

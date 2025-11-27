class AppException(Exception):
    
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        # Initialize exception with message, status code, and optional details
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppException):
    
    def __init__(self, resource_type: str, resource_id: str = None):
        # Initialize not found error for resource type and optional ID
        message = f"{resource_type} not found"
        if resource_id:
            message += f": {resource_id}"
        super().__init__(message, status_code=404, details={"resource_type": resource_type, "resource_id": resource_id})


class ValidationError(AppException):
    
    def __init__(self, message: str, field: str = None, details: dict = None):
        # Initialize validation error with message, optional field, and details
        error_details = details or {}
        if field:
            error_details["field"] = field
        super().__init__(message, status_code=400, details=error_details)


class AuthenticationError(AppException):
    
    def __init__(self, message: str = "Authentication failed"):
        # Initialize authentication error
        super().__init__(message, status_code=401)


class AuthorizationError(AppException):
    
    def __init__(self, message: str = "Access denied"):
        # Initialize authorization error
        super().__init__(message, status_code=403)


class DatabaseError(AppException):
    
    def __init__(self, message: str, operation: str = None, details: dict = None):
        # Initialize database error with message, optional operation, and details
        error_details = details or {}
        if operation:
            error_details["operation"] = operation
        super().__init__(message, status_code=500, details=error_details)


class ServiceError(AppException):
    
    def __init__(self, message: str, service_name: str = None, details: dict = None):
        # Initialize service error with message, optional service name, and details
        error_details = details or {}
        if service_name:
            error_details["service_name"] = service_name
        super().__init__(message, status_code=502, details=error_details)


class TimeoutError(AppException):
    
    def __init__(self, message: str = "Operation timed out", timeout_seconds: float = None):
        # Initialize timeout error with message and optional timeout duration
        details = {}
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
        super().__init__(message, status_code=504, details=details)

import pytest
from fastapi import HTTPException, status

from app.api.error_handlers import handle_app_exception
from app.core.exceptions import (
    AppException,
    NotFoundError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    ServiceError,
    TimeoutError as AppTimeoutError
)


class TestErrorHandlers:
    
    def test_handle_not_found_error(self):
        error = NotFoundError("Resource not found")
        result = handle_app_exception(error)
        
        assert isinstance(result, HTTPException)
        assert result.status_code == status.HTTP_404_NOT_FOUND
        assert "Resource not found" in str(result.detail)
    
    def test_handle_validation_error(self):
        error = ValidationError("Invalid input", field="email")
        result = handle_app_exception(error)
        
        assert isinstance(result, HTTPException)
        assert result.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid input" in result.detail
    
    def test_handle_authentication_error(self):
        error = AuthenticationError("Invalid credentials")
        result = handle_app_exception(error)
        
        assert isinstance(result, HTTPException)
        assert result.status_code == status.HTTP_401_UNAUTHORIZED
        assert result.detail == "Invalid credentials"
    
    def test_handle_authorization_error(self):
        error = AuthorizationError("Access denied")
        result = handle_app_exception(error)
        
        assert isinstance(result, HTTPException)
        assert result.status_code == status.HTTP_403_FORBIDDEN
        assert result.detail == "Access denied"
    
    def test_handle_database_error(self):
        error = DatabaseError("Database connection failed", operation="find_one")
        result = handle_app_exception(error)
        
        assert isinstance(result, HTTPException)
        assert result.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Database connection failed" in result.detail
    
    def test_handle_service_error(self):
        error = ServiceError("External service failed", service_name="OpenAI")
        result = handle_app_exception(error)
        
        assert isinstance(result, HTTPException)
        assert result.status_code == status.HTTP_502_BAD_GATEWAY
        assert "External service failed" in result.detail
    
    def test_handle_timeout_error(self):
        error = AppTimeoutError("Operation timed out", timeout_seconds=30.0)
        result = handle_app_exception(error)
        
        assert isinstance(result, HTTPException)
        assert result.status_code == status.HTTP_504_GATEWAY_TIMEOUT
        assert "Operation timed out" in result.detail
    
    def test_handle_generic_app_exception(self):
        error = AppException("Generic error", status_code=418)
        result = handle_app_exception(error)
        
        assert isinstance(result, HTTPException)
        assert result.status_code == 418
        assert "Generic error" in str(result.detail)


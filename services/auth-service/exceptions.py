from typing import Any, Dict, Optional
from fastapi import HTTPException, status

class BaseAPIException(HTTPException):
    """Base exception class for API errors"""

    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class InvalidCredentialsException(BaseAPIException):
    """Exception raised when credentials are invalid"""

    def __init__(self, detail: str = "Invalid username or password"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class UserNotFoundException(BaseAPIException):
    """Exception raised when user is not found"""

    def __init__(self, detail: str = "User not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )

class UserAlreadyExistsException(BaseAPIException):
    """Exception raised when trying to create a user that already exists"""

    def __init__(self, detail: str = "User with this email or username already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )

class TenantNotFoundException(BaseAPIException):
    """Exception raised when tenant is not found"""

    def __init__(self, detail: str = "Tenant not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )

class TenantAlreadyExistsException(BaseAPIException):
    """Exception raised when trying to create a tenant that already exists"""

    def __init__(self, detail: str = "Tenant with this slug already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )

class PermissionDeniedException(BaseAPIException):
    """Exception raised when user doesn't have required permissions"""

    def __init__(self, detail: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

class TokenExpiredException(BaseAPIException):
    """Exception raised when token has expired"""

    def __init__(self, detail: str = "Token has expired"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class InvalidTokenException(BaseAPIException):
    """Exception raised when token is invalid"""

    def __init__(self, detail: str = "Invalid token"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class RefreshTokenException(BaseAPIException):
    """Exception raised when refresh token is invalid or expired"""

    def __init__(self, detail: str = "Invalid or expired refresh token"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )

class AccountLockedException(BaseAPIException):
    """Exception raised when account is locked due to too many failed attempts"""

    def __init__(self, detail: str = "Account is locked due to too many failed login attempts"):
        super().__init__(
            status_code=status.HTTP_423_LOCKED,
            detail=detail
        )

class EmailNotVerifiedException(BaseAPIException):
    """Exception raised when email is not verified"""

    def __init__(self, detail: str = "Email address is not verified"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

class InvalidVerificationTokenException(BaseAPIException):
    """Exception raised when verification token is invalid"""

    def __init__(self, detail: str = "Invalid or expired verification token"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class PasswordResetTokenException(BaseAPIException):
    """Exception raised when password reset token is invalid"""

    def __init__(self, detail: str = "Invalid or expired password reset token"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class WeakPasswordException(BaseAPIException):
    """Exception raised when password doesn't meet requirements"""

    def __init__(self, detail: str = "Password does not meet security requirements"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class TwoFactorRequiredException(BaseAPIException):
    """Exception raised when two-factor authentication is required"""

    def __init__(self, detail: str = "Two-factor authentication required"):
        super().__init__(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail=detail
        )

class InvalidTwoFactorCodeException(BaseAPIException):
    """Exception raised when two-factor code is invalid"""

    def __init__(self, detail: str = "Invalid two-factor authentication code"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class RateLimitExceededException(BaseAPIException):
    """Exception raised when rate limit is exceeded"""

    def __init__(self, detail: str = "Rate limit exceeded. Please try again later"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail
        )

class TenantLimitExceededException(BaseAPIException):
    """Exception raised when tenant limits are exceeded"""

    def __init__(self, detail: str = "Tenant limit exceeded"):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=detail
        )

class InvalidTenantException(BaseAPIException):
    """Exception raised when tenant context is invalid"""

    def __init__(self, detail: str = "Invalid tenant context"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class ServiceUnavailableException(BaseAPIException):
    """Exception raised when a required service is unavailable"""

    def __init__(self, detail: str = "Service temporarily unavailable"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )

class DatabaseException(BaseAPIException):
    """Exception raised when database operation fails"""

    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )

class ValidationException(BaseAPIException):
    """Exception raised when validation fails"""

    def __init__(self, detail: str = "Validation failed"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )

class APIKeyException(BaseAPIException):
    """Exception raised when API key is invalid"""

    def __init__(self, detail: str = "Invalid API key"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "API-Key"}
        )

class SubscriptionExpiredException(BaseAPIException):
    """Exception raised when subscription has expired"""

    def __init__(self, detail: str = "Subscription has expired"):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=detail
        )

class FeatureNotEnabledException(BaseAPIException):
    """Exception raised when trying to access a disabled feature"""

    def __init__(self, detail: str = "This feature is not enabled for your account"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

class MaintenanceModeException(BaseAPIException):
    """Exception raised when system is in maintenance mode"""

    def __init__(self, detail: str = "System is currently under maintenance"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )

# Helper function to handle common database errors
def handle_database_error(error: Exception) -> None:
    """Convert database errors to appropriate HTTP exceptions"""
    error_str = str(error).lower()

    if "duplicate" in error_str or "unique" in error_str:
        if "email" in error_str:
            raise UserAlreadyExistsException("Email address already registered")
        elif "username" in error_str:
            raise UserAlreadyExistsException("Username already taken")
        elif "slug" in error_str:
            raise TenantAlreadyExistsException("Tenant slug already exists")
        else:
            raise ValidationException("Duplicate value error")

    elif "foreign key" in error_str:
        raise ValidationException("Referenced resource does not exist")

    elif "not null" in error_str:
        raise ValidationException("Required field is missing")

    else:
        raise DatabaseException(f"Database error: {error_str}")

# Helper function to validate request data
def validate_request_data(data: Dict[str, Any], required_fields: list) -> None:
    """Validate that required fields are present in request data"""
    missing_fields = []

    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)

    if missing_fields:
        raise ValidationException(f"Missing required fields: {', '.join(missing_fields)}")

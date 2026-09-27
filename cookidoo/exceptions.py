"""Cookidoo SDK Exceptions."""

class CookidooError(Exception):
    """Base exception for Cookidoo SDK errors."""
    pass

class CookidooAuthError(CookidooError):
    """Raised when authentication fails or session has expired."""
    pass

class CookidooNotFoundError(CookidooError):
    """Raised when a requested resource (recipe, day plan) is not found."""
    pass

class CookidooRateLimitError(CookidooError):
    """Raised when Cookidoo rate limits requests (HTTP 429)."""
    pass

class CookidooValidationError(CookidooError):
    """Raised when request payload or parameters fail validation."""
    pass

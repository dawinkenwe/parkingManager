from collections import defaultdict
class CustomError(Exception):
    """Base class for custom errors."""
    def __init__(self, message, status_code=500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ExternalAPIError(CustomError):
    """Error raised for issues with external API."""
    def __init__(self, message='Error with external API', status_code=500):
        super().__init__(message, status_code)


class ResponseParsingError(CustomError):
    """Error raised when parsing API response fails"""
    def __init__(self, message='Error parsing API response', status_code=500):
        super().__init__(message, status_code)


# Define error mappings
ERROR_MAPPING = defaultdict(lambda: (500, 'Encountered an unexpected error'), {
    ExternalAPIError: (500, 'Error communicating with external service')
})
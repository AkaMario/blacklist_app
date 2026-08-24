import uuid
from ..models.errors import BadRequestError


def validate_uuid(uuid_string: str) -> bool:
    """
    Validate if a string is a valid UUID.
    
    Args:
        uuid_string: String to validate
        
    Returns:
        bool: True if valid UUID
        
    Raises:
        BadRequestError: If the UUID is invalid
    """
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        raise BadRequestError(f"Invalid UUID format: {uuid_string}")


def get_client_ip(request) -> str:
    """
    Get the client IP address from the request.
    Handles X-Forwarded-For header for load balancers like Elastic Beanstalk.
    
    Args:
        request: Flask request object
        
    Returns:
        str: Client IP address
    """
    # Check for X-Forwarded-For header (set by load balancers)
    forwarded_for = request.headers.get('X-Forwarded-For')
    
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs (client, proxy1, proxy2, ...)
        # The first IP is the original client
        return forwarded_for.split(',')[0].strip()
    
    # Fallback to direct connection IP
    return request.remote_addr or 'unknown'


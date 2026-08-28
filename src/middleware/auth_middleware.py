import os
from functools import wraps
from flask import request, jsonify
from ..models.errors import UnauthorizedError


def require_bearer_token(f):
    """
    Decorator to require a valid Bearer token for API endpoints.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get the authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                "error": "Unauthorized",
                "message": "Authorization header is missing"
            }), 401
        
        # Check if it's a Bearer token
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({
                "error": "Unauthorized",
                "message": "Invalid authorization header format. Expected: Bearer <token>"
            }), 401
        
        token = parts[1]
        expected_token = os.environ.get('BEARER_TOKEN')
        
        if not expected_token:
            return jsonify({
                "error": "Internal Server Error",
                "message": "BEARER_TOKEN environment variable is not configured"
            }), 500
        
        # Validate the token
        if token != expected_token:
            return jsonify({
                "error": "Unauthorized",
                "message": "Invalid bearer token"
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


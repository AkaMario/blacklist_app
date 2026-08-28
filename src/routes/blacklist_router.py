from flask import Blueprint, request, jsonify
from marshmallow import ValidationError

from ..models.blacklist import (
    BlacklistCreateSchema,
    BlacklistCheckResponseSchema
)
from ..models.errors import BadRequestError, ConflictError, NotFoundError
from ..services.blacklist_service import BlacklistService
from ..middleware.auth_middleware import require_bearer_token
from ..utils.validation import get_client_ip

# Create Blueprint
blacklist_bp = Blueprint('blacklist', __name__, url_prefix='/blacklists')

# Initialize schemas
create_schema = BlacklistCreateSchema()
check_schema = BlacklistCheckResponseSchema()

# Service instance
blacklist_service = BlacklistService()


@blacklist_bp.route('', methods=['POST'])
@require_bearer_token
def create_blacklist():
    """
    Create a new blacklist entry.
    
    POST /blacklists
    
    Request body:
    {
        "email": "user@example.com",
        "app_uuid": "123e4567-e89b-12d3-a456-426614174000",
        "blocked_reason": "Spam activity detected"  # Optional
    }
    
    Returns:
    - 201: Blacklist entry created successfully
    - 400: Invalid request data
    - 401: Unauthorized
    - 409: Email already in blacklist
    """
    try:
        # Get and validate request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "Bad Request",
                "message": "Request body is required"
            }), 400
        
        # Validate with Marshmallow schema
        validated_data = create_schema.load(data)
        
        # Get client IP address
        ip_address = get_client_ip(request)
        
        # Add to blacklist
        result = blacklist_service.add_to_blacklist(
            email=validated_data['email'],
            app_uuid=validated_data['app_uuid'],
            blocked_reason=validated_data.get('blocked_reason'),
            ip_address=ip_address
        )
        
        return jsonify(result), 201
        
    except ValidationError as e:
        return jsonify({
            "error": "Bad Request",
            "message": "Validation failed",
            "details": e.messages
        }), 400
    except ConflictError as e:
        return jsonify({
            "error": "Conflict",
            "message": str(e)
        }), 409
    except Exception as e:
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500


@blacklist_bp.route('/<string:email>', methods=['GET'])
@require_bearer_token
def check_blacklist(email):
    """
    Check if an email is in the blacklist.
    
    GET /blacklists/<email>
    
    Returns:
    - 200: Email blacklist status
    - 401: Unauthorized
    """
    try:
        # Check blacklist
        result = blacklist_service.check_blacklist(email)
        
        # Validate response with schema
        validated_result = check_schema.dump(result)
        
        return jsonify(validated_result), 200
        
    except Exception as e:
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500


@blacklist_bp.route('/ping', methods=['GET'])
def ping():
    """
    Health check endpoint.
    
    GET /blacklists/ping
    
    Returns:
    - 200: Service is healthy
    """
    return jsonify({"message": "pong"}), 200


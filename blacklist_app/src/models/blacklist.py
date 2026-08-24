from marshmallow import Schema, fields, validate, ValidationError
import uuid as uuid_module


def validate_uuid_format(value):
    """Validate that a string is a valid UUID format"""
    try:
        uuid_module.UUID(value)
    except (ValueError, AttributeError, TypeError):
        raise ValidationError('Not a valid UUID format.')


class BlacklistCreateSchema(Schema):
    """
    Schema for creating a blacklist entry.
    """
    email = fields.Email(required=True, error_messages={
        "required": "Email is required",
        "invalid": "Invalid email format"
    })
    app_uuid = fields.String(
        required=True, 
        validate=validate_uuid_format,
        error_messages={
            "required": "App UUID is required"
        }
    )
    blocked_reason = fields.String(
        required=False, 
        allow_none=True,
        validate=validate.Length(max=255),
        error_messages={
            "invalid": "Blocked reason must be a string",
        }
    )


class BlacklistResponseSchema(Schema):
    """
    Schema for blacklist response.
    """
    id = fields.String(required=True)
    email = fields.Email(required=True)
    app_uuid = fields.String(required=True)
    blocked_reason = fields.String(allow_none=True)
    ip_address = fields.String(required=True)
    created_at = fields.DateTime(required=True)


class BlacklistCheckResponseSchema(Schema):
    """
    Schema for checking if an email is blacklisted.
    """
    is_blacklisted = fields.Boolean(required=True)
    email = fields.Email(required=True)
    blocked_reason = fields.String(allow_none=True)


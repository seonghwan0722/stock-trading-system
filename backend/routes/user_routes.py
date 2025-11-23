"""
User Management API Routes
Secure user registration, settings, and profile management
"""
from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields, validate, ValidationError
from backend.auth import token_required, get_auth_manager
from backend.database.mongo_db import get_user_manager
from cryptography.fernet import Fernet
import os
import base64
import logging

# Setup logger
logger = logging.getLogger(__name__)

# Create Blueprint
user_bp = Blueprint('user', __name__, url_prefix='/api/user')

# Get managers
auth_manager = get_auth_manager()
user_manager = get_user_manager()


# Validation Schemas
class RegisterSchema(Schema):
    """User registration validation"""
    username = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=50),
            validate.Regexp(r'^[a-zA-Z0-9_]+$', error='Username can only contain letters, numbers, and underscores')
        ]
    )
    password = fields.Str(
        required=True,
        validate=validate.Length(min=8, max=128, error='Password must be between 8-128 characters')
    )
    email = fields.Email(required=False, allow_none=True)
    full_name = fields.Str(required=False, validate=validate.Length(max=100))


class LoginSchema(Schema):
    """Login validation"""
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    password = fields.Str(required=True)


class UserSettingsSchema(Schema):
    """User settings validation"""
    # Investment profile
    investment_style = fields.Str(
        required=False,
        validate=validate.OneOf(['conservative', 'moderate', 'aggressive'])
    )
    risk_tolerance = fields.Int(required=False, validate=validate.Range(min=1, max=10))
    max_position_size = fields.Int(required=False, validate=validate.Range(min=0))
    max_positions = fields.Int(required=False, validate=validate.Range(min=1, max=50))

    # API Keys (will be encrypted before storage)
    telegram_bot_token = fields.Str(required=False, allow_none=True)
    telegram_chat_id = fields.Str(required=False, allow_none=True)

    # Notification preferences
    enable_telegram_notifications = fields.Bool(required=False)
    enable_trade_alerts = fields.Bool(required=False)
    enable_monthly_reports = fields.Bool(required=False)


# Encryption for sensitive data
def get_encryption_key():
    """Get or create encryption key for sensitive data"""
    key_file = 'config/.encryption_key'

    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        os.makedirs('config', exist_ok=True)
        with open(key_file, 'wb') as f:
            f.write(key)
        os.chmod(key_file, 0o600)  # Owner read/write only
        return key


ENCRYPTION_KEY = get_encryption_key()
cipher = Fernet(ENCRYPTION_KEY)


def encrypt_value(value: str) -> str:
    """Encrypt sensitive value"""
    if not value:
        return None
    return cipher.encrypt(value.encode()).decode()


def decrypt_value(encrypted: str) -> str:
    """Decrypt sensitive value"""
    if not encrypted:
        return None
    return cipher.decrypt(encrypted.encode()).decode()


# Routes
@user_bp.route('/register', methods=['POST'])
def register():
    """
    User registration endpoint

    Request body:
        {
            "username": "string",
            "password": "string",
            "email": "string (optional)",
            "full_name": "string (optional)"
        }

    Returns:
        {
            "success": true,
            "user": {...},
            "access_token": "string",
            "refresh_token": "string"
        }
    """
    try:
        # Validate request
        schema = RegisterSchema()
        data = schema.load(request.json)
        logger.info(f"Registration attempt for username: {data.get('username')}")

        # Validate password strength
        password = data['password']
        if not any(c.isupper() for c in password):
            return jsonify({
                'success': False,
                'error': 'Password must contain at least one uppercase letter'
            }), 400

        if not any(c.islower() for c in password):
            return jsonify({
                'success': False,
                'error': 'Password must contain at least one lowercase letter'
            }), 400

        if not any(c.isdigit() for c in password):
            return jsonify({
                'success': False,
                'error': 'Password must contain at least one digit'
            }), 400

        # Create user
        result = user_manager.create_user(
            username=data['username'],
            password=data['password'],
            email=data.get('email'),
            full_name=data.get('full_name')
        )

        if not result['success']:
            return jsonify(result), 400

        # Authenticate and return tokens
        auth_result = auth_manager.authenticate(data['username'], data['password'])

        return jsonify(auth_result), 201

    except ValidationError as err:
        return jsonify({'success': False, 'errors': err.messages}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint

    Request body:
        {
            "username": "string",
            "password": "string"
        }

    Returns:
        {
            "success": true,
            "access_token": "string",
            "refresh_token": "string",
            "user": {...}
        }
    """
    try:
        # Validate request
        schema = LoginSchema()
        data = schema.load(request.json)

        # Authenticate
        result = auth_manager.authenticate(data['username'], data['password'])

        if not result['success']:
            return jsonify(result), 401

        return jsonify(result), 200

    except ValidationError as err:
        return jsonify({'success': False, 'errors': err.messages}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """
    Refresh access token using refresh token

    Request body:
        {
            "refresh_token": "string"
        }

    Returns:
        {
            "success": true,
            "access_token": "string"
        }
    """
    try:
        data = request.json
        refresh_token = data.get('refresh_token')

        if not refresh_token:
            return jsonify({'success': False, 'error': 'Refresh token required'}), 400

        result = auth_manager.refresh_access_token(refresh_token)

        if not result['success']:
            return jsonify(result), 401

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """
    Get current user profile

    Headers:
        Authorization: Bearer <access_token>

    Returns:
        {
            "success": true,
            "user": {...}
        }
    """
    try:
        # Get user settings
        settings = user_manager.get_user_settings(current_user['user_id'])

        # Decrypt sensitive fields if they exist
        if settings:
            if settings.get('telegram_bot_token'):
                settings['telegram_bot_token'] = decrypt_value(settings['telegram_bot_token'])
            if settings.get('telegram_chat_id'):
                settings['telegram_chat_id'] = decrypt_value(settings['telegram_chat_id'])

        return jsonify({
            'success': True,
            'user': current_user,
            'settings': settings
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/settings', methods=['PUT'])
@token_required
def update_settings(current_user):
    """
    Update user settings

    Headers:
        Authorization: Bearer <access_token>

    Request body:
        {
            "investment_style": "moderate",
            "risk_tolerance": 5,
            "max_position_size": 1000000,
            "max_positions": 5,
            "telegram_bot_token": "string (optional)",
            "telegram_chat_id": "string (optional)",
            "enable_telegram_notifications": true,
            "enable_trade_alerts": true,
            "enable_monthly_reports": true
        }

    Returns:
        {
            "success": true,
            "message": "Settings updated successfully"
        }
    """
    try:
        # Validate request
        schema = UserSettingsSchema()
        data = schema.load(request.json)

        # Encrypt sensitive fields
        if 'telegram_bot_token' in data and data['telegram_bot_token']:
            data['telegram_bot_token'] = encrypt_value(data['telegram_bot_token'])

        if 'telegram_chat_id' in data and data['telegram_chat_id']:
            data['telegram_chat_id'] = encrypt_value(data['telegram_chat_id'])

        # Update settings
        result = user_manager.update_user_settings(current_user['user_id'], data)

        if not result['success']:
            return jsonify(result), 400

        return jsonify({
            'success': True,
            'message': 'Settings updated successfully'
        }), 200

    except ValidationError as err:
        return jsonify({'success': False, 'errors': err.messages}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/settings', methods=['GET'])
@token_required
def get_settings(current_user):
    """
    Get user settings

    Headers:
        Authorization: Bearer <access_token>

    Returns:
        {
            "success": true,
            "settings": {...}
        }
    """
    try:
        settings = user_manager.get_user_settings(current_user['user_id'])

        # Decrypt sensitive fields (masked for security)
        if settings:
            if settings.get('telegram_bot_token'):
                # Return masked value
                settings['telegram_bot_token_masked'] = '****' + decrypt_value(settings['telegram_bot_token'])[-4:]
                del settings['telegram_bot_token']

            if settings.get('telegram_chat_id'):
                settings['telegram_chat_id_masked'] = '****' + decrypt_value(settings['telegram_chat_id'])[-4:]
                del settings['telegram_chat_id']

        return jsonify({
            'success': True,
            'settings': settings if settings else {}
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    """
    Logout (invalidate session)

    Headers:
        Authorization: Bearer <access_token>

    Returns:
        {
            "success": true,
            "message": "Logged out successfully"
        }
    """
    # In a stateless JWT system, logout is handled client-side by deleting the token
    # For session-based systems, we would delete the session here

    return jsonify({
        'success': True,
        'message': 'Logged out successfully. Please delete your tokens.'
    }), 200

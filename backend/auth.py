"""
Secure Authentication Module
Implements OWASP security best practices:
- Password hashing with bcrypt
- JWT with short expiration
- Rate limiting on login
- Session management
"""
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from backend.config import get_config
from backend.database.mongo_db import get_user_manager

config = get_config()


class AuthManager:
    """Secure authentication manager"""

    def __init__(self):
        self.user_manager = get_user_manager()

    def generate_access_token(self, user_id: str, username: str) -> str:
        """
        Generate short-lived access token (15 minutes)

        Args:
            user_id: User ID from database
            username: Username

        Returns:
            JWT access token
        """
        payload = {
            'user_id': user_id,
            'username': username,
            'type': 'access',
            'exp': datetime.utcnow() + timedelta(seconds=config.JWT_ACCESS_TOKEN_EXPIRES),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, config.SECRET_KEY, algorithm='HS256')

    def generate_refresh_token(self, user_id: str, username: str) -> str:
        """
        Generate long-lived refresh token (7 days)

        Args:
            user_id: User ID from database
            username: Username

        Returns:
            JWT refresh token
        """
        payload = {
            'user_id': user_id,
            'username': username,
            'type': 'refresh',
            'exp': datetime.utcnow() + timedelta(seconds=config.JWT_REFRESH_TOKEN_EXPIRES),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, config.SECRET_KEY, algorithm='HS256')

    def verify_token(self, token: str, token_type: str = 'access') -> dict:
        """
        Verify JWT token

        Args:
            token: JWT token string
            token_type: 'access' or 'refresh'

        Returns:
            Payload dict or None if invalid
        """
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=['HS256'])

            # Verify token type
            if payload.get('type') != token_type:
                return None

            return payload

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def authenticate(self, username: str, password: str) -> dict:
        """
        Authenticate user with secure password verification

        Args:
            username: Username
            password: Plain text password

        Returns:
            Authentication result with tokens or error
        """
        result = self.user_manager.authenticate_user(username, password)

        if not result['success']:
            return result

        user = result['user']
        user_id = str(user['_id'])

        # Generate tokens
        access_token = self.generate_access_token(user_id, username)
        refresh_token = self.generate_refresh_token(user_id, username)

        return {
            'success': True,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user_id,
                'username': user['username'],
                'email': user.get('email'),
                'full_name': user.get('full_name')
            }
        }

    def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Generate new access token using refresh token

        Args:
            refresh_token: Valid refresh token

        Returns:
            New access token or error
        """
        payload = self.verify_token(refresh_token, token_type='refresh')

        if not payload:
            return {'success': False, 'error': 'Invalid or expired refresh token'}

        # Generate new access token
        access_token = self.generate_access_token(
            payload['user_id'],
            payload['username']
        )

        return {
            'success': True,
            'access_token': access_token
        }


# Authentication decorators
def token_required(f):
    """
    Decorator to require valid JWT access token

    Usage:
        @app.route('/protected')
        @token_required
        def protected_route(current_user):
            return jsonify({'user': current_user})
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Extract token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            parts = auth_header.split()

            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
            else:
                return jsonify({
                    'success': False,
                    'message': 'Invalid token format. Use: Bearer <token>'
                }), 401

        if not token:
            return jsonify({
                'success': False,
                'message': 'Authentication token is missing'
            }), 401

        # Verify token
        auth_manager = AuthManager()
        payload = auth_manager.verify_token(token, token_type='access')

        if not payload:
            return jsonify({
                'success': False,
                'message': 'Invalid or expired token'
            }), 401

        # Add current_user to function arguments
        current_user = {
            'user_id': payload['user_id'],
            'username': payload['username']
        }

        return f(current_user, *args, **kwargs)

    return decorated


def admin_required(f):
    """
    Decorator to require admin privileges

    Usage:
        @app.route('/admin')
        @admin_required
        def admin_route(current_user):
            return jsonify({'message': 'Admin access granted'})
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # First check if user is authenticated
        token = None

        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            parts = auth_header.split()

            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]

        if not token:
            return jsonify({
                'success': False,
                'message': 'Authentication required'
            }), 401

        auth_manager = AuthManager()
        payload = auth_manager.verify_token(token, token_type='access')

        if not payload:
            return jsonify({
                'success': False,
                'message': 'Invalid or expired token'
            }), 401

        # Check if user is admin
        user_manager = get_user_manager()
        user_settings = user_manager.get_user_settings(payload['user_id'])

        if not user_settings or not user_settings.get('is_admin', False):
            return jsonify({
                'success': False,
                'message': 'Admin privileges required'
            }), 403

        current_user = {
            'user_id': payload['user_id'],
            'username': payload['username']
        }

        return f(current_user, *args, **kwargs)

    return decorated


# Singleton instance
_auth_manager = None


def get_auth_manager() -> AuthManager:
    """Get AuthManager singleton instance"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager

import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from backend.config import Config


class AuthManager:
    """인증 관리 클래스"""

    @staticmethod
    def generate_token(username):
        """JWT 토큰 생성"""
        payload = {
            'username': username,
            'exp': datetime.utcnow() + timedelta(days=7),  # 7일 유효
            'iat': datetime.utcnow()
        }
        token = jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')
        return token

    @staticmethod
    def verify_token(token):
        """JWT 토큰 검증"""
        try:
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    def authenticate(username, password):
        """사용자 인증"""
        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            return True
        return False


def token_required(f):
    """토큰 검증 데코레이터"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Authorization 헤더에서 토큰 추출
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # "Bearer TOKEN"
            except IndexError:
                return jsonify({'message': '토큰 형식이 올바르지 않습니다.'}), 401

        if not token:
            return jsonify({'message': '토큰이 없습니다.'}), 401

        # 토큰 검증
        payload = AuthManager.verify_token(token)
        if not payload:
            return jsonify({'message': '유효하지 않은 토큰입니다.'}), 401

        return f(*args, **kwargs)

    return decorated

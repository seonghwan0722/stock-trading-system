"""
Secure Configuration Module
Implements security best practices for environment variable management
"""
import os
import secrets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class with security hardening"""

    # Flask Core Settings
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

    # Security: SECRET_KEY must be set in environment, no default
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        if ENVIRONMENT == 'production':
            raise ValueError("SECRET_KEY must be set in production environment")
        else:
            # Generate temporary key for development (warning will be logged)
            SECRET_KEY = secrets.token_urlsafe(32)
            print("⚠️  WARNING: Using temporary SECRET_KEY. Set SECRET_KEY in .env file!")

    # JWT Configuration - Shorter expiration for security
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 900))  # 15 minutes
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 604800))  # 7 days

    # MongoDB Configuration
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'stock_trading_db')

    # Free API Keys
    # Finnhub: Real-time quotes, company financials, news (60 calls/min FREE)
    FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', '')

    # Alpha Vantage: Technical indicators, time series (5 calls/min FREE)
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')

    # DART: Korean company financials (Unlimited FREE)
    DART_API_KEY = os.getenv('DART_API_KEY', '')

    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

    # Security Settings
    MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', 5))
    LOGIN_TIMEOUT = int(os.getenv('LOGIN_TIMEOUT', 300))  # 5 minutes

    # Rate Limiting
    RATELIMIT_ENABLED = os.getenv('RATELIMIT_ENABLED', 'True').lower() == 'true'
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '100 per hour')
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')

    # CORS Settings - Restrict to specific origins
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5000').split(',')

    # File Upload Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size
    ALLOWED_EXTENSIONS = {'json', 'csv'}

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')

    # Trading Settings (from user preferences in MongoDB)
    MAX_POSITION_SIZE = int(os.getenv('MAX_POSITION_SIZE', '1000000'))  # Default max position
    MAX_POSITIONS = int(os.getenv('MAX_POSITIONS', '5'))  # Default max holdings

    # News Sources (Free)
    NEWS_SOURCES = {
        'naver_finance': 'https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258',
        'hankyung': 'https://www.hankyung.com/finance/stock',
        'mk': 'https://www.mk.co.kr/news/stock/',
    }

    @classmethod
    def validate_required_vars(cls):
        """Validate required environment variables based on environment"""
        required_dev = ['DART_API_KEY']
        required_prod = ['SECRET_KEY', 'DART_API_KEY', 'FINNHUB_API_KEY', 'MONGODB_URI']

        required = required_prod if cls.ENVIRONMENT == 'production' else required_dev
        missing = []

        for var in required:
            value = getattr(cls, var, None)
            if not value:
                missing.append(var)

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    @classmethod
    def mask_sensitive_value(cls, value: str, visible_chars: int = 4) -> str:
        """Mask sensitive values for logging"""
        if not value or len(value) <= visible_chars:
            return "****"
        return value[:visible_chars] + "****"

    @classmethod
    def get_safe_config(cls) -> dict:
        """Return configuration dict with masked sensitive values for logging"""
        return {
            'ENVIRONMENT': cls.ENVIRONMENT,
            'MONGODB_DB_NAME': cls.MONGODB_DB_NAME,
            'FINNHUB_API_KEY': cls.mask_sensitive_value(cls.FINNHUB_API_KEY),
            'DART_API_KEY': cls.mask_sensitive_value(cls.DART_API_KEY),
            'TELEGRAM_BOT_TOKEN': cls.mask_sensitive_value(cls.TELEGRAM_BOT_TOKEN),
            'RATELIMIT_ENABLED': cls.RATELIMIT_ENABLED,
            'CORS_ORIGINS': cls.CORS_ORIGINS,
        }


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration with stricter security"""
    DEBUG = False
    TESTING = False

    # Production-specific settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    MONGODB_DB_NAME = 'stock_trading_test_db'


# Configuration dictionary
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}


def get_config() -> Config:
    """Get configuration based on ENVIRONMENT variable"""
    env = os.getenv('ENVIRONMENT', 'development')
    config_class = config_by_name.get(env, DevelopmentConfig)

    # Validate required variables
    try:
        config_class.validate_required_vars()
    except ValueError as e:
        print(f"⚠️  Configuration Error: {e}")
        if env == 'production':
            raise

    return config_class

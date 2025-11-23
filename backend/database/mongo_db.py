"""
MongoDB Database Module
Secure user management and data storage
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, ConnectionFailure
import bcrypt
import secrets
from backend.config import get_config

config = get_config()


class MongoDB:
    """MongoDB connection and operations manager"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize MongoDB connection (singleton pattern)"""
        if self._initialized:
            return

        try:
            self.client = MongoClient(
                config.MONGODB_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000
            )
            # Test connection
            self.client.admin.command('ping')

            self.db = self.client[config.MONGODB_DB_NAME]
            self._initialize_collections()
            self._initialized = True
            print(f"✅ Connected to MongoDB: {config.MONGODB_DB_NAME}")

        except ConnectionFailure as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            raise

    def _initialize_collections(self):
        """Create collections and indexes"""
        # Users collection
        self.users = self.db.users
        self.users.create_index([('username', ASCENDING)], unique=True)
        self.users.create_index([('email', ASCENDING)], unique=True, sparse=True)

        # User settings collection (encrypted sensitive data)
        self.user_settings = self.db.user_settings
        self.user_settings.create_index([('user_id', ASCENDING)], unique=True)

        # Trading history
        self.trades = self.db.trades
        self.trades.create_index([('user_id', ASCENDING), ('timestamp', DESCENDING)])
        self.trades.create_index([('stock_code', ASCENDING)])

        # Portfolio
        self.portfolio = self.db.portfolio
        self.portfolio.create_index([('user_id', ASCENDING), ('stock_code', ASCENDING)], unique=True)

        # Login attempts (for brute force protection)
        self.login_attempts = self.db.login_attempts
        self.login_attempts.create_index([('username', ASCENDING)])
        self.login_attempts.create_index([('timestamp', ASCENDING)], expireAfterSeconds=3600)  # 1 hour TTL

        # Sessions
        self.sessions = self.db.sessions
        self.sessions.create_index([('session_token', ASCENDING)], unique=True)
        self.sessions.create_index([('expires_at', ASCENDING)], expireAfterSeconds=0)

        # DART company data cache
        self.dart_companies = self.db.dart_companies
        self.dart_companies.create_index([('stock_code', ASCENDING)], unique=True)
        self.dart_companies.create_index([('corp_code', ASCENDING)])

        # Market data cache
        self.market_data = self.db.market_data
        self.market_data.create_index([('symbol', ASCENDING), ('timestamp', DESCENDING)])
        self.market_data.create_index([('timestamp', ASCENDING)], expireAfterSeconds=86400)  # 24 hour TTL

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("✅ MongoDB connection closed")


class UserManager:
    """Secure user management with encrypted credentials"""

    def __init__(self):
        self.db = MongoDB()
        self.users_collection = self.db.users

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def create_user(self, username: str, password: str, email: Optional[str] = None,
                    full_name: Optional[str] = None, is_admin: bool = False) -> Dict[str, Any]:
        """
        Create a new user with hashed password

        Args:
            username: Username
            password: Plain text password (will be hashed)
            email: User email
            full_name: User's full name
            is_admin: Whether user has admin privileges

        Returns:
            User document with masked sensitive fields
        """
        try:
            password_hash = self.hash_password(password)

            user_doc = {
                'username': username,
                'password_hash': password_hash,
                'email': email,
                'full_name': full_name,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'is_active': True,
                'is_admin': is_admin,
                'last_login': None,
            }

            result = self.db.users.insert_one(user_doc)
            user_doc['_id'] = result.inserted_id

            # Remove password hash from returned document
            user_doc.pop('password_hash', None)

            return {'success': True, 'user': user_doc}

        except DuplicateKeyError:
            return {'success': False, 'error': 'Username or email already exists'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user with brute force protection

        Returns:
            Authentication result with user data or error
        """
        # Check for brute force attempts
        if not self._check_login_attempts(username):
            return {
                'success': False,
                'error': 'Too many failed login attempts. Please try again later.'
            }

        user = self.db.users.find_one({'username': username})

        if not user:
            self._record_failed_attempt(username)
            return {'success': False, 'error': 'Invalid username or password'}

        if not user.get('is_active'):
            return {'success': False, 'error': 'Account is disabled'}

        if not self.verify_password(password, user['password_hash']):
            self._record_failed_attempt(username)
            return {'success': False, 'error': 'Invalid username or password'}

        # Successful login - update last login time
        self.db.users.update_one(
            {'_id': user['_id']},
            {
                '$set': {'last_login': datetime.utcnow()},
                '$unset': {'locked_until': ''}
            }
        )

        # Clear failed attempts
        self.db.login_attempts.delete_many({'username': username})

        # Remove sensitive fields
        user.pop('password_hash', None)

        return {'success': True, 'user': user}

    def _check_login_attempts(self, username: str) -> bool:
        """Check if user is locked out due to failed login attempts"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=config.LOGIN_TIMEOUT)

        attempts = self.db.login_attempts.count_documents({
            'username': username,
            'timestamp': {'$gte': cutoff_time}
        })

        return attempts < config.MAX_LOGIN_ATTEMPTS

    def _record_failed_attempt(self, username: str):
        """Record a failed login attempt"""
        self.db.login_attempts.insert_one({
            'username': username,
            'timestamp': datetime.utcnow()
        })

    def update_user_settings(self, user_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user settings (investment profile, API keys, etc.)
        Sensitive data should be encrypted before calling this method
        """
        try:
            settings_doc = {
                'user_id': user_id,
                'updated_at': datetime.utcnow(),
                **settings
            }

            result = self.db.user_settings.update_one(
                {'user_id': user_id},
                {'$set': settings_doc},
                upsert=True
            )

            return {'success': True, 'modified': result.modified_count > 0}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_user_settings(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user settings"""
        return self.db.user_settings.find_one({'user_id': user_id})

    def create_session(self, user_id: str) -> str:
        """Create a new session token"""
        session_token = secrets.token_urlsafe(32)

        self.db.sessions.insert_one({
            'session_token': session_token,
            'user_id': user_id,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(seconds=config.JWT_ACCESS_TOKEN_EXPIRES)
        })

        return session_token

    def verify_session(self, session_token: str) -> Optional[str]:
        """Verify session and return user_id"""
        session = self.db.sessions.find_one({
            'session_token': session_token,
            'expires_at': {'$gt': datetime.utcnow()}
        })

        return session['user_id'] if session else None

    def delete_session(self, session_token: str):
        """Delete session (logout)"""
        self.db.sessions.delete_one({'session_token': session_token})


class TradingDataManager:
    """Manage trading data in MongoDB"""

    def __init__(self):
        self.db = MongoDB()

    def record_trade(self, user_id: str, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record a trade execution"""
        try:
            trade_doc = {
                'user_id': user_id,
                'timestamp': datetime.utcnow(),
                **trade_data
            }

            result = self.db.trades.insert_one(trade_doc)

            return {'success': True, 'trade_id': str(result.inserted_id)}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_trade_history(self, user_id: str, limit: int = 50,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get trade history for a user"""
        query = {'user_id': user_id}

        if start_date or end_date:
            query['timestamp'] = {}
            if start_date:
                query['timestamp']['$gte'] = start_date
            if end_date:
                query['timestamp']['$lte'] = end_date

        trades = self.db.trades.find(query).sort('timestamp', DESCENDING).limit(limit)

        return list(trades)

    def update_portfolio(self, user_id: str, stock_code: str, quantity: int,
                        avg_price: float) -> Dict[str, Any]:
        """Update user's portfolio"""
        try:
            if quantity <= 0:
                # Remove from portfolio
                self.db.portfolio.delete_one({
                    'user_id': user_id,
                    'stock_code': stock_code
                })
            else:
                # Update or insert
                self.db.portfolio.update_one(
                    {'user_id': user_id, 'stock_code': stock_code},
                    {
                        '$set': {
                            'quantity': quantity,
                            'avg_price': avg_price,
                            'updated_at': datetime.utcnow()
                        }
                    },
                    upsert=True
                )

            return {'success': True}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_portfolio(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's current portfolio"""
        return list(self.db.portfolio.find({'user_id': user_id}))


# Singleton instances
_mongodb_instance = None
_user_manager_instance = None
_trading_manager_instance = None


def get_database() -> MongoDB:
    """Get MongoDB singleton instance"""
    global _mongodb_instance
    if _mongodb_instance is None:
        _mongodb_instance = MongoDB()
    return _mongodb_instance


def get_user_manager() -> UserManager:
    """Get UserManager singleton instance"""
    global _user_manager_instance
    if _user_manager_instance is None:
        _user_manager_instance = UserManager()
    return _user_manager_instance


def get_trading_manager() -> TradingDataManager:
    """Get TradingDataManager singleton instance"""
    global _trading_manager_instance
    if _trading_manager_instance is None:
        _trading_manager_instance = TradingDataManager()
    return _trading_manager_instance

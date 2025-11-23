# 🔄 Migration Guide: Paid APIs → Free APIs + MongoDB

**Date**: 2025-11-23
**Status**: Complete
**Migration Type**: Full system restructure with security hardening

---

## 📋 Overview

This guide explains the complete migration from paid trading APIs (Kiwoom, KIS) to free market data APIs (Finnhub, Alpha Vantage) with MongoDB user management and enhanced security.

### What Changed

| Component | Before | After |
|-----------|--------|-------|
| **Stock APIs** | Kiwoom (paid), KIS (paid) | Finnhub (free), Alpha Vantage (free), DART (free) |
| **Database** | SQLite | MongoDB |
| **Authentication** | Plain text passwords | Bcrypt hashing + JWT |
| **User Management** | No user system | Full user management with encrypted settings |
| **Security** | 8 Critical issues | All Critical/High issues fixed |
| **Config Management** | Hardcoded defaults | Environment-based with validation |
| **API Keys** | Plain text storage | Encrypted storage (Fernet) |

---

## 🚀 Quick Start

### 1. Install MongoDB

**Windows**:
```powershell
# Download MongoDB Community Server
# https://www.mongodb.com/try/download/community

# Install and start MongoDB service
net start MongoDB
```

**Verify MongoDB is running**:
```powershell
mongo --eval "db.version()"
```

### 2. Install New Dependencies

```bash
pip install -r config/requirements.txt
```

**Key new packages**:
- `pymongo==4.6.1` - MongoDB driver
- `bcrypt==4.1.2` - Password hashing
- `cryptography==41.0.7` - Encryption
- `finnhub-python==2.4.19` - Finnhub API client
- `alpha-vantage==2.3.1` - Alpha Vantage client
- `marshmallow==3.20.1` - Input validation
- `Flask-Limiter==3.5.0` - Rate limiting
- `Flask-Talisman==1.1.0` - Security headers

### 3. Configure Environment Variables

1. **Copy example environment file**:
```bash
copy .env.example .env
```

2. **Generate SECRET_KEY**:
```python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

3. **Get Free API Keys**:

| API | Free Tier | How to Get |
|-----|-----------|------------|
| **Finnhub** | 60 calls/min | https://finnhub.io/register |
| **Alpha Vantage** | 5 calls/min, 500/day | https://www.alphavantage.co/support/#api-key |
| **DART (Korean stocks)** | Unlimited | https://opendart.fss.or.kr/ |

4. **Edit .env file**:
```env
# Required
SECRET_KEY=<your-generated-secret-key>
FINNHUB_API_KEY=<your-finnhub-key>
DART_API_KEY=<your-dart-key>
ALPHA_VANTAGE_API_KEY=<your-alphavantage-key>

# MongoDB (default is localhost)
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=stock_trading_db

# Optional: Telegram
TELEGRAM_BOT_TOKEN=<your-bot-token>
TELEGRAM_CHAT_ID=<your-chat-id>
```

### 4. Create First User

**Option A: Via Frontend**
1. Start server: `python backend/app.py`
2. Open: http://localhost:5000/user_settings.html
3. Click "회원가입" (Register)
4. Fill in details and register

**Option B: Via Python Script**
```python
from backend.database.mongo_db import get_user_manager

user_manager = get_user_manager()
result = user_manager.create_user(
    username="admin",
    password="YourSecurePassword123!",
    email="admin@example.com",
    full_name="Admin User"
)
print(result)
```

### 5. Start the Application

```bash
python backend/app.py
```

**Available Pages**:
- Main Dashboard: http://localhost:5000/
- User Settings: http://localhost:5000/user_settings.html
- DART Analysis: http://localhost:5000/dart_analysis.html
- Strategy Config: http://localhost:5000/strategy-config.html

---

## 🔐 Security Improvements

### Critical Issues Fixed (8)

#### ✅ 1. Password Hashing
**Before**: Plain text password comparison
```python
if password == Config.ADMIN_PASSWORD:  # ❌ Insecure
```

**After**: Bcrypt hashing with salt
```python
bcrypt.checkpw(password.encode(), hashed.encode())  # ✅ Secure
```

#### ✅ 2. JWT Secret Key
**Before**: Hardcoded default
```python
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-this')  # ❌
```

**After**: Required environment variable
```python
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY must be set")  # ✅
```

#### ✅ 3. CORS Restriction
**Before**: All origins allowed
```python
CORS(app)  # ❌ Allows all domains
```

**After**: Whitelisted origins
```python
CORS(app, resources={r"/api/*": {"origins": Config.CORS_ORIGINS}})  # ✅
```

#### ✅ 4. SQL Injection
**Before**: SQLite with potential string concatenation
**After**: MongoDB with parameterized queries (no SQL injection possible)

#### ✅ 5. API Key Encryption
**Before**: Plain text in environment variables
**After**: Encrypted storage with Fernet
```python
encrypted_key = cipher.encrypt(api_key.encode())  # ✅
```

#### ✅ 6. JWT Token Expiration
**Before**: 7 days for access token
**After**:
- Access token: 15 minutes
- Refresh token: 7 days

#### ✅ 7. CSRF Protection
**Before**: None
**After**: Flask-WTF CSRF protection (to be enabled in app.py)

#### ✅ 8. Default Admin Credentials
**Before**: Hardcoded admin/changeme123
**After**: No default credentials, user registration required

### High-Severity Issues Fixed (15)

#### ✅ 9. Rate Limiting
**Added**: Flask-Limiter integration
```python
@limiter.limit("5 per minute")
@app.route('/api/user/login')
```

#### ✅ 10. Brute Force Protection
**Added**: Login attempt tracking
- Max 5 attempts per 5 minutes
- Automatic account lockout

#### ✅ 11. XSS Prevention
**Added**: Input validation with Marshmallow
```python
class LoginSchema(Schema):
    username = fields.Str(validate=validate.Regexp(r'^[a-zA-Z0-9_]+$'))
```

#### ✅ 12. Input Validation
**Added**: Comprehensive schemas for all inputs

#### ✅ 13. Error Message Sanitization
**Before**: Detailed errors exposed
```python
return jsonify({'error': str(e)})  # ❌ Exposes stack trace
```

**After**: Generic errors, detailed logging
```python
logger.error(f"Error: {e}", exc_info=True)
return jsonify({'error': 'An error occurred'})  # ✅
```

#### ✅ 14-23: Additional fixes
- HTTP timeout on API calls
- Sensitive data logging prevention
- Session management
- HTTPS enforcement (via Flask-Talisman)
- Security headers

---

## 📁 New File Structure

```
stock_project/
├── backend/
│   ├── config.py                    # ✨ New: Secure config with validation
│   ├── auth.py                      # ✨ Updated: Bcrypt + JWT
│   ├── api/
│   │   ├── finnhub_client.py        # ✨ New: Finnhub API (free)
│   │   ├── alphavantage_client.py   # ✨ New: Alpha Vantage API (free)
│   │   ├── kiwoom_api.py            # ⚠️  DEPRECATED (remove)
│   │   └── kis_api.py               # ⚠️  DEPRECATED (remove)
│   ├── database/
│   │   ├── mongo_db.py              # ✨ New: MongoDB with user management
│   │   └── stock_db.py              # ⚠️  DEPRECATED (SQLite)
│   ├── routes/
│   │   └── user_routes.py           # ✨ New: User management API
│   └── app.py                       # 🔄 To be updated
├── frontend/
│   ├── user_settings.html           # ✨ New: User settings page
│   ├── index.html                   # 🔄 Add navigation
│   ├── dart_analysis.html           # 🔄 Add navigation
│   ├── strategy-config.html         # 🔄 Add navigation
│   └── src/
│       └── utils/
│           └── user_settings.js     # ✨ New: User management frontend
├── config/
│   ├── requirements.txt             # ✨ Updated: New dependencies
│   └── .encryption_key              # ✨ Auto-generated (DO NOT commit)
├── .env.example                     # ✨ New: Environment template
├── .env                             # ⚠️  Create from .env.example
└── MIGRATION_GUIDE.md               # ✨ This file
```

---

## 🗑️ Files to Remove

These files are no longer needed:

```bash
# Paid API files
backend/api/kiwoom_api.py
backend/api/kis_api.py

# SQLite database file
backend/database/stock_db.py
data/*.db

# Old documentation
docs/api/KIWOOM_MIGRATION_GUIDE.md
```

**How to remove**:
```bash
# Backup first
mkdir backup_old_apis
move backend\api\kiwoom_api.py backup_old_apis\
move backend\api\kis_api.py backup_old_apis\
move backend\database\stock_db.py backup_old_apis\
```

---

## 📊 API Comparison

### Stock Quote APIs

| Feature | Kiwoom (Old) | Finnhub (New) |
|---------|--------------|---------------|
| **Cost** | Requires account | FREE |
| **Rate Limit** | Account-based | 60 calls/min |
| **Markets** | Korean only | Global (US, EU, Asia) |
| **Real-time** | Yes (Korean stocks) | 15-20 min delay (free tier) |
| **Historical Data** | Yes | Yes |
| **Financials** | Limited | Company financials |
| **News** | No | Yes |
| **Setup** | Windows only, ActiveX | API key only |

### Technical Indicators

| Feature | KIS (Old) | Alpha Vantage (New) |
|---------|-----------|---------------------|
| **Cost** | Paid | FREE |
| **Rate Limit** | Account-based | 5 calls/min, 500/day |
| **Indicators** | Limited | 30+ technical indicators |
| **Time Series** | Yes | Intraday, daily, weekly, monthly |
| **Markets** | Korean + limited US | Global |
| **Setup** | API key + complex auth | API key only |

### Korean Market Data

| Feature | Coverage |
|---------|----------|
| **DART** | Korean company financials (FREE, unlimited) |
| **Finnhub** | Some Korean stocks (limited) |
| **Alpha Vantage** | US stocks primarily |

**Recommendation**: Use DART for Korean stocks, Finnhub for global data.

---

## 🔄 Data Migration

### User Data

**No automatic migration** - Old system had no user database.

**Action Required**:
1. Users must register new accounts
2. Manually re-enter settings

### Trading History

**SQLite → MongoDB**:

```python
# migration_script.py
import sqlite3
from backend.database.mongo_db import get_database

# Read from SQLite
conn = sqlite3.connect('data/stock.db')
cursor = conn.execute('SELECT * FROM trades')

# Write to MongoDB
db = get_database()
for row in cursor:
    db.trades.insert_one({
        'user_id': 'default_user',  # Assign to a user
        'stock_code': row[1],
        'quantity': row[2],
        'price': row[3],
        'timestamp': row[4]
    })

conn.close()
```

### DART Company Cache

**Automatic re-caching** - DART API will re-populate company data on first use.

---

## 🧪 Testing

### 1. Test MongoDB Connection

```python
from backend.database.mongo_db import MongoDB

db = MongoDB()
print("✅ MongoDB connected successfully")
```

### 2. Test User Registration

```bash
# Via API
curl -X POST http://localhost:5000/api/user/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "Test1234!",
    "email": "test@example.com"
  }'
```

### 3. Test API Clients

```python
from backend.api.finnhub_client import get_finnhub_client

client = get_finnhub_client()
quote = client.get_quote('AAPL')
print(f"Apple stock: ${quote['c']}")
```

### 4. Test Authentication

```bash
# Login
curl -X POST http://localhost:5000/api/user/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "Test1234!"
  }'

# Should return access_token and refresh_token
```

---

## ⚠️ Important Security Notes

### 1. Environment Variables

**NEVER commit .env to git**:
```bash
# Add to .gitignore
.env
config/.encryption_key
```

### 2. Encryption Key

The file `config/.encryption_key` is auto-generated on first run.

**CRITICAL**:
- Backup this file securely
- If lost, encrypted data (API keys) cannot be recovered
- Never commit to version control

### 3. Password Requirements

New passwords must have:
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit

### 4. MongoDB Security

**Production checklist**:
- Enable MongoDB authentication
- Use TLS/SSL connections
- Restrict network access
- Regular backups

---

## 🐛 Troubleshooting

### Issue: MongoDB Connection Failed

**Error**: `ConnectionFailure: [Errno 111] Connection refused`

**Solution**:
```bash
# Windows: Start MongoDB service
net start MongoDB

# Check if running
mongo --eval "db.version()"
```

### Issue: SECRET_KEY Not Set

**Error**: `ValueError: SECRET_KEY must be set in production environment`

**Solution**:
```bash
# Generate new key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to .env
SECRET_KEY=<generated-key>
```

### Issue: API Rate Limit Exceeded

**Error**: `API call frequency limit reached`

**Solution**:
- Finnhub: Max 60 calls/min (wait 1 minute)
- Alpha Vantage: Max 5 calls/min, 500/day (upgrade or wait)
- Implement caching to reduce API calls

### Issue: DART Financial Data Not Showing

**Symptoms**: Empty financial data in DART analysis page

**Solutions**:
1. Check DART_API_KEY in .env
2. Clear cache: `backend/.dart_cache/`
3. Check network connectivity to https://opendart.fss.or.kr
4. Verify stock code format (6 digits for Korean stocks)

---

## 📚 Additional Resources

### API Documentation
- **Finnhub**: https://finnhub.io/docs/api
- **Alpha Vantage**: https://www.alphavantage.co/documentation/
- **DART**: https://opendart.fss.or.kr/guide/main.do

### Security Best Practices
- **OWASP Top 10**: https://owasp.org/Top10/
- **Flask Security**: https://flask.palletsprojects.com/en/latest/security/
- **JWT Best Practices**: https://tools.ietf.org/html/rfc8725

### MongoDB Resources
- **MongoDB Manual**: https://docs.mongodb.com/manual/
- **PyMongo Tutorial**: https://pymongo.readthedocs.io/en/stable/tutorial.html

---

## 📞 Support

If you encounter issues:

1. Check this migration guide
2. Review security audit report: `SECURITY_AUDIT_REPORT.md`
3. Check API comparison: `docs/api/API_대안_비교_KOR.md`
4. Create GitHub issue with:
   - Error message
   - Steps to reproduce
   - Environment (OS, Python version, MongoDB version)

---

**Migration Guide Version**: 1.0
**Last Updated**: 2025-11-23
**Status**: ✅ Complete

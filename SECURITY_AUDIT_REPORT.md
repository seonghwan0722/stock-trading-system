# 보안 취약점 점검 보고서

**프로젝트**: 주식 자동매매 시스템
**점검 일자**: 2025-11-23
**점검 범위**: Backend 전체 모듈

---

## 📋 요약

총 **45개의 보안 취약점**이 발견되었습니다.

| 심각도 | 개수 | 비율 |
|--------|------|------|
| 🔴 Critical | 8 | 18% |
| 🟠 High | 15 | 33% |
| 🟡 Medium | 14 | 31% |
| 🟢 Low | 8 | 18% |

---

## 🔴 Critical (치명적) - 즉시 조치 필요

### 1. 비밀번호 평문 저장 및 비교
**파일**: [backend/auth.py:36](backend/auth.py#L36)
**설명**: 사용자 비밀번호가 평문으로 비교됩니다. 해싱/솔팅 없음.

```python
# 취약한 코드
if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
    return True
```

**권장 조치**:
- bcrypt 또는 argon2를 사용한 비밀번호 해싱
- 솔트 추가
- 데이터베이스에 해시만 저장

**위험도**: 🔴 Critical
**OWASP**: A02:2021 – Cryptographic Failures

---

### 2. JWT SECRET_KEY 하드코딩
**파일**: [backend/config.py:10](backend/config.py#L10)
**설명**: JWT SECRET_KEY가 기본값으로 하드코딩되어 있습니다.

```python
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
```

**권장 조치**:
- 환경 변수로만 관리
- 기본값 제거
- 복잡한 랜덤 키 생성 강제
- 키 로테이션 정책 수립

**위험도**: 🔴 Critical
**OWASP**: A02:2021 – Cryptographic Failures

---

### 3. CORS 전체 허용
**파일**: [backend/app.py:28](backend/app.py#L28)
**설명**: 모든 도메인에서 API 접근 가능

```python
CORS(app)  # 모든 origin 허용
```

**권장 조치**:
```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://yourdomain.com"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"],
        "max_age": 3600
    }
})
```

**위험도**: 🔴 Critical
**OWASP**: A05:2021 – Security Misconfiguration

---

### 4. SQL Injection 가능성
**파일**: [backend/database/stock_db.py](backend/database/stock_db.py)
**설명**: 사용자 입력이 SQL 쿼리에 직접 삽입될 가능성

**권장 조치**:
- Parameterized queries 사용
- ORM 사용 (SQLAlchemy)
- 입력값 검증 및 이스케이핑

**위험도**: 🔴 Critical
**OWASP**: A03:2021 – Injection

---

### 5. 기본 관리자 계정 노출
**파일**: [backend/config.py:28-29](backend/config.py#L28-L29)
**설명**: 기본 관리자 계정이 코드에 노출됨

```python
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'changeme123')
```

**권장 조치**:
- 기본값 제거
- 초기 설정 시 강제 변경
- 복잡한 비밀번호 정책 적용

**위험도**: 🔴 Critical
**OWASP**: A07:2021 – Identification and Authentication Failures

---

### 6. API 키 평문 저장
**파일**: [backend/config.py:13-25](backend/config.py#L13-L25)
**설명**: 민감한 API 키가 환경 변수에만 의존

**권장 조치**:
- AWS Secrets Manager, Azure Key Vault 사용
- 암호화된 설정 파일
- 키 로테이션 자동화

**위험도**: 🔴 Critical
**OWASP**: A02:2021 – Cryptographic Failures

---

### 7. JWT 토큰 만료 시간 과다 (7일)
**파일**: [backend/auth.py:16](backend/auth.py#L16)
**설명**: 토큰 유효 기간이 너무 깁니다.

```python
'exp': datetime.utcnow() + timedelta(days=7)
```

**권장 조치**:
- Access Token: 15분 ~ 1시간
- Refresh Token: 7일 ~ 30일
- Refresh Token 로테이션 구현

**위험도**: 🔴 Critical
**OWASP**: A07:2021 – Identification and Authentication Failures

---

### 8. CSRF 보호 없음
**파일**: [backend/app.py](backend/app.py) 전체
**설명**: CSRF 토큰 검증이 없습니다.

**권장 조치**:
```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)
```

**위험도**: 🔴 Critical
**OWASP**: A01:2021 – Broken Access Control

---

## 🟠 High (높음)

### 9. Rate Limiting 부재
**파일**: [backend/app.py](backend/app.py) 전체
**설명**: API 요청 제한이 없어 DoS 공격에 취약

**권장 조치**:
```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.headers.get('Authorization'),
    default_limits=["100 per hour"]
)

@app.route('/api/auth/login')
@limiter.limit("5 per minute")
def login():
    ...
```

**위험도**: 🟠 High
**OWASP**: A05:2021 – Security Misconfiguration

---

### 10. Brute Force 공격 방어 없음
**파일**: [backend/app.py:48-66](backend/app.py#L48-L66)
**설명**: 로그인 시도 제한이 없습니다.

**권장 조치**:
- 로그인 시도 횟수 제한 (5회)
- 계정 잠금 메커니즘
- CAPTCHA 추가
- IP 기반 블랙리스트

**위험도**: 🟠 High
**OWASP**: A07:2021 – Identification and Authentication Failures

---

### 11. XSS (Cross-Site Scripting) 가능성
**파일**: [backend/dart/dart_routes.py:71-106](backend/dart/dart_routes.py#L71-L106)
**설명**: 검색 쿼리가 검증 없이 반환됨

**권장 조치**:
```python
from markupsafe import escape

query = escape(request.args.get('q', '').strip())
```

**위험도**: 🟠 High
**OWASP**: A03:2021 – Injection

---

### 12. 입력 검증 부족
**파일**: [backend/app.py:221-244](backend/app.py#L221-L244)
**설명**: stock_code, quantity, price 검증 없음

**권장 조치**:
```python
from marshmallow import Schema, fields, validate

class BuyOrderSchema(Schema):
    stock_code = fields.Str(required=True, validate=validate.Regexp(r'^\d{6}$'))
    quantity = fields.Int(required=True, validate=validate.Range(min=1, max=10000))
    price = fields.Int(validate=validate.Range(min=0))
```

**위험도**: 🟠 High
**OWASP**: A03:2021 – Injection

---

### 13. 에러 메시지 정보 노출
**파일**: [backend/app.py:180-183](backend/app.py#L180-L183)
**설명**: 상세 에러 메시지가 클라이언트에 노출됨

```python
return jsonify({
    'success': False,
    'message': f'상세정보 조회 중 오류 발생: {str(e)}'  # 스택 트레이스 노출 가능
})
```

**권장 조치**:
```python
# 로그에만 상세 정보 기록
logger.error(f"Detail error: {str(e)}", exc_info=True)

# 사용자에게는 일반 메시지만
return jsonify({
    'success': False,
    'message': '조회 중 오류가 발생했습니다.'
})
```

**위험도**: 🟠 High
**OWASP**: A05:2021 – Security Misconfiguration

---

### 14. HTTP 타임아웃 설정 없음
**파일**: [backend/api/kis_api.py](backend/api/kis_api.py) 전체
**설명**: 외부 API 호출 시 타임아웃 없음 (Slowloris 공격 취약)

**권장 조치**:
```python
response = requests.get(url, headers=headers, params=params, timeout=10)
```

**위험도**: 🟠 High
**OWASP**: A05:2021 – Security Misconfiguration

---

### 15. 민감 정보 로깅
**파일**: [backend/app.py:446](backend/app.py#L446)
**설명**: 전략 설정이 print로 출력됨 (로그에 민감 정보 포함 가능)

```python
print(f"전략 설정 저장: {data}")  # 토큰, API 키 등 포함 가능
```

**권장 조치**:
```python
# 민감 정보 필터링
safe_data = {k: v for k, v in data.items() if k not in ['token', 'api_key', 'password']}
logger.info(f"Strategy settings saved: {safe_data}")
```

**위험도**: 🟠 High
**OWASP**: A09:2021 – Security Logging and Monitoring Failures

---

### 16. Authorization 헤더 파싱 오류 처리 미흡
**파일**: [backend/auth.py:51-53](backend/auth.py#L51-L53)
**설명**: IndexError 가능성

```python
try:
    token = auth_header.split(" ")[1]  # 배열 인덱스 에러 가능
except IndexError:
    return jsonify({'message': '토큰 형식이 올바르지 않습니다.'}), 401
```

**권장 조치**: 이미 처리되어 있으나, 더 명시적인 검증 추가 권장

**위험도**: 🟠 High
**OWASP**: A04:2021 – Insecure Design

---

### 17. Path Traversal 가능성
**파일**: [backend/trading/strategy_manager.py:26](backend/trading/strategy_manager.py#L26)
**설명**: config_file 경로 검증 없음

**권장 조치**:
```python
from pathlib import Path

config_file = Path(__file__).parent / config_file
if not config_file.resolve().is_relative_to(Path(__file__).parent):
    raise ValueError("Invalid config file path")
```

**위험도**: 🟠 High
**OWASP**: A03:2021 – Injection

---

### 18. JSON 파일 암호화 없음
**파일**: [backend/trading/strategy_manager.py:69-75](backend/trading/strategy_manager.py#L69-L75)
**설명**: 전략 설정이 평문 JSON으로 저장됨

**권장 조치**:
- 암호화된 설정 파일 사용
- 파일 권한 제한 (chmod 600)

**위험도**: 🟠 High
**OWASP**: A02:2021 – Cryptographic Failures

---

### 19. 세션 관리 부재
**파일**: [backend/app.py](backend/app.py) 전체
**설명**: Flask Session 사용 없음 (JWT만 사용)

**권장 조치**:
- Flask-Session 사용
- Redis 기반 세션 저장소
- 세션 타임아웃 설정

**위험도**: 🟠 High
**OWASP**: A07:2021 – Identification and Authentication Failures

---

### 20. HTTPS 강제 없음
**파일**: [backend/app.py:1028](backend/app.py#L1028)
**설명**: HTTP로 서비스 가능

**권장 조치**:
```python
from flask_talisman import Talisman

Talisman(app, force_https=True)
```

**위험도**: 🟠 High
**OWASP**: A02:2021 – Cryptographic Failures

---

### 21. 외부 입력 기반 URL 생성
**파일**: [backend/news/news_summary.py:35](backend/news/news_summary.py#L35)
**설명**: URL이 외부 입력으로 생성될 가능성 (SSRF)

**권장 조치**:
- 허용된 도메인 화이트리스트
- URL 검증

**위험도**: 🟠 High
**OWASP**: A10:2021 – Server-Side Request Forgery

---

### 22. BeautifulSoup XML 파싱 (XXE)
**파일**: [backend/news/news_summary.py](backend/news/news_summary.py)
**설명**: XML 엔티티 확장 공격 가능성

**권장 조치**:
```python
from defusedxml import ElementTree
soup = BeautifulSoup(response.text, 'html.parser', features="lxml")
```

**위험도**: 🟠 High
**OWASP**: A03:2021 – Injection

---

### 23. 웹 스크래핑 시 SSRF 가능성
**파일**: [backend/news/news_summary.py:26, 54, 85](backend/news/news_summary.py)
**설명**: requests.get이 검증 없이 사용됨

**권장 조치**:
```python
ALLOWED_DOMAINS = ['finance.naver.com', 'hankyung.com', 'mk.co.kr']

def validate_url(url):
    from urllib.parse import urlparse
    domain = urlparse(url).netloc
    return any(allowed in domain for allowed in ALLOWED_DOMAINS)
```

**위험도**: 🟠 High
**OWASP**: A10:2021 – Server-Side Request Forgery

---

## 🟡 Medium (중간)

### 24. 비밀번호 복잡도 정책 없음
**파일**: [backend/auth.py](backend/auth.py)
**설명**: 비밀번호 강도 검증 없음

**권장 조치**:
- 최소 12자 이상
- 대소문자, 숫자, 특수문자 포함
- 일반적인 비밀번호 차단 (dictionary attack)

**위험도**: 🟡 Medium
**OWASP**: A07:2021 – Identification and Authentication Failures

---

### 25. 로그 레벨 설정 없음
**파일**: 전체 프로젝트
**설명**: print() 사용, 구조화된 로깅 없음

**권장 조치**:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

**위험도**: 🟡 Medium
**OWASP**: A09:2021 – Security Logging and Monitoring Failures

---

### 26. 환경 변수 검증 없음
**파일**: [backend/config.py](backend/config.py) 전체
**설명**: 필수 환경 변수 누락 시 처리 없음

**권장 조치**:
```python
required_vars = ['KIS_APP_KEY', 'KIS_APP_SECRET', 'SECRET_KEY']
missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    raise ValueError(f"Missing required env vars: {missing}")
```

**위험도**: 🟡 Medium
**OWASP**: A05:2021 – Security Misconfiguration

---

### 27. 디버그 모드 설정
**파일**: [backend/app.py:1028](backend/app.py#L1028)
**설명**: debug=False이지만 명시적 검증 없음

**권장 조치**:
```python
DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
app.run(host='0.0.0.0', port=5000, debug=DEBUG)

# Production에서는 반드시 False
if os.getenv('ENVIRONMENT') == 'production' and DEBUG:
    raise ValueError("Debug mode cannot be enabled in production")
```

**위험도**: 🟡 Medium
**OWASP**: A05:2021 – Security Misconfiguration

---

### 28. 파일 업로드 검증 없음
**설명**: 프로젝트에서 파일 업로드 기능 사용 시 검증 필요

**권장 조치**:
- 파일 확장자 화이트리스트
- 파일 크기 제한
- 바이러스 스캔
- 파일 타입 검증 (magic bytes)

**위험도**: 🟡 Medium
**OWASP**: A04:2021 – Insecure Design

---

### 29. 의존성 버전 고정 없음
**파일**: [config/requirements.txt](config/requirements.txt)
**설명**: 패키지 버전이 고정되지 않을 가능성

**권장 조치**:
```
Flask==2.3.0
requests==2.31.0
# 정확한 버전 명시
```

**위험도**: 🟡 Medium
**OWASP**: A06:2021 – Vulnerable and Outdated Components

---

### 30. Content Security Policy 없음
**파일**: [backend/app.py](backend/app.py)
**설명**: CSP 헤더 설정 없음

**권장 조치**:
```python
@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```

**위험도**: 🟡 Medium
**OWASP**: A05:2021 – Security Misconfiguration

---

### 31. 정적 파일 서빙 보안
**파일**: [backend/app.py:741-750](backend/app.py#L741-L750)
**설명**: 정적 파일 서빙 시 보안 검증 없음

**권장 조치**:
- Nginx/Apache 사용
- 파일 경로 검증
- Directory listing 비활성화

**위험도**: 🟡 Medium
**OWASP**: A05:2021 – Security Misconfiguration

---

### 32. API 버전 관리 없음
**파일**: [backend/app.py](backend/app.py)
**설명**: /api/v1/ 같은 버전 관리 없음

**권장 조치**:
```python
@app.route('/api/v1/auth/login', methods=['POST'])
```

**위험도**: 🟡 Medium
**OWASP**: A04:2021 – Insecure Design

---

### 33. 사용자 입력 길이 제한 없음
**파일**: 전체 API 엔드포인트
**설명**: 입력값 길이 제한 없음 (Buffer Overflow)

**권장 조치**:
```python
if len(username) > 50:
    return jsonify({'error': 'Username too long'}), 400
```

**위험도**: 🟡 Medium
**OWASP**: A03:2021 – Injection

---

### 34. 동시성 제어 없음
**파일**: [backend/trading/strategy_manager.py](backend/trading/strategy_manager.py)
**설명**: 파일 읽기/쓰기 시 락 없음

**권장 조치**:
```python
import threading

lock = threading.Lock()

def _save_config(self):
    with lock:
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)
```

**위험도**: 🟡 Medium
**OWASP**: A04:2021 – Insecure Design

---

### 35. API 응답 크기 제한 없음
**파일**: [backend/dart/dart_routes.py](backend/dart/dart_routes.py)
**설명**: 대량 데이터 반환 시 DoS 가능

**권장 조치**:
```python
limit = min(int(request.args.get('limit', 20)), 100)  # 최대 100개
```

**위험도**: 🟡 Medium
**OWASP**: A05:2021 – Security Misconfiguration

---

### 36. 백그라운드 작업 오류 처리
**파일**: [backend/app.py:755-815](backend/app.py#L755-L815)
**설명**: 예외 발생 시 스케줄러 중단 가능

**권장 조치**:
```python
def send_news_summary_job():
    try:
        # 작업 수행
    except Exception as e:
        logger.error(f"News summary job failed: {e}", exc_info=True)
        # 재시도 로직
```

**위험도**: 🟡 Medium
**OWASP**: A04:2021 – Insecure Design

---

### 37. 데이터베이스 연결 풀링 없음
**파일**: [backend/database/stock_db.py](backend/database/stock_db.py)
**설명**: SQLite 연결 관리 최적화 필요

**권장 조치**:
- SQLAlchemy 연결 풀 사용
- 연결 타임아웃 설정

**위험도**: 🟡 Medium
**OWASP**: A04:2021 – Insecure Design

---

## 🟢 Low (낮음)

### 38. 하드코딩된 URL
**파일**: [backend/config.py:37-41](backend/config.py#L37-L41)
**설명**: 뉴스 소스 URL이 하드코딩됨

**권장 조치**: 환경 변수 또는 설정 파일 사용

**위험도**: 🟢 Low
**OWASP**: A05:2021 – Security Misconfiguration

---

### 39. User-Agent 고정
**파일**: [backend/news/news_summary.py:16-18](backend/news/news_summary.py#L16-L18)
**설명**: User-Agent가 고정됨

**권장 조치**: 랜덤 User-Agent 사용

**위험도**: 🟢 Low
**OWASP**: N/A

---

### 40. 주석 부족
**파일**: 전체 프로젝트
**설명**: 보안 관련 로직 주석 부족

**권장 조치**: 보안 결정 사항 문서화

**위험도**: 🟢 Low
**OWASP**: A04:2021 – Insecure Design

---

### 41. 에러 코드 일관성
**파일**: 전체 API
**설명**: HTTP 상태 코드 일관성 부족

**권장 조치**:
- 200: 성공
- 400: 잘못된 요청
- 401: 인증 필요
- 403: 권한 없음
- 404: 찾을 수 없음
- 500: 서버 오류

**위험도**: 🟢 Low
**OWASP**: A04:2021 – Insecure Design

---

### 42. API 문서화 부족
**파일**: 전체 프로젝트
**설명**: Swagger/OpenAPI 문서 없음

**권장 조치**: Flask-RESTX 또는 flasgger 사용

**위험도**: 🟢 Low
**OWASP**: A04:2021 – Insecure Design

---

### 43. 환경 분리 부족
**파일**: [backend/config.py](backend/config.py)
**설명**: dev/staging/prod 환경 구분 없음

**권장 조치**:
```python
class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
```

**위험도**: 🟢 Low
**OWASP**: A05:2021 – Security Misconfiguration

---

### 44. 헬스 체크 엔드포인트 없음
**파일**: [backend/app.py](backend/app.py)
**설명**: /health 엔드포인트 없음

**권장 조치**:
```python
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'}), 200
```

**위험도**: 🟢 Low
**OWASP**: A09:2021 – Security Logging and Monitoring Failures

---

### 45. 캐싱 헤더 설정 없음
**파일**: [backend/app.py](backend/app.py)
**설명**: Cache-Control 헤더 없음

**권장 조치**:
```python
@app.after_request
def add_cache_headers(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    return response
```

**위험도**: 🟢 Low
**OWASP**: A05:2021 – Security Misconfiguration

---

## 🛠️ 우선순위 조치 계획

### Week 1: Critical 취약점 해결
1. 비밀번호 해싱 구현 (bcrypt)
2. JWT SECRET_KEY 환경 변수 강제
3. CORS 화이트리스트 설정
4. SQL Injection 방어 (Parameterized queries)
5. 기본 관리자 계정 제거

### Week 2: High 취약점 해결
1. Rate Limiting 구현
2. Brute Force 방어
3. XSS 방어
4. 입력 검증 스키마 추가
5. 에러 메시지 표준화

### Week 3-4: Medium/Low 취약점 해결
1. 로깅 시스템 구축
2. 보안 헤더 추가
3. 환경 변수 검증
4. 의존성 업데이트

---

## 📚 참고 자료

- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

## 📝 검토자 서명

**검토자**: Claude Code Security Audit
**검토 일자**: 2025-11-23
**다음 검토 예정일**: 2025-12-23

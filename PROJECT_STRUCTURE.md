# 📁 프로젝트 폴더 구조

## 🎯 개요

깔끔하게 정리된 주식 자동매매 시스템 프로젝트 구조입니다.

---

## 📂 전체 구조

```
주식 프로젝트/
│
├── 📄 README.md                    # 프로젝트 개요
├── 📄 run.py                       # 서버 실행 스크립트
├── 📄 .env                         # 환경 변수 (API 키 등)
├── 📄 .gitignore                   # Git 제외 파일 목록
│
├── 📁 backend/                     # 백엔드 소스코드
│   ├── 📁 api/                     # 외부 API 클라이언트
│   │   └── kis_api.py              # 한국투자증권 API
│   │
│   ├── 📁 dart/                    # DART API 모듈
│   │   ├── __init__.py
│   │   ├── dart_api_client.py      # DART API 클라이언트
│   │   ├── dart_routes.py          # Flask Blueprint
│   │   └── collect_companies.py    # 종목 수집 스크립트
│   │
│   ├── 📁 database/                # 데이터베이스 관리
│   │   ├── __init__.py
│   │   └── stock_db.py             # SQLite 종목 DB
│   │
│   ├── 📁 trading/                 # 매매 전략
│   │   ├── buy_strategy.py         # 매수 전략
│   │   ├── sell_strategy.py        # 매도 전략
│   │   ├── strategies.py           # 전략 모음
│   │   └── strategy_manager.py     # 전략 관리자
│   │
│   ├── 📁 scraper/                 # 웹 스크래퍼
│   │   ├── __init__.py
│   │   ├── base_scraper.py
│   │   ├── capitol_trades_scraper.py
│   │   ├── stocknear_scraper.py
│   │   ├── stock_analysis_scraper.py
│   │   └── chart_exchange_scraper.py
│   │
│   ├── 📁 news/                    # 뉴스 분석
│   │   └── news_summary.py
│   │
│   ├── 📁 telegram/                # 텔레그램 봇
│   │   └── bot.py
│   │
│   ├── auth.py                     # 인증 관리
│   ├── config.py                   # 설정
│   └── app.py                      # Flask 메인 앱
│
├── 📁 frontend/                    # 프론트엔드
│   ├── index.html                  # 메인 페이지
│   ├── strategy-config.html        # 전략 설정 페이지
│   ├── dart_analysis.html          # DART 재무제표 분석 페이지
│   ├── dart_analysis.js            # DART 분석 JavaScript
│   ├── script.js                   # 메인 JavaScript
│   └── styles.css                  # 스타일시트
│
├── 📁 data/                        # 데이터 저장소 (자동 생성)
│   └── stocks.db                   # 종목 데이터베이스
│
├── 📁 config/                      # 설정 파일
│   └── requirements.txt            # Python 패키지 목록
│
├── 📁 scripts/                     # 유틸리티 스크립트
│   └── (사용자 정의 스크립트)
│
├── 📁 assets/                      # 에셋 파일
│   ├── COMPONENT_SPECS.tsx         # 컴포넌트 명세
│   └── (React 컴포넌트 등)
│
├── 📁 docs/                        # 📚 문서 모음
│   │
│   ├── 📁 api/                     # API 관련 문서
│   │   ├── API_ALTERNATIVES_COMPARISON.md
│   │   ├── API_INTEGRATION_GUIDE.md
│   │   ├── API_RESEARCH_NOTES.md
│   │   ├── OPENDART_API_DOCUMENTATION.md
│   │   ├── OPENAPI_SPECIFICATION.yaml
│   │   ├── opendart_openapi.yaml
│   │   ├── OpenDART_Postman_Collection.json
│   │   └── capitoltrades_snapshot.txt
│   │
│   ├── 📁 design/                  # 디자인 문서
│   │   ├── DESIGN_SYSTEM.md
│   │   ├── DESIGN_IMPROVEMENTS_SUMMARY.md
│   │   ├── DESIGN_TOKENS.css
│   │   ├── design-tokens.css
│   │   ├── components.css
│   │   └── login-redesign.html
│   │
│   ├── 📁 implementation/          # 구현 문서
│   │   ├── ARCHITECTURE.md
│   │   ├── IMPLEMENTATION.md
│   │   ├── IMPLEMENTATION_GUIDE.md
│   │   ├── IMPLEMENTATION_ROADMAP.md
│   │   ├── IMPLEMENTATION_SUMMARY.md
│   │   ├── TECH_STACK.md
│   │   ├── TECHNICAL_SPECIFICATIONS.md
│   │   ├── DEPLOYMENT.md
│   │   └── CACHING_STRATEGY.md
│   │
│   ├── 📁 references/              # 참고 자료
│   │   ├── DART_INTEGRATION_GUIDE.md
│   │   ├── DART_UX_DESIGN.md
│   │   ├── FINANCIAL_METRICS_REFERENCE.md
│   │   ├── KOREAN_STOCK_SEARCH_RESEARCH.md
│   │   ├── SCRAPER_IMPLEMENTATION.md
│   │   ├── SCRAPING_IMPLEMENTATION_GUIDE.md
│   │   ├── SCRAPING_SERVICE.md
│   │   └── STRATEGY_GUIDE.md
│   │
│   ├── DOCUMENTATION_INDEX.md      # 문서 색인
│   ├── EXECUTIVE_SUMMARY.md        # 요약 보고서
│   ├── QUICK_START.md              # 빠른 시작 가이드
│   ├── QUICK_START_GUIDE.md        # 상세 시작 가이드
│   ├── DELIVERY_SUMMARY.txt        # 배포 요약
│   └── FILES_OVERVIEW.txt          # 파일 개요
│
└── 📁 .claude/                     # Claude Code 설정
    ├── agents/
    ├── skills/
    ├── commands/
    └── settings.local.json

```

---

## 📋 주요 폴더 설명

### 1. `backend/` - 백엔드 소스코드
**핵심 비즈니스 로직이 위치한 폴더**

- **`api/`** - 외부 API 연동 (한국투자증권, DART 등)
- **`dart/`** - 금융감독원 DART API 전용 모듈
- **`database/`** - 데이터베이스 관리 (SQLite)
- **`trading/`** - 매매 전략 및 알고리즘
- **`scraper/`** - 웹 스크래핑 모듈
- **`news/`** - 뉴스 수집 및 분석
- **`telegram/`** - 텔레그램 알림

### 2. `frontend/` - 프론트엔드
**사용자 인터페이스**

- `index.html` - 메인 대시보드
- `dart_analysis.html` - DART 재무제표 분석 페이지
- `strategy-config.html` - 전략 설정 페이지
- JavaScript & CSS 파일

### 3. `docs/` - 문서
**모든 문서를 체계적으로 정리**

#### `docs/api/` - API 문서
- API 대안 비교
- DART API 문서
- OpenAPI 명세서
- Postman 컬렉션

#### `docs/design/` - 디자인 문서
- 디자인 시스템
- 디자인 토큰
- UI 컴포넌트 스타일

#### `docs/implementation/` - 구현 문서
- 아키텍처
- 기술 스택
- 구현 가이드
- 배포 전략

#### `docs/references/` - 참고 자료
- DART 통합 가이드
- 재무 지표 설명
- 스크래핑 가이드
- 전략 가이드

### 4. `data/` - 데이터 저장소
**런타임 데이터 (Git에서 제외)**

- `stocks.db` - 종목 데이터베이스 (자동 생성)
- 로그 파일
- 캐시 파일

### 5. `config/` - 설정 파일
- `requirements.txt` - Python 패키지 의존성
- 기타 설정 파일

### 6. `scripts/` - 유틸리티 스크립트
- 데이터 수집 스크립트
- 유지보수 스크립트
- 배포 스크립트

### 7. `assets/` - 정적 에셋
- 컴포넌트 명세
- 이미지, 아이콘
- React 컴포넌트 (선택적)

---

## 🚀 빠른 시작

### 1. 프로젝트 클론/다운로드
```bash
cd "주식 프로젝트"
```

### 2. 환경 설정
```bash
# .env 파일 생성 및 API 키 설정
DART_API_KEY=your_dart_api_key
KIS_APP_KEY=your_kis_app_key
KIS_APP_SECRET=your_kis_app_secret
TELEGRAM_BOT_TOKEN=your_telegram_token
```

### 3. 패키지 설치
```bash
pip install -r config/requirements.txt
```

### 4. 종목 데이터 수집
```bash
python backend/dart/collect_companies.py
```

### 5. 서버 실행
```bash
python run.py
```

### 6. 브라우저 접속
- 메인: http://localhost:5000
- DART 분석: http://localhost:5000/dart_analysis.html

---

## 📚 문서 네비게이션

### 처음 시작하는 경우
1. 📄 `README.md` - 프로젝트 개요
2. 📄 `docs/QUICK_START.md` - 빠른 시작
3. 📄 `docs/implementation/ARCHITECTURE.md` - 아키텍처 이해

### DART API 사용
1. 📄 `docs/references/DART_INTEGRATION_GUIDE.md` - DART 통합 가이드
2. 📄 `docs/api/OPENDART_API_DOCUMENTATION.md` - API 상세 문서
3. 📄 `docs/references/FINANCIAL_METRICS_REFERENCE.md` - 재무 지표

### 매매 전략 개발
1. 📄 `docs/references/STRATEGY_GUIDE.md` - 전략 가이드
2. 📄 `backend/trading/strategies.py` - 전략 소스코드

### 스크래핑 기능
1. 📄 `docs/references/SCRAPING_IMPLEMENTATION_GUIDE.md`
2. 📄 `backend/scraper/` - 스크래퍼 모듈

### 배포
1. 📄 `docs/implementation/DEPLOYMENT.md`
2. 📄 `docs/implementation/CACHING_STRATEGY.md`

---

## 🔧 개발 워크플로우

### 새로운 기능 추가
1. `backend/` 또는 `frontend/`에 코드 추가
2. `docs/implementation/`에 문서 작성
3. `config/requirements.txt` 업데이트 (필요시)
4. 테스트 실행
5. Git 커밋

### 문서 작성/수정
1. 적절한 `docs/` 하위 폴더 선택
2. Markdown 형식으로 작성
3. `docs/DOCUMENTATION_INDEX.md` 업데이트

### 새로운 API 통합
1. `backend/api/` 또는 새 모듈 폴더 생성
2. `docs/api/`에 API 문서 작성
3. `backend/app.py`에 Blueprint 등록

---

## 🗂️ 파일 명명 규칙

### 소스코드
- Python: `snake_case.py` (예: `dart_api_client.py`)
- JavaScript: `camelCase.js` (예: `dartAnalysis.js`)
- HTML: `kebab-case.html` (예: `dart-analysis.html`)

### 문서
- 대문자 + 언더스코어: `DOCUMENT_NAME.md`
- 카테고리별 접두사 권장:
  - API 관련: `API_*.md`
  - 구현 관련: `IMPLEMENTATION_*.md`
  - 디자인 관련: `DESIGN_*.md`

### 설정 파일
- 소문자: `.gitignore`, `requirements.txt`
- 숨김 파일: `.env`, `.claude/`

---

## 🚫 .gitignore 주요 항목

```
# 환경 변수
.env

# 데이터베이스
data/*.db
*.sqlite

# 로그
*.log
logs/

# 캐시
.cache/
.dart_cache/

# Python
__pycache__/
*.pyc

# 임시 파일
*.tmp
*.bak
```

---

## 📊 폴더별 파일 개수

```
backend/         : ~20 파일 (소스코드)
frontend/        : ~6 파일 (HTML, CSS, JS)
docs/            : ~40 파일 (문서)
  ├─ api/        : ~8 파일
  ├─ design/     : ~6 파일
  ├─ implementation/ : ~9 파일
  └─ references/ : ~8 파일
config/          : ~1 파일
```

**총 파일 수**: 약 70개 (문서 포함)

---

## 🎯 정리 효과

### Before (정리 전)
```
주식 프로젝트/
├── 50+ 파일이 루트에 혼재
├── .md, .css, .html, .txt 뒤섞임
└── 찾기 어려운 구조
```

### After (정리 후)
```
주식 프로젝트/
├── 📄 필수 파일만 루트에 (4개)
├── 📁 명확한 폴더 구조
├── 📁 docs/ 안에 체계적 분류
└── 🔍 쉬운 탐색
```

---

## 💡 팁

### 문서 찾기
```bash
# 특정 키워드가 포함된 문서 찾기
grep -r "DART" docs/

# API 관련 문서만 보기
ls docs/api/

# 구현 가이드 보기
ls docs/implementation/
```

### 프로젝트 탐색
1. **개요 파악**: `README.md`
2. **빠른 시작**: `docs/QUICK_START.md`
3. **상세 문서**: `docs/DOCUMENTATION_INDEX.md`에서 찾기

### 코드 네비게이션
- Backend 로직: `backend/`
- API 엔드포인트: `backend/app.py` & `backend/dart/dart_routes.py`
- UI: `frontend/`

---

**정리 완료일**: 2025-01-22
**구조 버전**: 2.0
**상태**: ✅ **완전히 정리됨**

이제 훨씬 깔끔하고 탐색하기 쉬운 프로젝트 구조입니다! 🎉

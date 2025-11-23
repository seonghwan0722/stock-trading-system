# 📈 주식 자동매매 시스템 with DART 재무제표 분석

**AI 기반 주식 자동매매 및 재무제표 분석 통합 플랫폼**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 프로젝트 개요

국내 주식 시장을 위한 **AI 기반 자동매매 시스템**과 **금융감독원 DART API를 활용한 재무제표 분석 플랫폼**을 통합한 올인원 솔루션입니다.

### 주요 기능

#### 1️⃣ **자동매매 시스템**
- 🤖 AI 기반 매수/매도 전략
- 📊 실시간 포트폴리오 관리
- 📱 텔레그램 알림
- 📰 뉴스 감성 분석
- 🌐 미국 정치인 거래 데이터 수집

#### 2️⃣ **DART 재무제표 분석** ⭐ NEW!
- 🔍 종목 검색 (자동완성)
- 📑 재무제표 조회 (재무상태표, 손익계산서, 현금흐름표)
- 📈 50가지 재무 지표 분석
- 💼 2,000+ 국내 상장 종목 지원
- 🎨 직관적인 UI/UX

---

## 🚀 빠른 시작

### 1. 환경 설정

**필수 요구사항:**
- Python 3.8+
- pip

**.env 파일 생성:**
```bash
# DART API (재무제표 분석용)
dart_api=your_dart_api_key

# 한국투자증권 API (자동매매용)
KIS_APP_KEY=your_kis_app_key
KIS_APP_SECRET=your_kis_app_secret
KIS_ACCOUNT_NO=your_account_number

# 텔레그램 (알림용)
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 2. 패키지 설치

```bash
pip install -r config/requirements.txt
```

### 3. 종목 데이터베이스 구축

```bash
# DART에서 전체 상장 종목 수집 (최초 1회)
python backend/dart/collect_companies.py
```

### 4. 서버 실행

```bash
python run.py
```

### 5. 브라우저 접속

- **메인 대시보드**: http://localhost:5000
- **DART 재무제표 분석**: http://localhost:5000/dart_analysis.html
- **전략 설정**: http://localhost:5000/strategy-config.html

---

## 📁 프로젝트 구조

```
주식 프로젝트/
├── backend/              # 백엔드 (Flask)
│   ├── dart/            # DART API 모듈
│   ├── database/        # 종목 DB
│   ├── trading/         # 매매 전략
│   ├── scraper/         # 웹 스크래핑
│   └── app.py           # Flask 메인
│
├── frontend/            # 프론트엔드
│   ├── index.html       # 메인 대시보드
│   ├── dart_analysis.html  # DART 분석 페이지
│   └── *.js, *.css
│
├── docs/                # 📚 문서
│   ├── api/            # API 문서
│   ├── design/         # 디자인 가이드
│   ├── implementation/ # 구현 문서
│   └── references/     # 참고 자료
│
├── data/                # 데이터 (자동 생성)
│   └── stocks.db       # 종목 DB
│
├── config/              # 설정
│   └── requirements.txt
│
└── README.md            # 이 파일
```

> 📖 상세 구조는 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)를 참조하세요.

---

## 🎨 주요 화면

### 1. DART 재무제표 분석
- **종목 검색**: 회사명, 종목코드, 초성 검색
- **자동완성**: 2글자 이상 입력 시 실시간 추천
- **재무 지표**: 총자산, 매출액, 영업이익, ROE 등
- **재무비율**: 수익성, 안정성, 활동성, 성장성 지표

### 2. 자동매매 대시보드
- **계좌 현황**: 잔고, 보유 종목
- **AI 추천**: 매수/매도 추천 종목
- **뉴스 요약**: AI 기반 시장 분석

### 3. 전략 설정
- **매수 전략**: 기술적 분석, 가치 투자, 모멘텀
- **매도 전략**: 손절/익절 자동화
- **리스크 관리**: 포지션 크기, 분산 투자

---

## 🔧 주요 기술 스택

### Backend
- **Flask** - Web Framework
- **SQLite** - 종목 데이터베이스
- **Requests** - HTTP 클라이언트
- **BeautifulSoup4** - 웹 스크래핑
- **Pandas** - 데이터 분석

### Frontend
- **HTML5 / CSS3** - UI
- **Vanilla JavaScript** - 로직
- **Fetch API** - AJAX 통신

### APIs
- **DART Open API** - 재무제표 데이터
- **한국투자증권 API** - 주식 매매
- **OpenAI API** - AI 분석 (선택)

---

## 📊 DART API 기능

### 제공 데이터
- ✅ 재무상태표 (Balance Sheet)
- ✅ 손익계산서 (Income Statement)
- ✅ 현금흐름표 (Cash Flow Statement)
- ✅ 배당 정보
- ✅ 주요 주주 정보
- ✅ 공시 목록

### 50가지 재무 지표
- **수익성**: ROE, ROA, 영업이익률, 순이익률 등
- **안정성**: 부채비율, 유동비율, 자기자본비율 등
- **활동성**: 총자산회전율, 재고회전율 등
- **성장성**: 매출증가율, 이익증가율 등
- **현금흐름**: FCF, 영업활동현금흐름 등

> 📖 상세 지표 설명: [docs/references/FINANCIAL_METRICS_REFERENCE.md](docs/references/FINANCIAL_METRICS_REFERENCE.md)

---

## 🛠️ API 엔드포인트

### DART API

**종목 검색:**
```http
GET /api/dart/stocks/search?q=삼성&limit=20
```

**재무제표 조회:**
```http
GET /api/dart/financials/{corp_code}?year=2023&report_type=11011
```

**시스템 상태:**
```http
GET /api/dart/status
```

### 자동매매 API

**계좌 조회:**
```http
GET /api/account/balance
```

**매수/매도:**
```http
POST /api/trading/buy
POST /api/trading/sell
```

> 📖 전체 API 문서: [docs/api/](docs/api/)

---

## 📚 문서

### 시작하기
- 📄 [빠른 시작 가이드](docs/QUICK_START.md)
- 📄 [프로젝트 구조](PROJECT_STRUCTURE.md)

### DART 재무제표 분석
- 📄 [DART 통합 가이드](docs/references/DART_INTEGRATION_GUIDE.md)
- 📄 [DART API 문서](docs/api/OPENDART_API_DOCUMENTATION.md)
- 📄 [재무 지표 설명](docs/references/FINANCIAL_METRICS_REFERENCE.md)

### 자동매매
- 📄 [전략 가이드](docs/references/STRATEGY_GUIDE.md)
- 📄 [아키텍처](docs/implementation/ARCHITECTURE.md)

### 개발
- 📄 [구현 가이드](docs/implementation/IMPLEMENTATION_GUIDE.md)
- 📄 [기술 스택](docs/implementation/TECH_STACK.md)
- 📄 [배포 가이드](docs/implementation/DEPLOYMENT.md)

---

## 💡 사용 예시

### Python에서 DART API 사용

```python
from backend.dart.dart_api_client import DartAPIClient

# 클라이언트 초기화
client = DartAPIClient(api_key='your_key')

# 회사 검색
results = client.search_company('삼성전자')
company = results['companies'][0]

# 재무제표 조회
financials = client.get_financial_statements(
    corp_code=company.corp_code,
    bsns_year='2023',
    reprt_code='11011'  # 사업보고서
)

# 재무 지표 분석
from backend.dart.dart_api_client import FinancialDataAnalyzer
analyzer = FinancialDataAnalyzer()
metrics = analyzer.extract_metrics(financials)
ratios = analyzer.calculate_ratios(metrics)

print(f"ROE: {ratios['roe']:.2f}%")
print(f"부채비율: {ratios['debt_ratio']:.2f}%")
```

### JavaScript에서 API 호출

```javascript
// 종목 검색
fetch('/api/dart/stocks/search?q=삼성')
  .then(res => res.json())
  .then(data => console.log(data.data));

// 재무제표 조회
fetch('/api/dart/financials/00126380?year=2023&report_type=11011', {
  headers: { 'Authorization': `Bearer ${token}` }
})
  .then(res => res.json())
  .then(data => console.log(data.metrics));
```

---

## 🔐 보안

- ✅ `.env` 파일로 API 키 관리
- ✅ JWT 기반 인증
- ✅ `.gitignore`로 민감 정보 제외
- ✅ API Rate Limiting
- ✅ Input Validation

---

## 🐛 문제 해결

### API 키 오류
```
Error: DART_API_KEY not configured
```
→ `.env` 파일에 `dart_api` 추가

### 종목 검색 결과 없음
```
Stock count: 0
```
→ `python backend/dart/collect_companies.py` 실행

### 재무제표 조회 실패
```
Error 013: No data found
```
→ 해당 연도/분기 보고서 미제출 (다른 연도 시도)

---

## 📈 향후 계획

- [ ] 차트 시각화 (Chart.js)
- [ ] 종목 비교 기능
- [ ] Excel/PDF 내보내기
- [ ] 모바일 반응형 개선
- [ ] 실시간 알림 (신규 공시)
- [ ] 백테스팅 기능
- [ ] 포트폴리오 추적

---

## ✅ 사용자 액션 아이템 (TODO)

### 🔴 즉시 필요한 작업

#### 1. DART API 키 발급 및 설정
**필요성**: 재무제표 조회 기능 사용을 위해 필수
**소요 시간**: 5분
**단계**:
1. https://opendart.fss.or.kr/ 접속
2. 회원가입 → 로그인
3. "오픈API 이용현황" → "인증키 신청"
4. `.env` 파일에 `dart_api=발급받은키` 추가

**완료 여부**: [✓] (이미 설정됨)

---

#### 2. Python 패키지 설치
**필요성**: 프로젝트 실행을 위한 의존성 설치
**소요 시간**: 2분
**명령어**:
```bash
pip install -r config/requirements.txt
```

**완료 여부**: [ ]

---

#### 3. 종목 데이터베이스 초기 구축
**필요성**: 종목 검색 기능 사용을 위해 필수 (최초 1회만)
**소요 시간**: 1-2분
**명령어**:
```bash
python backend/dart/collect_companies.py
```

**예상 결과**: `data/stocks.db` 생성, 2,000+ 종목 저장

**완료 여부**: [ ]

---

### 🟡 선택적 작업

#### 4. TDD 환경 설정 (pytest)
**필요성**: 테스트 주도 개발을 원하는 경우
**소요 시간**: 2분
**참조 문서**: `docs/TDD_SETUP_OPTIONS.md`

**설정 완료 항목**:
- [✓] pytest 프레임워크 선택
- [✓] 테스트 디렉토리 구조 생성 (`tests/unit`, `tests/integration`)
- [✓] `pytest.ini`, `.coveragerc` 설정 완료
- [✓] 샘플 테스트 파일 생성

**패키지 설치** (requirements.txt에 이미 포함됨):
```bash
pip install pytest pytest-flask pytest-cov pytest-mock pytest-asyncio
```

**테스트 실행**:
```bash
pytest                    # 모든 테스트
pytest -m unit           # 유닛 테스트만
pytest -m integration    # 통합 테스트만
```

**완료 여부**: [✓]

---

#### 5. 한국투자증권 API 설정 (자동매매용)
**필요성**: 실제 주식 매매를 원하는 경우만
**소요 시간**: 10-15분 (계좌 개설 별도)
**단계**:
1. 한국투자증권 계좌 개설
2. API 신청
3. `.env`에 `KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_ACCOUNT_NO` 추가

**완료 여부**: [ ]

---

#### 6. 텔레그램 봇 설정 (알림용)
**필요성**: 텔레그램으로 알림 받고 싶은 경우
**소요 시간**: 5분
**단계**:
1. Telegram에서 @BotFather 검색
2. `/newbot` 명령으로 봇 생성
3. 토큰 복사
4. `.env`에 `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` 추가

**완료 여부**: [ ]

---

### 🔵 개발 관련 작업

#### 7. Git 자동 커밋 시스템 사용법 숙지
**필요성**: 변경사항을 자동으로 GitHub에 저장
**위치**: `scripts/auto_commit.py`

**사용법**:
```bash
# 기본 사용 (자동 커밋 + 푸시)
python scripts/auto_commit.py

# 커밋 메시지 지정
python scripts/auto_commit.py -m "feat: 새 기능 추가"

# 커밋만 하고 푸시 안 함
python scripts/auto_commit.py --no-push
```

**완료 여부**: [ ]

---

#### 8. 첫 테스트 실행 (TDD 선택 시)
**필요성**: TDD 환경이 제대로 설정되었는지 확인
**단계**:
1. 테스트 디렉토리 생성: `mkdir tests tests/unit tests/integration`
2. 샘플 테스트 파일 생성
3. 테스트 실행: `pytest -v`

**완료 여부**: [ ]

---

## 🧪 테스트 필요 부분 (진단)

### 자동 진단: Claude가 확인할 수 있는 부분

#### ✅ 이미 확인됨
- [x] Git 저장소 초기화
- [x] GitHub 원격 저장소 연결 (`https://github.com/seonghwan0722/stock-trading-system`)
- [x] 프로젝트 폴더 구조 정리
- [x] 자동 커밋 스크립트 생성

#### ⏳ 사용자 확인 필요
- [ ] `.env` 파일에 `DART_API_KEY` 설정됨
- [ ] `data/stocks.db` 파일 생성됨 (종목 데이터 수집 완료)
- [ ] Python 패키지 설치 완료

---

### 수동 테스트 체크리스트

#### 기능 테스트

**1. 서버 실행 테스트**
```bash
python run.py
```
**기대 결과**: `Running on http://127.0.0.1:5000` 출력

**완료 여부**: [ ]

---

**2. DART 분석 페이지 접속**
```
http://localhost:5000/dart_analysis.html
```
**기대 결과**: 종목 검색창이 보임

**완료 여부**: [ ]

---

**3. 종목 검색 테스트**
- 검색창에 "삼성" 입력
- 자동완성 목록에서 "삼성전자" 클릭
- 재무 데이터 로딩

**기대 결과**: 총자산, 매출액 등 재무 지표 표시

**완료 여부**: [ ]

---

**4. API 직접 테스트**
```bash
curl "http://localhost:5000/api/dart/stocks/search?q=삼성&limit=10"
```
**기대 결과**: JSON 응답 with 삼성 관련 종목 목록

**완료 여부**: [ ]

---

**5. Git 자동 커밋 테스트**
```bash
# 파일 수정 후
python scripts/auto_commit.py -m "test: 자동 커밋 테스트"
```
**기대 결과**: 커밋 생성 및 GitHub 푸시 완료

**완료 여부**: [ ]

---

## 🤖 Claude 자동 처리 vs 사용자 결정 필요

### ✅ Claude가 자동으로 처리한 것
1. Git 저장소 초기화
2. GitHub 저장소 생성 및 첫 커밋
3. 프로젝트 폴더 구조 정리 (40+ 문서 분류)
4. 자동 커밋 스크립트 생성
5. TDD 가이드 문서 작성
6. README.md에 TODO 정리

### 🙋 사용자가 결정해야 할 것

#### 1. TDD 프레임워크 선택
**옵션**:
- A) pytest (추천 ⭐)
- B) unittest (Python 내장)
- C) TDD 하지 않음 (나중에 결정)

**선택**: _________

---

#### 2. 테스트 커버리지 목표
**옵션**:
- A) 80%+ (엄격)
- B) 60%+ (보통)
- C) 테스트 커버리지 신경 안 씀

**선택**: _________

---

#### 3. CI/CD 설정
**옵션**:
- A) GitHub Actions로 자동 테스트 설정
- B) 나중에 설정
- C) 필요 없음

**선택**: _________

---

#### 4. 자동 커밋 사용 방식
**옵션**:
- A) 매번 Claude가 자동으로 커밋 + 푸시
- B) 사용자가 명시적으로 요청할 때만
- C) Git Hook으로 파일 저장 시 자동 커밋

**선택**: _________

---

## 📝 다음 세션 시작 시 확인사항

Claude와 다음 세션 시작 시 아래 항목을 확인해주세요:

1. **완료된 TODO 항목**: 위에서 체크한 항목들
2. **결정 사항**: TDD 프레임워크, 커버리지 목표, CI/CD, 자동 커밋 방식
3. **발생한 문제**: 설치 오류, API 연결 실패 등
4. **다음 작업 요청**: 새 기능 추가, 버그 수정 등

---

## 🔗 관련 문서

- 📄 `NEXT_STEPS.md` - 빠른 시작 가이드 (3분)
- 📄 `docs/SETUP_VERIFICATION.md` - 상세 검증 체크리스트
- 📄 `docs/TDD_SETUP_OPTIONS.md` - TDD 환경 설정 가이드
- 📄 `PROJECT_STRUCTURE.md` - 프로젝트 폴더 구조
- 📄 `IMPLEMENTATION_COMPLETE.md` - 구현 완료 보고서

---

## 🤝 기여

프로젝트 개선 아이디어나 버그 리포트는 환영합니다!

1. Fork the Project
2. Create your Feature Branch
3. Commit your Changes
4. Push to the Branch
5. Open a Pull Request

---

## 📝 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

## 👨‍💻 개발자

**주식 자동매매 시스템 with DART 분석**
- Backend: Flask, Python
- Frontend: HTML, CSS, JavaScript
- Database: SQLite
- APIs: DART, 한국투자증권

---

## 📞 문의

- 📧 Email: your.email@example.com
- 💬 Issues: [GitHub Issues](https://github.com/yourusername/yourrepo/issues)

---

## 🙏 감사의 말

- **금융감독원** - DART Open API 제공
- **한국투자증권** - 증권 API 제공
- **OpenAI** - AI 분석 기능

---

**마지막 업데이트**: 2025-01-22
**버전**: 2.0.0
**상태**: ✅ Production Ready

---

> 💡 **Tip**: 처음 사용하신다면 [docs/QUICK_START.md](docs/QUICK_START.md)부터 시작하세요!


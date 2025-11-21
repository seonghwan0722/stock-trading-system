# 빠른 시작 가이드

## 📋 필수 요구사항

- Python 3.8 이상
- pip
- 인터넷 연결

## 🚀 설치 단계

### 1. 의존성 설치

```bash
# 프로젝트 디렉토리로 이동
cd "C:\Users\jasan\OneDrive\Desktop\25-1\주식 프로젝트"

# Python 패키지 설치
pip install -r requirements.txt
```

### 2. Playwright 브라우저 설치

StockNear 크롤링을 위해 필요합니다:

```bash
playwright install chromium
```

## 🎮 실행 방법

### 서버 시작

```bash
# 방법 1: 직접 실행
python -m backend.app

# 방법 2: 백엔드 디렉토리에서
cd backend
python app.py
```

서버가 시작되면 다음과 같은 메시지가 표시됩니다:
```
==================================================
주식 자동매매 시스템 시작
==================================================
백그라운드 작업 시작됨
 * Running on http://0.0.0.0:5000
```

### 웹 브라우저에서 접속

1. 브라우저를 열고 `http://localhost:5000` 접속
2. 로그인 (기본 계정 정보는 `.env` 파일 참조)
3. 상단 메뉴에서 **"기타"** 탭 클릭

## 🎯 기능 테스트

### 1. 정치인 주식 거래 (Capitol Trades)

**테스트 방법:**
1. "기타" 탭 클릭
2. 기본적으로 "🏛️ 정치인 주식" 서브탭이 활성화됨
3. "새로고침" 버튼 클릭
4. Nancy Pelosi 등의 거래 내역 확인

**예상 결과:**
- 거래 카드 목록 표시
- 정치인 이름, 종목, 거래일, 금액 표시
- 매수/매도 뱃지 색상 구분

### 2. StockNear 데이터

**테스트 방법:**
1. "📊 StockNear" 서브탭 클릭
2. "새로고침" 버튼 클릭
3. 로딩 완료 대기 (봇 감지 우회 중...)

**예상 결과:**
- 인기 종목 카드에 트렌딩 주식 표시
- 거래량 급증 종목 표시
- 내부자 거래 정보 표시

**주의:**
- Cloudflare 챌린지로 인해 30-60초 소요될 수 있음
- 실패 시 재시도

### 3. StockAnalysis

**테스트 방법:**
1. "📈 StockAnalysis" 서브탭 클릭
2. 검색창에 종목 심볼 입력 (예: `AAPL`)
3. "검색" 버튼 클릭

**예상 결과:**
- 주요 지표 카드에 메트릭스 표시
- 재무 정보 표시
- 밸류에이션 데이터 표시

### 4. ChartExchange

**테스트 방법:**
1. "📉 ChartExchange" 서브탭 클릭
2. 검색창에 종목 입력 (예: `NASDAQ:MNDR`)
3. "검색" 버튼 클릭

**예상 결과:**
- 기술적 분석 지표 표시
- 차트 패턴 목록 표시
- 거래 정보 표시

## 🔍 문제 해결

### 문제 1: "Module not found" 오류

**해결책:**
```bash
# requirements.txt 재설치
pip install -r requirements.txt --force-reinstall
```

### 문제 2: Playwright 브라우저 오류

**해결책:**
```bash
# 브라우저 재설치
playwright install --force chromium

# 시스템 의존성 설치 (Linux)
playwright install-deps
```

### 문제 3: "크롤링 오류" 메시지

**원인:**
- 대상 웹사이트 HTML 구조 변경
- Rate limit 초과
- 네트워크 연결 문제

**해결책:**
1. 인터넷 연결 확인
2. 몇 분 후 재시도
3. 로그 확인: 터미널/콘솔에서 에러 메시지 확인

### 문제 4: 데이터가 표시되지 않음

**확인 사항:**
1. 백엔드 서버가 실행 중인지 확인
2. 브라우저 개발자 도구(F12)에서 네트워크 오류 확인
3. 로그인 토큰이 유효한지 확인

## 📊 API 직접 테스트

로그인 후 토큰을 얻어서 API를 직접 테스트할 수 있습니다:

```bash
# 1. 로그인하여 토큰 받기
TOKEN="your_auth_token_here"

# 2. Capitol Trades 테스트
curl -H "Authorization: $TOKEN" \
  http://localhost:5000/api/scraper/capitol-trades

# 3. StockNear 테스트
curl -H "Authorization: $TOKEN" \
  http://localhost:5000/api/scraper/stocknear

# 4. StockAnalysis 테스트
curl -H "Authorization: $TOKEN" \
  http://localhost:5000/api/scraper/stock-analysis/AAPL

# 5. ChartExchange 테스트
curl -H "Authorization: $TOKEN" \
  http://localhost:5000/api/scraper/chart-exchange/nasdaq-mndr
```

## ⚠️ 주의사항

### 법적 고려사항
- 웹 스크래핑은 교육 목적으로만 사용
- 과도한 요청으로 서버에 부담 주지 않기
- 각 사이트의 이용약관 준수

### 성능 고려사항
- StockNear 크롤링은 시간이 오래 걸림 (30-60초)
- 동시에 여러 크롤링 요청하지 않기
- 캐싱 시스템 구현 권장 (향후 개선사항)

### 데이터 정확성
- 실시간 데이터가 아닐 수 있음
- HTML 구조 변경 시 스크래퍼 업데이트 필요
- 중요한 투자 결정에 사용하지 않기

## 📱 모바일 테스트

모바일 브라우저에서도 테스트 가능합니다:

1. 같은 네트워크에 연결된 모바일 기기 사용
2. PC의 IP 주소 확인: `ipconfig` (Windows) 또는 `ifconfig` (Mac/Linux)
3. 모바일 브라우저에서 `http://[PC_IP]:5000` 접속

## 🔧 개발자 모드

디버깅을 위해 개발자 모드로 실행:

```python
# backend/app.py 마지막 줄 수정
app.run(host='0.0.0.0', port=5000, debug=True)
```

**장점:**
- 코드 변경 시 자동 재시작
- 상세한 에러 메시지
- 개발자 도구 사용 가능

**주의:**
- 프로덕션 환경에서는 `debug=False` 사용

## 📖 추가 문서

- **전체 구현 가이드**: `SCRAPER_IMPLEMENTATION.md`
- **API 문서**: `API_ALTERNATIVES_COMPARISON.md`
- **기술 명세**: `TECHNICAL_SPECIFICATIONS.md`

## 🆘 지원

문제가 발생하면:
1. 터미널/콘솔의 에러 로그 확인
2. 브라우저 개발자 도구(F12) 확인
3. 문서 재확인

## ✅ 체크리스트

설정 완료 전에 확인:

- [ ] Python 3.8+ 설치됨
- [ ] `pip install -r requirements.txt` 실행됨
- [ ] `playwright install chromium` 실행됨
- [ ] `.env` 파일에 설정 확인
- [ ] 서버가 `http://localhost:5000`에서 실행 중
- [ ] 브라우저에서 로그인 가능
- [ ] "기타" 탭이 메뉴에 표시됨

모든 체크리스트를 완료하면 사용할 준비가 된 것입니다! 🎉

## 🚀 다음 단계

기본 기능 테스트 후:
1. 각 스크래퍼의 데이터 정확성 확인
2. 필요에 따라 HTML 선택자 조정
3. 캐싱 시스템 추가 (선택사항)
4. 데이터베이스 저장 구현 (선택사항)
5. 실시간 업데이트 추가 (선택사항)

Happy Scraping! 📈💹

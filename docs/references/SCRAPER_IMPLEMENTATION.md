# 웹 스크래핑 기능 구현 완료

## 개요

"기타" 탭에 4개의 주요 금융 데이터 소스에서 데이터를 크롤링하는 기능이 완전히 구현되었습니다.

## 구현된 기능

### 1. Capitol Trades (정치인 주식 거래)
- **URL**: https://www.capitoltrades.com/
- **기능**:
  - Nancy Pelosi를 포함한 미국 정치인들의 주식 거래 내역 조회
  - 매수/매도 유형별 필터링
  - 정치인별 필터링
  - 거래 금액, 날짜, 종목 정보 표시

### 2. StockNear (실시간 주식 데이터)
- **URL**: https://stocknear.com/
- **기능**:
  - 봇 감지 우회 (Playwright 사용)
  - Cloudflare 챌린지 자동 처리
  - 인기 종목 (Trending Stocks)
  - 거래량 급증 종목
  - 내부자 거래 정보

### 3. StockAnalysis (종합 분석)
- **URL**: https://stockanalysis.com/
- **기능**:
  - 주요 지표 (Market Cap, P/E Ratio, EPS 등)
  - 재무 정보
  - 밸류에이션 메트릭스
  - 종목 검색 기능

### 4. ChartExchange (차트 분석)
- **URL**: https://chartexchange.com/
- **기능**:
  - 기술적 분석 지표
  - 차트 패턴 인식
  - 거래 정보
  - 종목별 상세 분석

## 프로젝트 구조

```
주식 프로젝트/
├── frontend/
│   ├── index.html          # "기타" 탭 UI 추가됨
│   ├── styles.css          # 새로운 스타일 추가됨
│   └── script.js           # 크롤링 API 연동 함수들
├── backend/
│   ├── app.py              # 8개의 새로운 API 엔드포인트
│   └── scraper/
│       ├── __init__.py
│       ├── base_scraper.py               # 기본 스크래퍼 클래스
│       ├── capitol_trades_scraper.py     # Capitol Trades 크롤러
│       ├── stocknear_scraper.py          # StockNear 크롤러 (Playwright)
│       ├── stock_analysis_scraper.py     # StockAnalysis 크롤러
│       └── chart_exchange_scraper.py     # ChartExchange 크롤러
└── requirements.txt        # 새로운 의존성 추가됨
```

## API 엔드포인트

### Capitol Trades
```
GET /api/scraper/capitol-trades
GET /api/scraper/capitol-trades/{politician_slug}
```

### StockNear
```
GET /api/scraper/stocknear
```

### StockAnalysis
```
GET /api/scraper/stock-analysis
GET /api/scraper/stock-analysis/{symbol}
```

### ChartExchange
```
GET /api/scraper/chart-exchange
GET /api/scraper/chart-exchange/{symbol}
```

## 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. Playwright 브라우저 설치 (StockNear용)

```bash
playwright install chromium
```

### 3. 서버 실행

```bash
python -m backend.app
```

또는

```bash
cd backend
python app.py
```

### 4. 프론트엔드 접속

브라우저에서 `http://localhost:5000` 접속 후 로그인하여 "기타" 탭 클릭

## 새로 추가된 패키지

```
playwright==1.40.0     # StockNear 봇 우회용
selenium==4.16.0       # 백업 옵션
aiohttp==3.9.1         # 비동기 HTTP 요청
```

## 주요 기술

### 1. 기본 스크래핑
- `requests` + `BeautifulSoup4`: 일반 웹 스크래핑
- Rate limiting: 1초 대기
- User-Agent 스푸핑

### 2. 봇 감지 우회 (StockNear)
- `Playwright` 헤드리스 브라우저
- `webdriver` 속성 숨기기
- Cloudflare 챌린지 대기
- JavaScript 실행 후 데이터 추출

### 3. 비동기 처리
- `asyncio`를 사용한 비동기 스크래핑
- 동기 래퍼 함수로 Flask 통합

## 사용 예시

### 프론트엔드

```javascript
// Nancy Pelosi의 거래 내역 로드
loadPoliticianTrades();

// StockNear 데이터 로드
loadStockNearData();

// 특정 종목 분석 (예: AAPL)
searchStockAnalysis(); // input에 'AAPL' 입력 후

// 차트 데이터 검색 (예: NASDAQ:MNDR)
searchChartExchange(); // input에 'NASDAQ:MNDR' 입력 후
```

### API 호출 예시

```bash
# Capitol Trades - 모든 거래
curl -H "Authorization: YOUR_TOKEN" \
  http://localhost:5000/api/scraper/capitol-trades

# Capitol Trades - Nancy Pelosi
curl -H "Authorization: YOUR_TOKEN" \
  http://localhost:5000/api/scraper/capitol-trades/nancy-pelosi

# StockNear 데이터
curl -H "Authorization: YOUR_TOKEN" \
  http://localhost:5000/api/scraper/stocknear

# StockAnalysis - AAPL
curl -H "Authorization: YOUR_TOKEN" \
  http://localhost:5000/api/scraper/stock-analysis/AAPL

# ChartExchange - NASDAQ:MNDR
curl -H "Authorization: YOUR_TOKEN" \
  http://localhost:5000/api/scraper/chart-exchange/nasdaq-mndr
```

## UI 특징

### 서브 탭 네비게이션
- 4개의 서브 탭으로 구성
- 각 데이터 소스별로 독립적인 UI

### 정치인 주식 탭
- 정치인별 필터
- 거래 유형별 필터 (매수/매도)
- 거래 카드 형식 표시

### StockNear 탭
- 3개의 정보 카드 (인기 종목, 거래량, 내부자)
- 실시간 변동률 표시

### StockAnalysis 탭
- 검색 기능
- 3개의 정보 카드 (지표, 재무, 밸류에이션)
- 메트릭스 그리드 레이아웃

### ChartExchange 탭
- 검색 기능
- 3개의 정보 카드 (기술적, 패턴, 거래)
- 기술 지표 표시

## 스타일링

### CSS 변수 사용
```css
--primary-main
--success-dark / --danger-dark
--gray-xxx
```

### 반응형 디자인
- 모바일 최적화
- 768px 이하에서 1열 레이아웃

### 애니메이션
- 페이드인 효과
- 호버 효과
- 트랜지션

## 에러 핸들링

### 프론트엔드
- Loading 상태 표시
- 에러 메시지 표시
- 빈 데이터 처리

### 백엔드
- Try-catch 블록
- 로깅
- Graceful degradation

## 성능 최적화

### Rate Limiting
- 각 요청 사이 1초 대기
- 서버 부하 방지

### 캐싱 권장사항
- Redis 캐시 추가 가능
- 5-15분 TTL 권장

### 비동기 처리
- StockNear는 비동기로 처리
- 다른 요청 블로킹 방지

## 법적 고려사항

### robots.txt 준수
- Rate limiting 구현
- User-Agent 명시

### 데이터 사용
- 개인 사용 목적
- 상업적 재배포 금지

### 봇 감지 우회
- 교육 목적
- 윤리적 스크래핑 원칙 준수

## 알려진 제한사항

### Capitol Trades
- HTML 구조 변경 시 업데이트 필요
- 일부 데이터는 회원 전용

### StockNear
- Cloudflare 챌린지 시간 소요
- Playwright 메모리 사용량 높음
- 헤드리스 모드에서 CAPTCHA 어려움

### StockAnalysis
- 무료 데이터 제한
- 실시간 데이터 아님

### ChartExchange
- 일부 차트는 JavaScript 의존
- 이미지 차트는 OCR 필요

## 향후 개선 사항

### 1. 캐싱 시스템
```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@cache.memoize(timeout=300)
def get_capitol_trades():
    # ...
```

### 2. 백그라운드 작업
```python
from celery import Celery

celery = Celery('scraper')

@celery.task
def scrape_all_sources():
    # ...
```

### 3. 데이터베이스 저장
```python
# MongoDB or PostgreSQL에 저장
trades_collection.insert_many(trades)
```

### 4. 웹소켓 실시간 업데이트
```javascript
const socket = io();
socket.on('trades_update', (data) => {
    updateTradesUI(data);
});
```

### 5. 차트 시각화
```javascript
// Chart.js 또는 D3.js 사용
new Chart(ctx, {
    type: 'line',
    data: chartData
});
```

## 문제 해결

### Playwright 오류
```bash
# 브라우저 재설치
playwright install --force chromium
```

### Import 오류
```bash
# PYTHONPATH 설정
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Rate Limit 오류
- 요청 간격 늘리기
- User-Agent 변경
- IP 순환 (프록시)

## 개발자 정보

- **구현 일자**: 2025-11-21
- **Python 버전**: 3.8+
- **Flask 버전**: 3.0.0
- **Playwright 버전**: 1.40.0

## 라이센스

이 프로젝트는 교육 목적으로 제작되었습니다.

## 참고 자료

- [Playwright Documentation](https://playwright.dev/python/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Web Scraping Best Practices](https://www.scrapehero.com/web-scraping-best-practices/)

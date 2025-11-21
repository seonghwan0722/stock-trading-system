# DART API 통합 가이드

## 🎯 개요

금융감독원 Open DART API를 활용한 국내 상장 종목 재무제표 분석 시스템입니다.

## ✨ 주요 기능

### 1. 종목 검색
- **자동완성 검색**: 2글자 이상 입력 시 실시간 검색 결과 표시
- **다양한 검색 방식**:
  - 회사명 검색 (예: 삼성전자)
  - 종목코드 검색 (예: 005930)
  - 초성 검색 (예: ㅅㅅㅈㅈ)
- **시장 구분 표시**: KOSPI, KOSDAQ, KONEX

### 2. 재무제표 분석
- **재무상태표 (Balance Sheet)**
  - 총자산, 총부채, 총자본
  - 유동자산/비유동자산
  - 유동부채/비유동부채

- **손익계산서 (Income Statement)**
  - 매출액, 영업이익, 당기순이익
  - 매출총이익, 판관비
  - 영업외수익/비용

- **현금흐름표 (Cash Flow Statement)**
  - 영업활동 현금흐름
  - 투자활동 현금흐름
  - 재무활동 현금흐름

### 3. 재무비율 (50가지 주요 지표)
- **수익성 지표**: ROE, ROA, 매출총이익률, 영업이익률, 순이익률
- **안정성 지표**: 부채비율, 유동비율, 당좌비율, 자기자본비율
- **활동성 지표**: 총자산회전율, 재고자산회전율, 매출채권회전율
- **성장성 지표**: 매출액증가율, 영업이익증가율, 순이익증가율

## 🚀 설치 및 실행

### 1. 환경 설정

**.env 파일에 DART API 키 추가:**
```bash
DART_API_KEY=your_api_key_here
```

**API 키 발급 방법:**
1. https://opendart.fss.or.kr/ 접속
2. 회원가입 및 로그인
3. 인증키 신청/관리 → API 인증키 발급

### 2. 종목 데이터 수집

```bash
# 종목 데이터베이스 구축 (최초 1회 실행)
python backend/dart/collect_companies.py
```

**실행 결과:**
- `data/stocks.db` SQLite 데이터베이스 생성
- 약 2,000~3,000개 상장 종목 저장
- 실행 시간: 약 30초~1분

### 3. 서버 실행

```bash
# Flask 서버 시작
python run.py
```

서버가 시작되면:
- Main App: http://localhost:5000
- DART 분석: http://localhost:5000/dart_analysis.html

## 📡 API 엔드포인트

### 종목 검색 API

**모든 종목 조회**
```
GET /api/dart/stocks/all
Query: ?market=KOSPI (optional)

Response:
{
  "success": true,
  "data": [...],
  "count": 1234,
  "market_stats": {
    "KOSPI": 800,
    "KOSDAQ": 400
  }
}
```

**종목 검색**
```
GET /api/dart/stocks/search?q=삼성&limit=20

Response:
{
  "success": true,
  "data": [
    {
      "stock_code": "005930",
      "corp_code": "00126380",
      "company_name": "삼성전자",
      "market_type": "KOSPI"
    }
  ],
  "count": 5
}
```

**특정 종목 조회**
```
GET /api/dart/stocks/005930

Response:
{
  "success": true,
  "data": {
    "stock_code": "005930",
    "corp_code": "00126380",
    "company_name": "삼성전자",
    "market_type": "KOSPI"
  }
}
```

### 재무제표 API

**재무제표 조회**
```
GET /api/dart/financials/{corp_code}
Query:
  - year: 2023 (사업연도)
  - report_type: 11011 (11011:사업보고서, 11012:반기, 11013:3분기, 11014:1분기)
  - fs_div: 1001 (1001:연결, 1002:별도)

Response:
{
  "success": true,
  "company": {...},
  "financials": {...},
  "metrics": {
    "total_assets": 1000000000000,
    "revenue": 500000000000,
    ...
  },
  "ratios": {
    "gross_margin": 25.5,
    "operating_margin": 15.2,
    ...
  }
}
```

**이용 가능한 재무제표 목록**
```
GET /api/dart/financials/{corp_code}/available

Response:
{
  "success": true,
  "statements": [
    {
      "bsns_year": "2023",
      "reprt_code": "11011"
    }
  ]
}
```

### 기타 API

**배당 정보**
```
GET /api/dart/dividend/{stock_code}
```

**주요 주주 정보**
```
GET /api/dart/shareholders/{corp_code}?page=1&count=10
```

**시스템 상태**
```
GET /api/dart/status

Response:
{
  "api_configured": true,
  "database_ready": true,
  "stock_count": 2345,
  "last_update": "2025-01-21T10:30:00",
  "market_stats": {...}
}
```

## 📁 프로젝트 구조

```
주식 프로젝트/
├── backend/
│   ├── dart/
│   │   ├── __init__.py
│   │   ├── dart_api_client.py       # DART API 클라이언트
│   │   ├── dart_routes.py           # Flask Blueprint
│   │   └── collect_companies.py     # 종목 수집 스크립트
│   ├── database/
│   │   ├── __init__.py
│   │   └── stock_db.py              # SQLite DB 관리
│   └── app.py                       # Flask 앱
├── frontend/
│   ├── dart_analysis.html           # 재무제표 분석 UI
│   ├── dart_analysis.js             # JavaScript
│   └── styles.css
├── data/
│   └── stocks.db                    # 종목 데이터베이스
└── .env                            # 환경 변수
```

## 🔧 사용 예시

### 1. 종목 검색 및 선택

```javascript
// 종목 검색
fetch('/api/dart/stocks/search?q=삼성')
  .then(res => res.json())
  .then(data => console.log(data.data));
```

### 2. 재무제표 조회

```javascript
// 삼성전자 2023년 사업보고서
fetch('/api/dart/financials/00126380?year=2023&report_type=11011&fs_div=1001', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
  .then(res => res.json())
  .then(data => console.log(data.metrics));
```

### 3. Python에서 직접 사용

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
    reprt_code='11011'
)

# 재무 지표 분석
from backend.dart.dart_api_client import FinancialDataAnalyzer
analyzer = FinancialDataAnalyzer()
metrics = analyzer.extract_metrics(financials)
ratios = analyzer.calculate_ratios(metrics)

print(f"총자산: {metrics['total_assets']:,}원")
print(f"ROE: {ratios['roe']:.2f}%")
```

## 📊 50가지 재무 지표 목록

### 수익성 지표 (Profitability)
1. ROE (자기자본이익률)
2. ROA (총자산이익률)
3. ROIC (투하자본이익률)
4. 매출총이익률
5. 영업이익률
6. 순이익률
7. EBITDA 마진
8. 주당순이익 (EPS)
9. 주당배당금 (DPS)
10. 배당성향

### 안정성 지표 (Stability)
11. 부채비율
12. 자기자본비율
13. 유동비율
14. 당좌비율
15. 이자보상배율
16. 차입금의존도
17. 순차입금비율
18. 고정비율
19. 고정장기적합률
20. 현금비율

### 활동성 지표 (Activity)
21. 총자산회전율
22. 유동자산회전율
23. 고정자산회전율
24. 재고자산회전율
25. 매출채권회전율
26. 매입채무회전율
27. 운전자본회전율
28. 자기자본회전율
29. 현금전환주기
30. 순운전자본

### 성장성 지표 (Growth)
31. 매출액증가율 (YoY)
32. 영업이익증가율 (YoY)
33. 순이익증가율 (YoY)
34. 총자산증가율 (YoY)
35. 자기자본증가율 (YoY)
36. EPS증가율 (YoY)
37. 유형자산증가율
38. 3년 매출 CAGR
39. 3년 영업이익 CAGR
40. 3년 순이익 CAGR

### 현금흐름 지표 (Cash Flow)
41. 영업활동현금흐름
42. 투자활동현금흐름
43. 재무활동현금흐름
44. 잉여현금흐름 (FCF)
45. 현금창출능력
46. 영업활동현금/매출액
47. 영업활동현금/순이익
48. 배당커버리지
49. CAPEX/매출액
50. 현금전환율

## ⚠️ 주의사항

### API 사용 제한
- **일일 요청 한도**: 10,000건
- **초당 요청**: 제한 없음 (과도한 요청 자제)
- **캐싱**: 24시간 캐시 사용

### 데이터 업데이트
- 재무제표는 분기/반기/연간 보고서 기준
- 실시간 데이터가 아님
- 최신 데이터는 보고서 제출 후 반영

### 종목 DB 업데이트
```bash
# 정기적으로 실행하여 신규 상장 종목 반영
python backend/dart/collect_companies.py
```

## 🐛 트러블슈팅

### 1. API 키 오류
```
Error: DART_API_KEY not configured
```
→ `.env` 파일에 `DART_API_KEY` 설정 확인

### 2. 종목 검색 결과 없음
```
Stock count: 0
```
→ 종목 수집 스크립트 실행: `python backend/dart/collect_companies.py`

### 3. 재무제표 조회 실패
```
Error 013: No data found
```
→ 해당 연도/분기 보고서가 없거나 아직 제출되지 않음

## 📚 추가 리소스

- **DART API 문서**: https://opendart.fss.or.kr/guide/main.do
- **API 명세서**: OPENDART_API_DOCUMENTATION.md
- **UX 디자인**: DART_UX_DESIGN.md
- **재무 지표 설명**: FINANCIAL_METRICS_REFERENCE.md

## 🎓 학습 자료

### DART API 학습
1. 기본 개념 이해 (전자공시 시스템)
2. API 인증 및 호출
3. 재무제표 데이터 구조
4. 재무 지표 계산 방법

### 프로젝트 확장 아이디어
- 종목 비교 기능
- 업종 평균 비교
- 재무제표 차트 시각화
- PDF 리포트 생성
- 알림 설정 (신규 공시)

## 📞 지원

문제 발생 시:
1. 로그 확인: `backend/logs/`
2. API 상태 확인: `GET /api/dart/status`
3. GitHub Issues 등록

---

**작성일**: 2025-01-21
**버전**: 1.0.0
**작성자**: AI Assistant

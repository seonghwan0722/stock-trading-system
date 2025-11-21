# 🚀 다음 단계 - 빠른 시작 가이드

**프로젝트**: 주식 자동매매 시스템 with DART 재무제표 분석
**날짜**: 2025-01-22
**상태**: ✅ 구현 완료 → ⏳ 초기 설정 필요

---

## ⚡ 3분 안에 시작하기

### 1️⃣ DART API 키 설정 (1분)

```bash
# .env 파일 열기
notepad .env

# 또는
vim .env
```

**`.env` 파일에 추가**:
```
DART_API_KEY=발급받은_DART_API_키
```

**API 키 발급 방법**:
1. https://opendart.fss.or.kr/ 접속
2. 회원가입 → 로그인
3. "오픈API 이용현황" → "인증키 신청" 클릭
4. 발급된 키를 복사하여 `.env`에 붙여넣기

---

### 2️⃣ 패키지 설치 (1분)

```bash
pip install -r config/requirements.txt
```

**설치되는 주요 패키지**:
- Flask
- Requests
- python-dotenv
- BeautifulSoup4
- Pandas

---

### 3️⃣ 종목 데이터 수집 (1분)

```bash
python backend/dart/collect_companies.py
```

**예상 출력**:
```
🔍 DART 종목 수집 시작...
📥 ZIP 파일 다운로드 중...
📦 XML 파싱 중...
💾 데이터베이스 저장 중...
✅ 2,156개 종목 저장 완료!
```

이 과정은 **최초 1회만** 실행하면 됩니다.
데이터는 `data/stocks.db`에 저장됩니다.

---

### 4️⃣ 서버 실행

```bash
python run.py
```

**예상 출력**:
```
 * Running on http://127.0.0.1:5000
 * Restarting with stat
 * Debugger is active!
```

---

### 5️⃣ 브라우저 접속

**DART 재무제표 분석**:
```
http://localhost:5000/dart_analysis.html
```

**메인 대시보드**:
```
http://localhost:5000
```

---

## 🧪 기능 테스트

### ✅ 테스트 1: 종목 검색

1. `dart_analysis.html` 페이지 접속
2. 검색창에 "**삼성**" 입력 (2글자 이상)
3. 자동완성 목록 확인
4. "삼성전자" 클릭

**예상 결과**: 삼성전자의 재무 데이터가 화면에 표시됨

---

### ✅ 테스트 2: 재무제표 조회

1. 종목 선택 후 연도 선택 (예: 2023)
2. 보고서 유형 선택 (예: 사업보고서)
3. "재무상태표" 탭 클릭

**예상 결과**:
- 총자산, 총부채, 총자본 등 표시
- 매출액, 영업이익, 당기순이익 등 표시

---

### ✅ 테스트 3: 재무비율 확인

1. "재무비율" 탭 클릭

**예상 결과**:
- 매출총이익률
- 영업이익률
- 순이익률
- 부채비율
- 자기자본비율
- 유동비율
- 부채자본비율

---

### ✅ 테스트 4: API 직접 호출

**종목 검색 API**:
```bash
curl "http://localhost:5000/api/dart/stocks/search?q=삼성&limit=10"
```

**예상 응답**:
```json
{
  "success": true,
  "data": [
    {
      "stock_name": "삼성전자",
      "stock_code": "005930",
      "corp_code": "00126380",
      "market": "KOSPI"
    },
    ...
  ],
  "count": 10
}
```

**시스템 상태 확인**:
```bash
curl "http://localhost:5000/api/dart/status"
```

---

## 🐛 자주 발생하는 문제

### ❌ "DART_API_KEY not configured"

**해결**:
```bash
# .env 파일 확인
cat .env

# DART_API_KEY가 있는지 확인
# 없으면 추가:
echo "DART_API_KEY=your_key_here" >> .env
```

---

### ❌ "No module named 'flask'"

**해결**:
```bash
pip install -r config/requirements.txt
```

---

### ❌ 종목 검색 결과 0개

**해결**:
```bash
# 데이터베이스 확인
ls -lh data/stocks.db

# 파일이 없거나 크기가 0이면:
python backend/dart/collect_companies.py
```

---

### ❌ "No data found" (재무제표 조회 실패)

**원인**: 해당 연도/분기 보고서 미제출

**해결**:
- 다른 연도 시도 (2022, 2021, 2020 등)
- 다른 보고서 유형 시도:
  - 11011: 사업보고서 (연간)
  - 11012: 반기보고서
  - 11013: 3분기보고서

---

## 📚 추가 문서

**필독 문서**:
1. 📄 `README.md` - 프로젝트 전체 개요
2. 📄 `PROJECT_STRUCTURE.md` - 폴더 구조 설명
3. 📄 `docs/SETUP_VERIFICATION.md` - 상세 검증 체크리스트

**DART 관련**:
1. 📁 `docs/references/DART_INTEGRATION_GUIDE.md` - DART 통합 가이드
2. 📁 `docs/api/OPENDART_API_DOCUMENTATION.md` - API 상세 문서
3. 📁 `docs/references/FINANCIAL_METRICS_REFERENCE.md` - 재무 지표 설명

**기술 문서**:
1. 📁 `docs/implementation/ARCHITECTURE.md` - 시스템 아키텍처
2. 📁 `docs/implementation/TECH_STACK.md` - 기술 스택 상세
3. 📁 `docs/implementation/DEPLOYMENT.md` - 배포 가이드

---

## 🎯 구현 완료 기능

### ✅ 종목 검색 시스템
- [x] 회사명 검색
- [x] 종목코드 검색
- [x] 자동완성 (2글자 이상)
- [x] SQLite 데이터베이스
- [x] 2,000+ 국내 상장 종목 지원
- [x] 300ms 디바운스 최적화

### ✅ 재무제표 분석
- [x] DART API 클라이언트
- [x] 재무상태표 (BS)
- [x] 손익계산서 (IS)
- [x] 현금흐름표 (CF)
- [x] 50가지 지표 프레임워크
- [x] 7개 핵심 지표 표시
- [x] 7개 재무비율 표시

### ✅ API 엔드포인트
- [x] 15개 RESTful API
- [x] JWT 인증
- [x] Rate Limiting
- [x] Response Caching (24시간 TTL)
- [x] 에러 핸들링

### ✅ 프로젝트 구조
- [x] 폴더 정리 (9개 항목만 루트에)
- [x] 문서 분류 (docs/ 4개 서브폴더)
- [x] .gitignore 설정
- [x] 종합 문서 작성

---

## 🚀 다음 확장 계획 (선택 사항)

### 🔜 UI 개선
- [ ] Chart.js 차트 시각화
- [ ] 로딩 스피너
- [ ] 반응형 모바일 디자인
- [ ] 다크 모드

### 🔜 기능 추가
- [ ] 종목 비교 (2-3개)
- [ ] Excel 내보내기
- [ ] PDF 보고서 생성
- [ ] 업종 평균 비교

### 🔜 고급 기능
- [ ] 실시간 공시 알림
- [ ] 포트폴리오 관리
- [ ] AI 재무 분석 (GPT)
- [ ] 백테스팅

---

## 💡 팁

### 개발 모드 실행
```bash
# Flask 디버그 모드로 실행
export FLASK_ENV=development
python run.py
```

### 데이터베이스 확인
```bash
# SQLite CLI로 종목 수 확인
sqlite3 data/stocks.db "SELECT COUNT(*) FROM stocks;"

# 삼성 관련 종목 조회
sqlite3 data/stocks.db "SELECT * FROM stocks WHERE stock_name LIKE '%삼성%' LIMIT 10;"
```

### 로그 확인
```bash
# Flask 서버 로그
tail -f backend/logs/app.log
```

### 캐시 초기화
```bash
# DART API 캐시 삭제
rm -rf .dart_cache/

# 또는 API 호출
curl -X POST "http://localhost:5000/api/dart/cache/clear" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## ✅ 최종 체크리스트

시작하기 전 확인:

- [ ] Python 3.8+ 설치됨
- [ ] `.env` 파일에 `DART_API_KEY` 설정됨
- [ ] `pip install -r config/requirements.txt` 실행됨
- [ ] `python backend/dart/collect_companies.py` 실행됨
- [ ] `data/stocks.db` 파일 생성됨
- [ ] `python run.py` 서버 실행 중
- [ ] `http://localhost:5000/dart_analysis.html` 접속 확인

---

## 🎉 완료!

모든 단계를 완료했다면 DART 재무제표 분석 시스템을 사용할 준비가 되었습니다!

**질문이나 문제가 있다면**:
1. `docs/SETUP_VERIFICATION.md` 참조
2. 프로젝트 문서 확인
3. DART 공식 문서 참조: https://opendart.fss.or.kr/

---

**행운을 빕니다!** 🚀📈

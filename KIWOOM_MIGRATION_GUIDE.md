# 키움증권 OpenAPI 마이그레이션 가이드

한국투자증권에서 키움증권 OpenAPI+로의 전환 가이드입니다.

---

## 📋 변경 사항 요약

### 1. API 방식 변경
- **이전**: 한국투자증권 REST API (HTTP 기반)
- **이후**: 키움증권 OpenAPI+ (Active-X 기반)

### 2. 주요 차이점

| 항목 | 한국투자증권 | 키움증권 |
|------|------------|---------|
| 방식 | REST API | Active-X COM |
| 플랫폼 | 멀티 플랫폼 | Windows 전용 |
| 인증 | OAuth 2.0 | 자동 로그인 |
| 통신 | 동기 HTTP | 이벤트 기반 비동기 |
| 배포 | 서버 배포 가능 | 로컬 환경만 가능 |
| 실시간 | WebSocket | 내장 이벤트 |
| 라이브러리 | requests | PyQt5 |

---

## 🔧 설치 및 설정

### 1. 키움증권 OpenAPI+ 설치

**필수 사전 작업**:
1. [키움증권 홈페이지](https://www.kiwoom.com/)에서 KOA Studio 다운로드
2. OpenAPI+ 모듈 설치
3. 모의투자 또는 실계좌 신청

**설치 경로 확인**:
```
C:\OpenAPI\
```

### 2. Python 패키지 설치

```bash
# 기본 패키지 업데이트
pip install -r config/requirements.txt

# 또는 개별 설치
pip install PyQt5==5.15.10
pip install PyQtWebEngine==5.15.6
```

### 3. 환경 변수 설정 (.env)

```env
# 키움증권 OpenAPI 설정
KIWOOM_ACCOUNT_NO=1234567890  # 계좌번호 (10자리)
KIWOOM_USER_ID=your_id        # 로그인 ID (선택사항 - 자동 로그인용)
KIWOOM_USER_PW=your_pw        # 로그인 PW (선택사항 - 자동 로그인용)
```

---

## 📝 코드 변경 가이드

### Step 1: backend/app.py 수정

**Before** (한국투자증권):
```python
from api.kis_api import KISApi

kis_api = KISApi()
```

**After** (키움증권):
```python
from api.kiwoom_api import KiwoomAPI, get_kiwoom_api

kiwoom_api = get_kiwoom_api()  # 싱글톤 인스턴스
```

### Step 2: API 호출 부분 전체 변경

**계좌 정보 조회**:
```python
# Before
result = kis_api.get_balance()

# After
result = kiwoom_api.get_balance()
```

**현재가 조회**:
```python
# Before
price = kis_api.get_current_price('005930')

# After
price = kiwoom_api.get_current_price('005930')
```

**매수 주문**:
```python
# Before
result = kis_api.buy_stock('005930', 10, 70000)

# After
result = kiwoom_api.buy_stock('005930', 10, 70000)
```

**매도 주문**:
```python
# Before
result = kis_api.sell_stock('005930', 10, 70000)

# After
result = kiwoom_api.sell_stock('005930', 10, 70000)
```

### Step 3: app.py 전체 변경 스크립트

다음 명령어로 일괄 변경:

```bash
# app.py에서 kis_api를 kiwoom_api로 변경
# Windows PowerShell
(Get-Content backend/app.py) -replace 'kis_api', 'kiwoom_api' | Set-Content backend/app.py
(Get-Content backend/app.py) -replace 'from api.kis_api import KISApi', 'from api.kiwoom_api import KiwoomAPI, get_kiwoom_api' | Set-Content backend/app.py
(Get-Content backend/app.py) -replace 'kis_api = KISApi\(\)', 'kiwoom_api = get_kiwoom_api()' | Set-Content backend/app.py
```

또는 수동으로:
1. 모든 `kis_api` → `kiwoom_api` 변경
2. import 문 변경
3. 초기화 부분 변경

---

## 🚀 실행 가이드

### 1. 로그인

키움증권 API는 처음 실행 시 자동으로 로그인 창이 표시됩니다.

```python
# backend/app.py 또는 별도 로그인 스크립트
from api.kiwoom_api import get_kiwoom_api

kiwoom = get_kiwoom_api()

# 로그인 (GUI 창이 표시됨)
if kiwoom.comm_connect():
    print("로그인 성공!")
    print(f"계좌 목록: {kiwoom.account_list}")
else:
    print("로그인 실패")
```

### 2. Flask 앱 실행

**주의**: 키움 API는 Windows 환경에서만 동작합니다.

```bash
# 일반 실행
python backend/app.py

# 디버그 모드
$env:FLASK_DEBUG="True"
python backend/app.py
```

### 3. 제약 사항

키움증권 OpenAPI+의 제한사항:
- ✅ Windows 전용 (Linux/Mac 불가)
- ✅ 로컬 환경에서만 실행 가능
- ✅ 서버 배포 불가 (AWS, Azure 등)
- ✅ 1초당 TR 요청 5회 제한
- ✅ GUI 로그인 필수 (자동 로그인 가능하나 보안 이슈)

---

## 🔍 API 주요 변경 사항

### 1. 현재가 조회

**한국투자증권 (REST)**:
```python
response = requests.get(
    f"{base_url}/uapi/domestic-stock/v1/quotations/inquire-price",
    headers=headers,
    params={"FID_INPUT_ISCD": stock_code}
)
```

**키움증권 (TR)**:
```python
kiwoom.set_input_value("종목코드", stock_code)
kiwoom.comm_rq_data("주식기본정보", "OPT10001", 0, "0101")
# 이벤트 기반으로 결과 수신
```

### 2. 계좌 잔고 조회

**한국투자증권**:
- TR: `TTTC8434R`
- 단일 API 호출

**키움증권**:
- TR: `OPW00018` (잔고), `OPW00001` (예수금)
- 2개의 TR 요청 필요

### 3. 주문

**한국투자증권**:
- HTTP POST 요청
- 응답 즉시 반환

**키움증권**:
- `SendOrder()` 함수 호출
- 체결 이벤트 대기
- 비동기 콜백으로 결과 수신

---

## 📊 TR 코드 참고표

| 기능 | TR 코드 | 설명 |
|------|---------|------|
| 주식 현재가 | OPT10001 | 주식기본정보 |
| 계좌평가잔고 | OPW00018 | 계좌평가잔고내역 |
| 예수금 | OPW00001 | 예수금상세현황 |
| 일봉 차트 | OPT10081 | 주식일봉차트조회 |
| 분봉 차트 | OPT10080 | 주식분봉차트조회 |
| 주문 | - | SendOrder() 함수 |

전체 TR 코드: [KOA Studio](https://www3.kiwoom.com/nkw.templateFrameSet.do?m=m1408000000) 참고

---

## 🧪 테스트

### 1. 연결 테스트

```python
from api.kiwoom_api import get_kiwoom_api

kiwoom = get_kiwoom_api()

# 연결 상태 확인
if kiwoom.get_connect_state() == 1:
    print("✅ 키움 API 연결됨")
else:
    print("❌ 연결 안됨 - 로그인 필요")
    kiwoom.comm_connect()
```

### 2. 현재가 조회 테스트

```python
# 삼성전자 현재가
price_info = kiwoom.get_current_price('005930')
print(f"현재가: {price_info['current_price']:,}원")
print(f"등락율: {price_info['change_rate']}%")
```

### 3. 계좌 조회 테스트

```python
balance = kiwoom.get_balance()
print(f"예수금: {balance['cash_balance']:,}원")
print(f"보유 종목 수: {len(balance['positions'])}")
```

### 4. 단위 테스트 실행

```bash
pytest tests/unit/test_kiwoom_api.py -v
```

---

## ⚠️ 주의 사항

### 1. TR 요청 제한
- **초당 5회** 제한
- 초과 시 `OP_ERR_RQ_OVERLOAD` 에러
- 해결: 각 요청 사이에 `time.sleep(0.2)` 추가

```python
price1 = kiwoom.get_current_price('005930')
time.sleep(0.2)  # 200ms 대기
price2 = kiwoom.get_current_price('000660')
```

### 2. 이벤트 루프
- PyQt5 이벤트 루프가 필요
- Flask 앱과 동시 실행 시 스레드 관리 필요

### 3. 로그인
- 처음 실행 시 로그인 창 표시
- 자동 로그인 가능하나 보안 위험
- 모의투자 계좌 권장 (실계좌 주의)

### 4. 윈도우 전용
- Linux/Mac에서 실행 불가
- Docker 배포 불가
- WSL(Windows Subsystem for Linux) 불가

---

## 🔄 롤백 가이드

키움증권으로 변경 후 문제 발생 시 한국투자증권으로 롤백:

### 1. app.py 복원

```python
# 다시 한국투자증권 사용
from api.kis_api import KISApi

kis_api = KISApi()
```

### 2. 모든 API 호출 복원

```bash
# kiwoom_api를 kis_api로 변경
(Get-Content backend/app.py) -replace 'kiwoom_api', 'kis_api' | Set-Content backend/app.py
```

### 3. .env 환경 변수 복원

```env
# 한국투자증권 설정
KIS_APP_KEY=your_app_key
KIS_APP_SECRET=your_app_secret
KIS_CANO=12345678
KIS_ACNT_PRDT_CD=01
```

---

## 📚 추가 리소스

### 공식 문서
- [키움증권 OpenAPI+ 가이드](https://www3.kiwoom.com/nkw.templateFrameSet.do?m=m1408000000)
- [KOA Studio 다운로드](https://www3.kiwoom.com/nkw.templateFrameSet.do?m=m1408010000)
- [PyQt5 문서](https://www.riverbankcomputing.com/static/Docs/PyQt5/)

### 커뮤니티
- [키움 OpenAPI 네이버 카페](https://cafe.naver.com/kiwoomapi)
- [Python 키움증권 GitHub](https://github.com/search?q=kiwoom+python)

### 예제 코드
- [backend/api/kiwoom_api.py](backend/api/kiwoom_api.py) - 구현 코드
- [tests/unit/test_kiwoom_api.py](tests/unit/test_kiwoom_api.py) - 테스트 코드

---

## 🎯 체크리스트

변경 작업 완료 확인:

- [ ] KOA Studio 설치 완료
- [ ] PyQt5, PyQtWebEngine 설치
- [ ] .env 파일에 키움증권 설정 추가
- [ ] backend/app.py import 변경
- [ ] 모든 kis_api → kiwoom_api 변경
- [ ] 로그인 테스트 성공
- [ ] 현재가 조회 테스트
- [ ] 계좌 조회 테스트
- [ ] 단위 테스트 통과
- [ ] 실제 거래 전 모의투자 확인

---

## 💬 FAQ

### Q: 키움 API를 서버에 배포할 수 있나요?
**A**: 아니요. Active-X 기반이라 Windows 로컬 환경에서만 동작합니다. 클라우드 배포가 필요하면 한국투자증권 REST API를 사용하세요.

### Q: Mac/Linux에서 사용 가능한가요?
**A**: 불가능합니다. Windows 전용입니다. 대안으로 한국투자증권 API 사용을 권장합니다.

### Q: Docker로 배포할 수 있나요?
**A**: 불가능합니다. Active-X 컨트롤이 필요하여 컨테이너 환경에서 실행 불가합니다.

### Q: 자동 로그인은 어떻게 하나요?
**A**: 보안상 권장하지 않습니다. 필요 시 별도 문의 바랍니다.

### Q: TR 요청이 너무 느려요.
**A**: 초당 5회 제한 때문입니다. 각 요청 사이에 0.2초 딜레이를 추가하세요.

### Q: 실시간 데이터는 어떻게 받나요?
**A**: `SetRealReg()` 함수로 실시간 등록 후 `OnReceiveRealData` 이벤트로 수신합니다. (현재 미구현)

---

**변경 일자**: 2025-11-23
**작성자**: Claude Code
**버전**: 1.0.0

# 키움 증권 OpenAPI 설정 가이드

키움 증권 OpenAPI를 사용하여 실제 주식 매매를 자동화할 수 있습니다.

## 📋 요구사항

### 1. 운영체제
- **Windows 7/8/10/11** (32bit 또는 64bit)
- ⚠️ **macOS, Linux는 지원하지 않습니다**

### 2. 소프트웨어
- Python 3.8 이상
- PyQt5 (자동 설치됨)

### 3. 계좌
- 키움증권 계좌 (실계좌 또는 모의투자 계좌)

---

## 🚀 설치 단계

### 1단계: 키움증권 계좌 개설

#### 실계좌 개설
1. [키움증권 홈페이지](https://www.kiwoom.com) 접속
2. 계좌 개설 신청
3. 본인 인증 및 서류 제출
4. 계좌 개설 완료 (약 1-2일 소요)

#### 모의투자 계좌 신청 (추천)
1. [키움 모의투자 페이지](https://www1.kiwoom.com/nkw.templateFrameSet.do?m=m1408030000) 접속
2. 키움증권 아이디로 로그인
3. 모의투자 신청
4. 즉시 사용 가능 (초기 자금 5,000만원)

---

### 2단계: 키움 OpenAPI+ 설치

1. **OpenAPI+ 다운로드**
   - [키움 OpenAPI+ 다운로드 페이지](https://www1.kiwoom.com/nkw.templateFrameSet.do?m=m1408000000)
   - "OpenAPI+ KHOpenAPI.ocx" 다운로드

2. **설치 실행**
   ```
   다운로드한 파일 실행 → 설치 진행 → 완료
   ```

3. **버전처리 관리자 실행**
   - OpenAPI+ 폴더에서 "KOAStudio.exe" 실행
   - 최신 버전으로 업데이트

4. **API 등록 확인**
   - 작업 표시줄에 OpenAPI 아이콘이 있는지 확인

---

### 3단계: Python 패키지 설치

```bash
# PyQt5 설치
pip install PyQt5==5.15.10

# 또는 requirements.txt로 일괄 설치
pip install -r config/requirements.txt
```

---

### 4단계: 로그인 및 인증서 등록

1. **키움 영웅문 실행**
   - 키움증권 홈페이지에서 영웅문 다운로드 및 설치
   - 영웅문 실행 후 로그인

2. **인증서 등록**
   - 도구 → 인증센터 → 인증서 등록
   - 공인인증서 등록 (필수)

3. **OpenAPI 비밀번호 설정**
   - 도구 → 시스템 → OpenAPI 비밀번호 설정
   - 자동 로그인용 비밀번호 설정 (선택사항)

---

## 💻 코드 사용 예제

### 기본 연결 및 로그인

```python
from backend.api.kiwoom_client import KiwoomClient

# 실제 API 사용 (Windows 전용)
client = KiwoomClient(simulation_mode=False)
result = client.connect()

if result['success']:
    print(f"로그인 성공: {result['user_name']}")
    print(f"계좌목록: {result['accounts']}")
else:
    print(f"로그인 실패: {result['message']}")
```

### 시뮬레이션 모드 (테스트용)

```python
from backend.api.kiwoom_client import get_kiwoom_client

# 시뮬레이션 모드 (모든 OS에서 실행 가능)
client = get_kiwoom_client(simulation_mode=True)
result = client.connect()
print(result)
```

### 주식 매수/매도

```python
# 삼성전자 10주 매수 (지정가 70,000원)
buy_result = client.buy_stock("005930", 10, 70000, "지정가")
print(buy_result)

# 삼성전자 10주 매도 (시장가)
sell_result = client.sell_stock("005930", 10, 0, "시장가")
print(sell_result)
```

### 현재가 조회

```python
# 삼성전자 시세 조회
price = client.get_stock_price("005930")
print(f"현재가: {price['current_price']}원")
print(f"등락률: {price['change_rate']}%")
```

### 계좌 정보 조회

```python
# 계좌 잔고 및 보유 종목 조회
account_info = client.get_account_info()
print(f"총 평가금액: {account_info['total_balance']:,}원")

for position in account_info['positions']:
    print(f"{position['stock_name']}: {position['quantity']}주")
```

---

## 🔧 실시간 데이터 및 고급 기능

### 실시간 시세 구독

```python
from backend.api.kiwoom_realtime import KiwoomRealtimeAPI, KiwoomOrderManager

# 실시간 API 초기화
realtime_api = KiwoomRealtimeAPI(client.api.ocx)

# 실시간 시세 콜백 함수
def on_price_update(code, data):
    print(f"{code}: {data['current_price']}원")

# 삼성전자, SK하이닉스 실시간 시세 구독
realtime_api.subscribe_realtime_price(["005930", "000660"], on_price_update)

# 구독 해제
realtime_api.unsubscribe_realtime_price(["005930"])
```

### 주문 관리

```python
# 주문 관리자 생성
order_manager = KiwoomOrderManager(client)

# 시장가 매수
order_manager.place_market_buy("005930", 10)

# 지정가 매도
order_manager.place_limit_sell("005930", 10, 75000)

# 미체결 주문 조회
pending_orders = order_manager.get_pending_orders()

# 주문 취소
order_manager.cancel_order("12345678")
```

---

## ⚠️ 주의사항

### 1. API 사용 제한
- 초당 최대 5회 조회 (과도한 요청 시 차단)
- 일일 조회 제한: 1,000회
- 실시간 데이터: 최대 100종목

### 2. 거래 시간
- 평일 09:00 ~ 15:30 (장 운영 시간)
- 시간외 거래: 08:30 ~ 09:00, 15:40 ~ 16:00

### 3. 보안
- **절대 API 키나 계좌번호를 코드에 직접 입력하지 마세요**
- 환경변수(.env)를 사용하세요
- 실계좌 사용 시 각별히 주의하세요

### 4. 모의투자 권장
- 처음 사용 시 **반드시 모의투자로 테스트**하세요
- 전략 검증 후 실계좌 사용을 권장합니다

---

## 🐛 문제 해결

### "연결 실패" 오류
1. OpenAPI+ 설치 확인
2. 영웅문 로그인 확인
3. 인증서 등록 확인
4. 방화벽 설정 확인

### "PyQt5 ImportError"
```bash
pip uninstall PyQt5
pip install PyQt5==5.15.10
```

### "OCX 등록 오류"
- 관리자 권한으로 OpenAPI+ 재설치
- Windows 재부팅 후 재시도

### "로그인 실패"
- 키움증권 아이디/비밀번호 확인
- 인증서 유효기간 확인
- 모의투자 신청 여부 확인

---

## 📚 참고 자료

- [키움 OpenAPI+ 개발가이드](https://www3.kiwoom.com/nkw.templateFrameSet.do?m=m1408020200)
- [키움 OpenAPI 함수 목록](https://download.kiwoom.com/web/openapi/kiwoom_openapi_plus_devguide_ver_1.5.pdf)
- [키움 모의투자 FAQ](https://www1.kiwoom.com/nkw.templateFrameSet.do?m=m1408030000)

---

## ✅ 체크리스트

설정을 완료하셨나요? 아래 항목을 확인하세요:

- [ ] Windows OS 사용 중
- [ ] 키움증권 계좌 개설 (실계좌 또는 모의투자)
- [ ] 키움 OpenAPI+ 설치 완료
- [ ] 영웅문 로그인 확인
- [ ] 인증서 등록 완료
- [ ] PyQt5 설치 완료
- [ ] 테스트 코드 실행 성공

모든 항목을 체크하셨다면 실제 매매를 시작할 수 있습니다! 🎉

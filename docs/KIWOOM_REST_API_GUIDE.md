# 키움증권 REST API 설정 가이드

키움증권 REST API를 사용하면 **모든 OS(Windows, macOS, Linux)**에서 주식 거래 자동화가 가능합니다.

## 🎯 REST API vs OpenAPI+ 비교

| 구분 | REST API ✅ | OpenAPI+ (ActiveX) |
|------|-----------|-------------------|
| **OS** | 모든 OS 지원 | Windows 전용 |
| **설치** | 불필요 | OpenAPI+ 설치 필요 |
| **인증** | OAuth 토큰 | 로그인 + 인증서 |
| **언어** | 모든 언어 | Python (PyQt5) |
| **배포** | 서버 배포 가능 | 로컬 실행만 |

## 📋 요구사항

1. 키움증권 계좌 (실계좌 또는 모의투자)
2. OpenAPI 신청 및 승인
3. APP KEY, SECRET KEY 발급

---

## 🚀 설정 단계

### 1단계: 키움증권 계좌 개설

#### 모의투자 계좌 신청 (추천)
1. [키움 모의투자 신청](https://www1.kiwoom.com/nkw.templateFrameSet.do?m=m1408030000)
2. 키움증권 아이디로 로그인
3. 모의투자 신청 → 즉시 사용 가능
4. 초기 자금: 5,000만원

#### 실계좌 개설
1. [키움증권 홈페이지](https://www.kiwoom.com)
2. 온라인 계좌 개설
3. 본인 인증 및 서류 제출 (약 1-2일 소요)

---

### 2단계: OpenAPI 신청

1. **OpenAPI 포털 접속**
   - [키움 OpenAPI 포털](https://openapi.kiwoom.com)

2. **회원가입 및 로그인**
   - 키움증권 아이디로 로그인

3. **API 신청**
   - 포털 → API 신청 → 사용 목적 입력
   - 승인 대기 (영업일 기준 1-2일)

4. **승인 확인**
   - 승인 완료 시 이메일 또는 문자 알림

---

### 3단계: APP KEY 및 SECRET KEY 발급

1. **OpenAPI 포털 로그인**
   - https://openapi.kiwoom.com

2. **APP KEY 발급**
   - 포털 → API 관리 → APP KEY 발급
   - APP KEY 복사 (예: `PS1234567890abcd`)

3. **SECRET KEY 발급**
   - 같은 페이지에서 SECRET KEY 발급
   - SECRET KEY 복사 (예: `SE9876543210zyxw`)
   - ⚠️ **SECRET KEY는 한 번만 표시됩니다. 반드시 저장하세요!**

4. **계좌번호 확인**
   - 실계좌: 8자리 계좌번호
   - 모의투자: 모의투자 신청 시 발급된 계좌번호

---

### 4단계: 환경변수 설정

`.env` 파일에 API 키 추가:

```env
# Kiwoom REST API
KIWOOM_APP_KEY=PS1234567890abcd
KIWOOM_SECRET_KEY=SE9876543210zyxw
KIWOOM_ACCOUNT_NO=12345678
```

---

## 💻 사용 예제

### 기본 연결 및 토큰 발급

```python
from backend.api.kiwoom_rest_client import KiwoomRestAPI

# 모의투자 모드 (기본값)
client = KiwoomRestAPI(is_mock=True)

# 토큰 발급
token_result = client.get_access_token()
if token_result['success']:
    print(f"✅ 토큰 발급 성공: {token_result['access_token'][:20]}...")
else:
    print(f"❌ 토큰 발급 실패: {token_result['message']}")
```

### 주식 매수/매도

```python
# 삼성전자 10주 매수 (지정가 70,000원)
buy_result = client.buy_stock("005930", 10, 70000, "00")  # "00": 지정가
print(buy_result)

# 삼성전자 10주 매도 (시장가)
sell_result = client.sell_stock("005930", 10, 0, "01")  # "01": 시장가
print(sell_result)

# 주문 취소
cancel_result = client.cancel_order("ORD123456", "005930", 10)
print(cancel_result)
```

### 계좌 조회

```python
# 계좌 잔고 조회
balance = client.get_account_balance()
print(f"총 평가금액: {balance['total_balance']:,}원")
print(f"총 손익: {balance['total_profit_loss']:,}원")

for position in balance['positions']:
    print(f"{position['stock_name']}: {position['quantity']}주")
    print(f"  평균가: {position['average_price']:,}원")
    print(f"  현재가: {position['current_price']:,}원")
    print(f"  수익률: {position['profit_rate']:.2f}%")
```

### 시세 조회

```python
# 삼성전자 현재가 조회
price = client.get_stock_price("005930")
print(f"현재가: {price['current_price']:,}원")
print(f"등락률: {price['change_rate']:.2f}%")
print(f"거래량: {price['volume']:,}주")

# 일봉 차트 조회 (최근 30일)
chart = client.get_daily_chart("005930", days=30)
for day in chart['chart_data'][:5]:
    print(f"{day['date']}: 종가 {day['close']:,}원")
```

### 미체결 주문 조회

```python
# 미체결 주문 조회
orders = client.get_orders()
for order in orders['orders']:
    print(f"주문번호: {order['order_no']}")
    print(f"{order['stock_name']}: {order['quantity']}주 @ {order['price']:,}원")
```

---

## 🔧 주문 유형 코드

### 주문 구분 (ORD_DVSN)
- `"00"`: 지정가
- `"01"`: 시장가
- `"02"`: 조건부지정가
- `"03"`: 최유리지정가
- `"04"`: 최우선지정가
- `"05"`: 장전시간외
- `"06"`: 장후시간외

### 시장 구분 (FID_COND_MRKT_DIV_CODE)
- `"J"`: 주식
- `"ETF"`: ETF
- `"ETN"`: ETN

---

## ⚠️ 주의사항

### 1. API 호출 제한
- **초당 최대 20건**
- **분당 최대 200건**
- 초과 시 일시적으로 차단될 수 있음

### 2. 토큰 관리
- 토큰 유효기간: **24시간**
- 자동 갱신 기능 구현됨
- 만료 전 자동으로 재발급

### 3. 계좌번호 보안
- **절대 코드에 직접 입력하지 마세요**
- `.env` 파일 사용 (Git에 커밋하지 않음)
- `.gitignore`에 `.env` 추가 확인

### 4. 모의투자 권장
- 처음 사용 시 **반드시 모의투자로 테스트**
- 전략 검증 후 실계좌 사용

### 5. 거래 시간
- **평일 09:00 ~ 15:30** (장 운영 시간)
- 시간외 거래: 08:30 ~ 09:00, 15:40 ~ 16:00

---

## 🐛 문제 해결

### "토큰 발급 실패" 오류
1. APP KEY, SECRET KEY 확인
2. OpenAPI 승인 상태 확인
3. 네트워크 연결 확인

### "계좌번호 오류"
1. 계좌번호 형식 확인 (8자리)
2. 실계좌/모의투자 구분 확인
3. `is_mock` 파라미터 확인

### "주문 실패" 오류
1. 거래 시간 확인
2. 계좌 잔고 확인
3. 종목코드 확인 (6자리)
4. 주문 가능 수량 확인

### "API 호출 제한 초과"
1. 요청 간격 조정 (최소 0.05초)
2. 호출 횟수 모니터링
3. 필요 시 대기 시간 추가

---

## 📊 실전/모의투자 전환

```python
# 모의투자 (기본값)
client = KiwoomRestAPI(is_mock=True)

# 실전 투자
client = KiwoomRestAPI(is_mock=False)
```

**API 엔드포인트**:
- 모의투자: `https://mockapi.kiwoom.com`
- 실전투자: `https://api.kiwoom.com`

---

## 📚 참고 자료

- [키움 OpenAPI 포털](https://openapi.kiwoom.com)
- [API 가이드](https://openapi.kiwoom.com/guide/apiguide)
- [전체 API 명세서 다운로드](https://openapi.kiwoom.com/guide/apiguide) (엑셀/PDF)

---

## ✅ 체크리스트

설정을 완료하셨나요? 아래 항목을 확인하세요:

- [ ] 키움증권 계좌 개설 (실계좌 또는 모의투자)
- [ ] OpenAPI 신청 및 승인 완료
- [ ] APP KEY 발급
- [ ] SECRET KEY 발급 및 안전하게 저장
- [ ] 계좌번호 확인
- [ ] `.env` 파일에 API 키 추가
- [ ] 토큰 발급 테스트 성공
- [ ] 시세 조회 테스트 성공

모든 항목을 체크하셨다면 실제 매매를 시작할 수 있습니다! 🎉

---

## 🆚 OpenAPI+ vs REST API

이미 OpenAPI+ 설정을 완료하셨다면?

**REST API의 장점**:
1. ✅ 모든 OS에서 실행 가능
2. ✅ 서버 배포 가능 (AWS, GCP 등)
3. ✅ Docker 컨테이너화 가능
4. ✅ 설치 과정 불필요
5. ✅ CI/CD 파이프라인 통합 용이

**REST API를 사용하세요!** 👍

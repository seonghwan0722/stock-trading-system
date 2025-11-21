# 🧪 TDD (Test-Driven Development) 환경 설정 가이드

**날짜**: 2025-01-22
**프로젝트**: 주식 자동매매 시스템

---

## 📋 TDD란?

**Test-Driven Development (테스트 주도 개발)**은 다음 3단계를 반복하는 개발 방법론입니다:

1. **Red** 🔴: 실패하는 테스트 작성
2. **Green** 🟢: 테스트를 통과하는 최소한의 코드 작성
3. **Refactor** 🔵: 코드 개선 (테스트는 계속 통과)

---

## 🎯 TDD 프레임워크 선택

### 옵션 1: **pytest** (추천 ⭐)

**장점**:
- ✅ 간단하고 직관적인 문법
- ✅ Python 표준처럼 널리 사용됨
- ✅ 풍부한 플러그인 생태계
- ✅ Fixture 시스템 강력
- ✅ 병렬 테스트 지원 (pytest-xdist)
- ✅ Flask 테스트에 최적화

**단점**:
- ❌ 학습 곡선 있음 (fixture 개념)

**설치**:
```bash
pip install pytest pytest-flask pytest-cov pytest-mock
```

**예시 테스트**:
```python
# tests/test_dart_api.py
import pytest
from backend.dart.dart_api_client import DartAPIClient

def test_search_company():
    client = DartAPIClient(api_key="test_key")
    result = client.search_company("삼성전자")
    assert result is not None
    assert "companies" in result
```

**실행**:
```bash
pytest                          # 모든 테스트 실행
pytest tests/test_dart_api.py  # 특정 파일만
pytest -v                       # 상세 출력
pytest --cov                    # 커버리지 측정
```

---

### 옵션 2: **unittest** (Python 내장)

**장점**:
- ✅ Python 표준 라이브러리 (설치 불필요)
- ✅ JUnit 스타일에 익숙하면 쉬움
- ✅ 안정적이고 검증됨

**단점**:
- ❌ 문법이 장황함 (클래스 기반)
- ❌ Fixture 지원 약함
- ❌ 플러그인 생태계 작음

**예시 테스트**:
```python
import unittest
from backend.dart.dart_api_client import DartAPIClient

class TestDartAPI(unittest.TestCase):
    def setUp(self):
        self.client = DartAPIClient(api_key="test_key")

    def test_search_company(self):
        result = self.client.search_company("삼성전자")
        self.assertIsNotNone(result)
        self.assertIn("companies", result)
```

**실행**:
```bash
python -m unittest discover tests
```

---

### 옵션 3: **nose2** (legacy)

**장점**:
- ✅ unittest 확장
- ✅ 플러그인 지원

**단점**:
- ❌ pytest보다 기능 부족
- ❌ 활발히 개발되지 않음

**추천하지 않음** - pytest 사용 권장

---

## 🏗️ 추천 TDD 환경 구성

### 프레임워크: **pytest** ⭐

```bash
# 필수 패키지
pip install pytest pytest-flask pytest-cov pytest-mock pytest-asyncio

# 선택 패키지
pip install pytest-xdist    # 병렬 테스트
pip install pytest-watch    # 파일 변경 감지 자동 테스트
pip install pytest-html     # HTML 리포트
```

---

## 📁 테스트 디렉토리 구조

```
주식 프로젝트/
├── tests/                      # 테스트 루트
│   ├── __init__.py
│   ├── conftest.py            # pytest 설정 및 fixture
│   │
│   ├── unit/                  # 단위 테스트
│   │   ├── __init__.py
│   │   ├── test_dart_api.py
│   │   ├── test_stock_db.py
│   │   └── test_strategies.py
│   │
│   ├── integration/           # 통합 테스트
│   │   ├── __init__.py
│   │   ├── test_dart_routes.py
│   │   └── test_api_endpoints.py
│   │
│   ├── e2e/                   # E2E 테스트
│   │   ├── __init__.py
│   │   └── test_user_flow.py
│   │
│   └── fixtures/              # 테스트 데이터
│       ├── sample_financials.json
│       └── sample_stocks.json
│
├── pytest.ini                 # pytest 설정
├── .coveragerc               # 커버리지 설정
└── backend/
    └── (프로덕션 코드)
```

---

## ⚙️ pytest 설정 파일

### `pytest.ini`

```ini
[pytest]
# 테스트 경로
testpaths = tests

# 파일 패턴
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# 출력 옵션
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=backend
    --cov-report=html
    --cov-report=term-missing

# 마커 정의
markers =
    unit: 단위 테스트
    integration: 통합 테스트
    e2e: E2E 테스트
    slow: 느린 테스트
    dart: DART API 관련 테스트
    db: 데이터베이스 테스트

# 경고 무시
filterwarnings =
    ignore::DeprecationWarning
```

### `.coveragerc`

```ini
[run]
source = backend
omit =
    */tests/*
    */venv/*
    */__pycache__/*
    */migrations/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
```

---

## 🧪 Fixture 예시 (`conftest.py`)

```python
import pytest
from backend.app import app as flask_app
from backend.dart.dart_api_client import DartAPIClient
from backend.database.stock_db import StockDatabase

@pytest.fixture
def app():
    """Flask 앱 fixture"""
    flask_app.config.update({
        "TESTING": True,
        "DART_API_KEY": "test_key",
    })
    yield flask_app

@pytest.fixture
def client(app):
    """Flask 테스트 클라이언트"""
    return app.test_client()

@pytest.fixture
def dart_client():
    """DART API 클라이언트 fixture"""
    return DartAPIClient(api_key="test_api_key")

@pytest.fixture
def test_db(tmp_path):
    """테스트용 데이터베이스"""
    db_path = tmp_path / "test.db"
    db = StockDatabase(db_path=str(db_path))
    yield db
    # 테스트 후 정리
    db.close()

@pytest.fixture
def sample_stock_data():
    """샘플 종목 데이터"""
    return {
        "stock_name": "삼성전자",
        "stock_code": "005930",
        "corp_code": "00126380",
        "market": "KOSPI"
    }
```

---

## 📝 테스트 작성 예시

### 1. 단위 테스트 (Unit Test)

**`tests/unit/test_stock_db.py`**:

```python
import pytest
from backend.database.stock_db import StockDatabase

class TestStockDatabase:
    """종목 데이터베이스 단위 테스트"""

    def test_insert_stock(self, test_db, sample_stock_data):
        """종목 삽입 테스트"""
        count = test_db.insert_stock(sample_stock_data)
        assert count == 1

    def test_search_stocks(self, test_db, sample_stock_data):
        """종목 검색 테스트"""
        test_db.insert_stock(sample_stock_data)
        results = test_db.search_stocks("삼성")
        assert len(results) == 1
        assert results[0]["stock_name"] == "삼성전자"

    def test_search_empty_query(self, test_db):
        """빈 검색어 테스트"""
        results = test_db.search_stocks("")
        assert results == []
```

---

### 2. 통합 테스트 (Integration Test)

**`tests/integration/test_dart_routes.py`**:

```python
import pytest

class TestDartAPI:
    """DART API 엔드포인트 통합 테스트"""

    def test_search_stocks_endpoint(self, client):
        """종목 검색 API 테스트"""
        response = client.get("/api/dart/stocks/search?q=삼성&limit=10")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "data" in data

    def test_get_financials_unauthorized(self, client):
        """인증 없이 재무제표 조회 시 실패"""
        response = client.get("/api/dart/financials/00126380")
        assert response.status_code == 401

    def test_get_financials_with_auth(self, client, auth_token):
        """인증된 재무제표 조회"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get(
            "/api/dart/financials/00126380?year=2023",
            headers=headers
        )
        assert response.status_code == 200
```

---

### 3. Mock을 사용한 테스트

**`tests/unit/test_dart_api_client.py`**:

```python
import pytest
from unittest.mock import Mock, patch
from backend.dart.dart_api_client import DartAPIClient

class TestDartAPIClient:
    """DART API 클라이언트 테스트"""

    @patch('requests.get')
    def test_search_company_success(self, mock_get, dart_client):
        """회사 검색 성공 케이스"""
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "000",
            "companies": [
                {"corp_name": "삼성전자", "corp_code": "00126380"}
            ]
        }
        mock_get.return_value = mock_response

        # 테스트 실행
        result = dart_client.search_company("삼성전자")

        # 검증
        assert result["status"] == "000"
        assert len(result["companies"]) == 1
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_api_error_handling(self, mock_get, dart_client):
        """API 에러 핸들링 테스트"""
        mock_get.side_effect = Exception("Network error")

        with pytest.raises(Exception):
            dart_client.search_company("삼성전자")
```

---

## 🎯 TDD 워크플로우

### 1. Red 단계 (실패하는 테스트 작성)

```python
# tests/unit/test_new_feature.py
def test_calculate_roe():
    """ROE 계산 테스트"""
    analyzer = FinancialDataAnalyzer()
    roe = analyzer.calculate_roe(
        net_income=1000000,
        equity=5000000
    )
    assert roe == 20.0  # 기대값: 20%
```

**실행**: `pytest tests/unit/test_new_feature.py`
**결과**: ❌ FAILED (함수가 없음)

---

### 2. Green 단계 (통과하는 코드 작성)

```python
# backend/dart/dart_api_client.py
class FinancialDataAnalyzer:
    def calculate_roe(self, net_income: float, equity: float) -> float:
        """ROE 계산"""
        if equity == 0:
            return 0.0
        return (net_income / equity) * 100
```

**실행**: `pytest tests/unit/test_new_feature.py`
**결과**: ✅ PASSED

---

### 3. Refactor 단계 (코드 개선)

```python
class FinancialDataAnalyzer:
    def calculate_roe(self, net_income: float, equity: float) -> float:
        """
        ROE (Return on Equity) 계산

        Args:
            net_income: 당기순이익
            equity: 자기자본

        Returns:
            ROE 퍼센트 (0.0 if equity is 0)
        """
        if equity <= 0:  # 개선: 음수도 처리
            return 0.0
        return round((net_income / equity) * 100, 2)  # 개선: 소수점 2자리
```

**실행**: `pytest tests/unit/test_new_feature.py`
**결과**: ✅ PASSED (리팩토링 후에도 통과)

---

## 📊 테스트 커버리지 목표

| 카테고리 | 목표 커버리지 | 설명 |
|---------|-------------|------|
| **핵심 비즈니스 로직** | 90%+ | DART API, 재무 분석 |
| **API 엔드포인트** | 80%+ | Flask 라우트 |
| **데이터베이스** | 85%+ | 종목 DB, 검색 |
| **유틸리티** | 70%+ | 헬퍼 함수 |
| **전체** | 80%+ | 프로젝트 전체 |

**커버리지 확인**:
```bash
pytest --cov=backend --cov-report=html
# htmlcov/index.html 열기
```

---

## 🚀 CI/CD 통합 (GitHub Actions)

**`.github/workflows/tests.yml`**:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.8'

    - name: Install dependencies
      run: |
        pip install -r config/requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: pytest --cov=backend --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

## 🛠️ 개발 워크플로우

### 일상적인 TDD 사이클

```bash
# 1. 새 기능 개발 시작
git checkout -b feature/new-feature

# 2. 실패하는 테스트 작성
vim tests/unit/test_new_feature.py

# 3. 테스트 실행 (실패 확인)
pytest tests/unit/test_new_feature.py -v

# 4. 코드 구현
vim backend/module/new_feature.py

# 5. 테스트 실행 (통과 확인)
pytest tests/unit/test_new_feature.py -v

# 6. 리팩토링
vim backend/module/new_feature.py

# 7. 전체 테스트 실행
pytest

# 8. 커버리지 확인
pytest --cov

# 9. 커밋
git add .
git commit -m "feat: 새 기능 추가 with TDD"
```

---

## 💡 TDD 베스트 프랙티스

### ✅ DO

1. **작은 단위로 테스트**
   - 함수/메서드 단위로 테스트 작성

2. **Given-When-Then 패턴**
   ```python
   def test_example():
       # Given (준비)
       user = create_user()

       # When (실행)
       result = user.login()

       # Then (검증)
       assert result is True
   ```

3. **테스트 이름 명확히**
   - `test_search_returns_empty_when_no_results()`
   - `test_api_raises_error_on_invalid_key()`

4. **Fixture 활용**
   - 반복되는 설정은 fixture로

5. **Mock 적절히 사용**
   - 외부 API 호출, DB 접근 등

### ❌ DON'T

1. **테스트에 로직 넣지 않기**
   - 테스트는 단순해야 함

2. **테스트 간 의존성**
   - 각 테스트는 독립적이어야 함

3. **실제 DB 사용**
   - 테스트용 DB 또는 Mock 사용

4. **너무 많은 Mock**
   - 과도한 Mock은 테스트 신뢰성 하락

---

## 📚 다음 단계

1. ✅ TDD 프레임워크 선택 (pytest 추천)
2. ✅ 테스트 디렉토리 구조 생성
3. ✅ `pytest.ini`, `.coveragerc` 설정
4. ✅ `conftest.py`에 fixture 작성
5. ✅ 첫 테스트 작성 (간단한 기능부터)
6. ✅ CI/CD 설정 (GitHub Actions)

---

**다음 문서**: `README.md`에 결정 사항 정리

---

# Open DART API Documentation

## Overview

Open DART (전자공시 Open DART 시스템) is Korea's official Electronic Disclosure System API, provided by the Financial Supervisory Service (FSS). It provides access to comprehensive financial data, corporate filings, and regulatory disclosures for all listed and KOSDAQ companies.

**API Base URL**: `https://opendart.fss.or.kr/api`

**Documentation URL**: https://opendart.fss.or.kr/guide/main.do

---

## 1. Authentication

### API Key Registration

1. Visit: https://opendart.fss.or.kr/
2. Create a free account (회원가입)
3. Request API Key (API 인증키 신청)
4. API key will be issued immediately (무료)
5. Use `crtfc_key` parameter in all API requests

### Authentication Method

All requests require the following query parameter:

```
crtfc_key=YOUR_API_KEY_HERE
```

**Example**:
```
https://opendart.fss.or.kr/api/company.json?crtfc_key=YOUR_API_KEY&corp_code=00126380
```

### Security Notes
- API keys are personal; do not share publicly
- API key has no expiration date
- No OAuth2 or JWT authentication required
- Single query parameter authentication model

---

## 2. Rate Limits & Usage Restrictions

### Rate Limiting Policy
- **Concurrent Requests**: Max 10 concurrent connections per API key
- **Daily Requests**: No official daily limit, but recommended max 10,000 requests/day
- **Request Interval**: Minimum 0.1 seconds between requests recommended
- **Response Size**: JSON responses typically 1-50 KB

### Best Practices
```python
import time
import requests

# Implement request throttling
class DartAPIClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.last_request_time = 0
        self.min_interval = 0.1  # seconds

    def request(self, endpoint, params):
        # Rate limiting
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)

        self.last_request_time = time.time()
        params['crtfc_key'] = self.api_key

        response = requests.get(endpoint, params=params)
        return response.json()
```

---

## 3. Core API Endpoints

### 3.1 Company Information Endpoints

#### A. Get Company by Code
```
GET /company.json
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| corp_code | string | Yes | 8-digit corporate code (고유번호) |
| crtfc_key | string | Yes | API authentication key |

**Example Request**:
```bash
curl "https://opendart.fss.or.kr/api/company.json?crtfc_key=YOUR_KEY&corp_code=00126380"
```

**Example Response**:
```json
{
  "status": "000",
  "message": "정상",
  "corp_code": "00126380",
  "corp_name": "삼성전자",
  "stock_code": "005930",
  "modify_date": "20231215"
}
```

#### B. Company List (Bulk Download)
```
GET /corpCode.json
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| crtfc_key | string | Yes | API authentication key |

**Description**: Returns list of all registered companies with corp_code and stock_code

**Example**:
```bash
curl "https://opendart.fss.or.kr/api/corpCode.json?crtfc_key=YOUR_KEY"
```

**Response**: Returns zip file containing compressed XML with all companies

#### C. Search Company by Name (Preview API)
```
GET /companysearch.json
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| corp_name | string | Yes | Company name (Korean) |
| crtfc_key | string | Yes | API authentication key |
| page_count | integer | No | Results per page (default: 10, max: 100) |
| page_no | integer | No | Page number (default: 1) |

**Example Request**:
```bash
curl "https://opendart.fss.or.kr/api/companysearch.json?crtfc_key=YOUR_KEY&corp_name=삼성&page_no=1&page_count=10"
```

**Example Response**:
```json
{
  "status": "000",
  "message": "정상",
  "page_count": 10,
  "total_count": 128,
  "current_page": 1,
  "list": [
    {
      "corp_code": "00126380",
      "corp_name": "삼성전자",
      "corp_name_eng": "SAMSUNG ELECTRONICS",
      "stock_code": "005930",
      "modify_date": "20231215"
    }
  ]
}
```

---

### 3.2 Filings & Reports Endpoints

#### A. Get Latest Filings
```
GET /list.json
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| corp_code | string | Yes | 8-digit corporate code |
| crtfc_key | string | Yes | API authentication key |
| pageNo | integer | No | Page number (default: 1) |
| pageCount | integer | No | Results per page (default: 10, max: 100) |

**Example**:
```bash
curl "https://opendart.fss.or.kr/api/list.json?crtfc_key=YOUR_KEY&corp_code=00126380"
```

**Example Response**:
```json
{
  "status": "000",
  "message": "정상",
  "page_no": 1,
  "page_count": 10,
  "total_count": 245,
  "list": [
    {
      "corp_code": "00126380",
      "corp_name": "삼성전자",
      "filing_type": "A001",
      "form_code": "감사보고서",
      "event_date": "20231231",
      "report_nm": "2023년 감사보고서",
      "receipt_no": "20240314000123",
      "filing_date": "20240314",
      "mod_date": "20240314",
      "disclosure_date": "20240314"
    }
  ]
}
```

#### B. Get Specific Filing Details
```
GET /document.json
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| receipt_no | string | Yes | Filing receipt number from list.json |
| crtfc_key | string | Yes | API authentication key |
| pageNo | integer | No | Page number |
| pageCount | integer | No | Results per page (max: 100) |

**Example**:
```bash
curl "https://opendart.fss.or.kr/api/document.json?crtfc_key=YOUR_KEY&receipt_no=20240314000123"
```

---

### 3.3 Financial Statements Endpoints

#### A. Get Financial Statements
```
GET /fnlttSinglAcntAll.json
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| corp_code | string | Yes | 8-digit corporate code |
| bsns_year | string | Yes | Fiscal year (YYYY format) |
| reprt_code | string | Yes | Report type code (see table below) |
| crtfc_key | string | Yes | API authentication key |

**Report Type Codes**:
| Code | Description | Season |
|------|-------------|--------|
| 11014 | 1Q Report | Q1 (1-3월) |
| 11012 | Half-Year Report | H1 (1-6월) |
| 11013 | 3Q Report | Q3 (1-9월) |
| 11011 | Annual Report (감사보고서) | Full Year (1-12월) |

**Account Division Codes**:
| Code | Division |
|------|----------|
| 1001 | Consolidated (연결) |
| 1002 | Non-Consolidated (별도) |

**Example Request**:
```bash
# Annual financial statement for 2023, Samsung Electronics
curl "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json?crtfc_key=YOUR_KEY&corp_code=00126380&bsns_year=2023&reprt_code=11011&fs_div=1001"
```

**Example Response**:
```json
{
  "status": "000",
  "message": "정상",
  "list": [
    {
      "rcept_no": "20240314000123",
      "reprt_code": "11011",
      "reprt_nm": "2023년 감사보고서",
      "fs_nm": "재무제표",
      "sj_div": "BS",
      "sj_nm": "재무상태표",
      "account_id": "1120000",
      "account_nm": "자산",
      "account_detail": "유동자산",
      "thstrm_nm": "2023년 12월 31일",
      "thstrm_add_nm": null,
      "thstrm_amount": "123456789000",
      "frmtrm_nm": "2022년 12월 31일",
      "frmtrm_amount": "120000000000",
      "currency": "KRW",
      "unit": "원"
    }
  ]
}
```

#### B. Financial Statement Metadata (Available Data)
```
GET /fnlttSinglAcnt.json
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| corp_code | string | Yes | 8-digit corporate code |
| crtfc_key | string | Yes | API authentication key |

**Description**: Returns list of available financial reports for a company

---

### 3.4 Dividend Information

#### Get Dividend Information
```
GET /dividend.json
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| stock_code | string | Yes | Stock code (6 digits) |
| crtfc_key | string | Yes | API authentication key |

**Example**:
```bash
curl "https://opendart.fss.or.kr/api/dividend.json?crtfc_key=YOUR_KEY&stock_code=005930"
```

---

### 3.5 Insider Trading

#### Get Major Shareholder Changes
```
GET /majorstock.json
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| corp_code | string | Yes | 8-digit corporate code |
| crtfc_key | string | Yes | API authentication key |
| pageNo | integer | No | Page number |
| pageCount | integer | No | Results per page |

---

---

## 4. Financial Data Structure

### Statement Types (Statement Division Codes)

| Code | Name (Korean) | Name (English) | Description |
|------|-----------------|------------------|-------------|
| BS | 재무상태표 | Balance Sheet | Assets, Liabilities, Equity |
| IS | 손익계산서 | Income Statement | Revenue, Expenses, Profit/Loss |
| CF | 현금흐름표 | Cash Flow Statement | Operating, Investing, Financing |
| SCE | 자본변동표 | Statement of Changes in Equity | Equity movements |
| AFS | 별도 재무제표 | Non-consolidated Statements | Parent company only |

### Account Structure

The API returns financial data with hierarchical account codes:

```
1000000 (Level 1) - 자산 (Assets)
├─ 1100000 (Level 2) - 유동자산 (Current Assets)
│  ├─ 1110000 (Level 3) - 현금 (Cash)
│  ├─ 1120000 - 단기금융상품 (Short-term investments)
│  └─ 1130000 - 매출채권 (Accounts receivable)
└─ 1200000 - 비유동자산 (Non-current Assets)
   ├─ 1210000 - 유형자산 (Property, Plant & Equipment)
   └─ 1220000 - 무형자산 (Intangible Assets)
```

### Response Fields

```json
{
  "rcept_no": "Receipt number from filing",
  "reprt_code": "Report code (11011, 11012, etc.)",
  "fs_nm": "Financial statement name",
  "sj_div": "Statement division (BS, IS, CF, etc.)",
  "account_id": "Account hierarchical code",
  "account_nm": "Account name (Korean)",
  "account_detail": "Detailed account description",
  "thstrm_nm": "Current period label (e.g., '2023년 12월 31일')",
  "thstrm_amount": "Current period amount (in won)",
  "frmtrm_nm": "Previous period label (e.g., '2022년 12월 31일')",
  "frmtrm_amount": "Previous period amount",
  "currency": "KRW (Korean Won)",
  "unit": "원 (Won)"
}
```

---

## 5. 50 Key Financial Metrics

### Balance Sheet (재무상태표) - 15 Metrics

| # | Metric Name (English) | Korean Name | Account Code | Category |
|----|----------------------|-------------|--------------|----------|
| 1 | Total Assets | 자산총계 | 1000000 | Assets |
| 2 | Current Assets | 유동자산 | 1100000 | Assets |
| 3 | Non-Current Assets | 비유동자산 | 1200000 | Assets |
| 4 | Cash and Equivalents | 현금및현금성자산 | 1110000 | Current Assets |
| 5 | Short-term Investments | 단기금융상품 | 1120000 | Current Assets |
| 6 | Accounts Receivable | 매출채권 | 1130000 | Current Assets |
| 7 | Inventories | 재고자산 | 1150000 | Current Assets |
| 8 | Property, Plant & Equipment | 유형자산 | 1210000 | Non-Current Assets |
| 9 | Intangible Assets | 무형자산 | 1220000 | Non-Current Assets |
| 10 | Long-term Investments | 장기금융상품 | 1250000 | Non-Current Assets |
| 11 | Total Liabilities | 부채총계 | 2000000 | Liabilities |
| 12 | Current Liabilities | 유동부채 | 2100000 | Liabilities |
| 13 | Non-Current Liabilities | 비유동부채 | 2200000 | Liabilities |
| 14 | Short-term Debt | 단기차입금 | 2110000 | Current Liabilities |
| 15 | Long-term Debt | 장기차입금 | 2210000 | Non-Current Liabilities |

### Balance Sheet (continued) - 10 Metrics

| # | Metric Name (English) | Korean Name | Account Code | Category |
|----|----------------------|-------------|--------------|----------|
| 16 | Total Equity | 자본총계 | 3000000 | Equity |
| 17 | Capital Stock | 자본금 | 3110000 | Equity |
| 18 | Retained Earnings | 이익잉여금 | 3200000 | Equity |
| 19 | Accounts Payable | 외상매입금 | 2140000 | Current Liabilities |
| 20 | Deferred Income Tax (Asset) | 이연세금자산 | 1280000 | Non-Current Assets |
| 21 | Deferred Income Tax (Liability) | 이연세금부채 | 2240000 | Non-Current Liabilities |
| 22 | Other Comprehensive Income | 기타포괄손익누적액 | 3300000 | Equity |
| 23 | Provisions | 충당금 | 2150000 | Current Liabilities |
| 24 | Non-controlling Interests | 비지배주주지분 | 3400000 | Equity |
| 25 | Lease Liabilities | 리스부채 | 2160000 | Current Liabilities |

### Income Statement (손익계산서) - 15 Metrics

| # | Metric Name (English) | Korean Name | Account Code | Category |
|----|----------------------|-------------|--------------|----------|
| 26 | Total Revenue | 매출액 | 4100000 | Revenue |
| 27 | Cost of Goods Sold | 매출원가 | 5100000 | Cost |
| 28 | Gross Profit | 매출총이익 | - | Calculated |
| 29 | Operating Expenses | 판매비와관리비 | 5200000 | Expenses |
| 30 | Operating Income | 영업이익 | - | Calculated |
| 31 | Finance Costs | 금융비용 | 5500000 | Non-operating |
| 32 | Finance Income | 금융수익 | 4300000 | Non-operating |
| 33 | Other Gains/Losses | 기타이익(손실) | 4400000 | Non-operating |
| 34 | Profit Before Tax | 세전이익 | - | Calculated |
| 35 | Income Tax Expense | 법인세비용 | 5600000 | Tax |
| 36 | Net Income | 당기순이익 | - | Calculated |
| 37 | Other Comprehensive Income (OCI) | 기타포괄손익 | 4500000 | OCI |
| 38 | Total Comprehensive Income | 총포괄손익 | - | Calculated |
| 39 | Discontinued Operations | 중단영업이익 | 4200000 | Special |
| 40 | Earnings Per Share (Basic) | 주당순이익(기본) | - | Derived |

### Cash Flow Statement (현금흐름표) - 10 Metrics

| # | Metric Name (English) | Korean Name | Account Code | Category |
|----|----------------------|-------------|--------------|----------|
| 41 | Operating Cash Flow | 영업활동현금흐름 | 6100000 | Operating |
| 42 | Investing Cash Flow | 투자활동현금흐름 | 6200000 | Investing |
| 43 | Financing Cash Flow | 재무활동현금흐름 | 6300000 | Financing |
| 44 | Change in Cash | 현금순증감 | - | Calculated |
| 45 | Cash at Beginning | 기초현금 | - | Opening Balance |
| 46 | Cash at Ending | 기말현금 | - | Closing Balance |
| 47 | Depreciation & Amortization | 감가상각 | - | Non-cash |
| 48 | Stock-based Compensation | 주식기반보상 | 5300000 | Non-cash |
| 49 | Impairment Losses | 손상차손 | 5400000 | Non-cash |
| 50 | Other Non-Cash Items | 기타비현금항목 | 6000000 | Non-cash |

---

## 6. Python Integration Examples

### 6.1 Basic API Client

```python
import requests
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

class DartAPIClient:
    """
    Open DART API Client for Korean Financial Data

    Attributes:
        api_key (str): API authentication key from Open DART
        base_url (str): Base URL for API endpoints
        timeout (int): Request timeout in seconds
    """

    BASE_URL = "https://opendart.fss.or.kr/api"

    def __init__(self, api_key: str, timeout: int = 10):
        """
        Initialize DART API client

        Args:
            api_key: Your API key from Open DART
            timeout: Request timeout in seconds
        """
        if not api_key:
            raise ValueError("API key is required")

        self.api_key = api_key
        self.timeout = timeout
        self.last_request_time = 0
        self.min_interval = 0.1  # Minimum 100ms between requests

    def _request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict:
        """
        Make API request with rate limiting

        Args:
            endpoint: API endpoint path (without base URL)
            params: Query parameters

        Returns:
            Parsed JSON response

        Raises:
            RequestException: If request fails
            ValueError: If API returns error
        """
        # Rate limiting
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)

        # Prepare parameters
        if params is None:
            params = {}
        params['crtfc_key'] = self.api_key

        # Make request
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        finally:
            self.last_request_time = time.time()

        # Parse response
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {str(e)}")

        # Check status code
        if data.get('status') != '000':
            error_msg = data.get('message', 'Unknown error')
            raise ValueError(f"API Error ({data.get('status')}): {error_msg}")

        return data

    # Company Lookup Methods

    def get_company_by_code(self, corp_code: str) -> Dict:
        """
        Get company information by corporate code

        Args:
            corp_code: 8-digit corporate code

        Returns:
            Company information dictionary
        """
        result = self._request("company.json", {"corp_code": corp_code})
        return result

    def search_company(self, corp_name: str, page_no: int = 1,
                      page_count: int = 10) -> Dict:
        """
        Search companies by name

        Args:
            corp_name: Company name (Korean)
            page_no: Page number (default: 1)
            page_count: Results per page (default: 10, max: 100)

        Returns:
            Search results with pagination
        """
        params = {
            "corp_name": corp_name,
            "page_no": page_no,
            "page_count": min(page_count, 100)
        }
        result = self._request("companysearch.json", params)
        return result

    def get_company_list(self) -> bytes:
        """
        Get full company list as zip file

        Returns:
            Zip file binary content
        """
        url = f"{self.BASE_URL}/corpCode.json"
        params = {'crtfc_key': self.api_key}

        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()

        return response.content

    # Filing Methods

    def get_filings(self, corp_code: str, page_no: int = 1,
                   page_count: int = 10) -> Dict:
        """
        Get list of filings for a company

        Args:
            corp_code: Corporate code
            page_no: Page number
            page_count: Results per page

        Returns:
            Filing list with pagination
        """
        params = {
            "corp_code": corp_code,
            "pageNo": page_no,
            "pageCount": min(page_count, 100)
        }
        result = self._request("list.json", params)
        return result

    def get_filing_details(self, receipt_no: str) -> Dict:
        """
        Get details of specific filing

        Args:
            receipt_no: Receipt number from get_filings()

        Returns:
            Filing details
        """
        params = {"receipt_no": receipt_no}
        result = self._request("document.json", params)
        return result

    # Financial Statement Methods

    def get_financial_statements(self, corp_code: str, bsns_year: str,
                                reprt_code: str = "11011",
                                fs_div: str = "1001") -> Dict:
        """
        Get financial statements

        Args:
            corp_code: Corporate code
            bsns_year: Business year (YYYY)
            reprt_code: Report code
                - 11011: Annual (감사보고서)
                - 11012: Half-year (반기보고서)
                - 11013: Q3 (3분기보고서)
                - 11014: Q1 (1분기보고서)
            fs_div: Financial statement division
                - 1001: Consolidated (연결)
                - 1002: Non-consolidated (별도)

        Returns:
            Financial statement data
        """
        params = {
            "corp_code": corp_code,
            "bsns_year": bsns_year,
            "reprt_code": reprt_code,
            "fs_div": fs_div
        }
        result = self._request("fnlttSinglAcntAll.json", params)
        return result

    def get_available_statements(self, corp_code: str) -> Dict:
        """
        Get list of available financial statements

        Args:
            corp_code: Corporate code

        Returns:
            List of available financial reports
        """
        params = {"corp_code": corp_code}
        result = self._request("fnlttSinglAcnt.json", params)
        return result
```

### 6.2 Financial Data Processor

```python
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple

class FinancialDataProcessor:
    """
    Process and structure DART API financial data
    """

    # Key account codes for common metrics
    KEY_ACCOUNTS = {
        # Balance Sheet (Assets)
        'total_assets': '1000000',
        'current_assets': '1100000',
        'cash_and_equivalents': '1110000',
        'accounts_receivable': '1130000',
        'inventories': '1150000',
        'non_current_assets': '1200000',
        'ppe': '1210000',  # Property, Plant & Equipment
        'intangible_assets': '1220000',

        # Balance Sheet (Liabilities)
        'total_liabilities': '2000000',
        'current_liabilities': '2100000',
        'short_term_debt': '2110000',
        'accounts_payable': '2140000',
        'non_current_liabilities': '2200000',
        'long_term_debt': '2210000',

        # Balance Sheet (Equity)
        'total_equity': '3000000',
        'capital_stock': '3110000',
        'retained_earnings': '3200000',

        # Income Statement
        'revenue': '4100000',
        'cost_of_goods_sold': '5100000',
        'operating_expenses': '5200000',
        'finance_costs': '5500000',
        'finance_income': '4300000',
        'income_tax_expense': '5600000',

        # Cash Flow
        'operating_cash_flow': '6100000',
        'investing_cash_flow': '6200000',
        'financing_cash_flow': '6300000',
    }

    @staticmethod
    def extract_key_metrics(financial_data: Dict) -> Dict[str, Dict]:
        """
        Extract key financial metrics from raw API data

        Args:
            financial_data: Raw response from get_financial_statements()

        Returns:
            Dictionary of key metrics by category
        """
        if not financial_data.get('list'):
            return {}

        # Create lookup by account code
        accounts = {}
        for item in financial_data['list']:
            accounts[item['account_id']] = item

        metrics = {
            'balance_sheet': {},
            'income_statement': {},
            'cash_flow': {}
        }

        # Extract metrics
        for key, code in FinancialDataProcessor.KEY_ACCOUNTS.items():
            if code in accounts:
                item = accounts[code]
                amount = int(item.get('thstrm_amount', 0))

                if key.startswith(('total_assets', 'current_assets', 'non_current_assets',
                                  'ppe', 'intangible', 'total_liabilities', 'current_liabilities',
                                  'non_current', 'total_equity', 'capital', 'retained')):
                    metrics['balance_sheet'][key] = amount
                elif key in ['revenue', 'cost_of_goods_sold', 'operating_expenses',
                            'finance_costs', 'finance_income', 'income_tax_expense']:
                    metrics['income_statement'][key] = amount
                elif 'cash_flow' in key:
                    metrics['cash_flow'][key] = amount

        return metrics

    @staticmethod
    def calculate_ratios(balance_sheet: Dict, income_stmt: Dict) -> Dict[str, float]:
        """
        Calculate common financial ratios

        Args:
            balance_sheet: Balance sheet metrics
            income_stmt: Income statement metrics

        Returns:
            Dictionary of calculated ratios
        """
        ratios = {}

        try:
            # Profitability Ratios
            if income_stmt.get('revenue', 0) > 0:
                ratios['net_margin'] = (income_stmt.get('revenue', 0) -
                                       income_stmt.get('cost_of_goods_sold', 0) -
                                       income_stmt.get('operating_expenses', 0)) / income_stmt['revenue']
                ratios['gross_margin'] = (income_stmt.get('revenue', 0) -
                                         income_stmt.get('cost_of_goods_sold', 0)) / income_stmt['revenue']

            # Leverage Ratios
            if balance_sheet.get('total_assets', 0) > 0:
                ratios['debt_ratio'] = balance_sheet.get('total_liabilities', 0) / balance_sheet['total_assets']
                ratios['equity_ratio'] = balance_sheet.get('total_equity', 0) / balance_sheet['total_assets']

            if balance_sheet.get('total_equity', 0) > 0:
                ratios['debt_to_equity'] = balance_sheet.get('total_liabilities', 0) / balance_sheet['total_equity']

            # Liquidity Ratios
            if balance_sheet.get('current_liabilities', 0) > 0:
                ratios['current_ratio'] = balance_sheet.get('current_assets', 0) / balance_sheet['current_liabilities']

        except (ZeroDivisionError, TypeError):
            pass

        return ratios

    @staticmethod
    def to_dataframe(financial_data: Dict) -> pd.DataFrame:
        """
        Convert financial data to pandas DataFrame

        Args:
            financial_data: Raw API response

        Returns:
            Formatted DataFrame
        """
        if not financial_data.get('list'):
            return pd.DataFrame()

        df = pd.DataFrame(financial_data['list'])

        # Convert amounts to numeric
        for col in ['thstrm_amount', 'frmtrm_amount']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Format dates
        if 'rcept_no' in df.columns:
            # Extract date from receipt number (YYYYMM...)
            df['receipt_date'] = pd.to_datetime(
                df['rcept_no'].str[:8],
                format='%Y%m%d',
                errors='coerce'
            )

        return df
```

### 6.3 Example Usage

```python
# Initialize client
api_key = "YOUR_API_KEY_HERE"
client = DartAPIClient(api_key)

# 1. Search for company
print("Searching for Samsung...")
search_results = client.search_company("삼성전자", page_count=5)
print(f"Found {search_results['total_count']} results")

samsung_code = search_results['list'][0]['corp_code']  # "00126380"
print(f"Samsung Corp Code: {samsung_code}")

# 2. Get company information
company_info = client.get_company_by_code(samsung_code)
print(f"Company: {company_info['corp_name']}")
print(f"Stock Code: {company_info['stock_code']}")

# 3. Get financial statements for 2023
print("\nFetching 2023 financial statements...")
fin_data = client.get_financial_statements(
    corp_code=samsung_code,
    bsns_year="2023",
    reprt_code="11011",  # Annual report
    fs_div="1001"  # Consolidated
)

# 4. Extract and analyze metrics
processor = FinancialDataProcessor()
metrics = processor.extract_key_metrics(fin_data)

print("\n=== Balance Sheet Metrics (2023) ===")
for key, value in metrics['balance_sheet'].items():
    print(f"{key}: {value:,} KRW")

# 5. Calculate ratios
ratios = processor.calculate_ratios(metrics['balance_sheet'], metrics['income_statement'])
print("\n=== Financial Ratios ===")
for ratio, value in ratios.items():
    print(f"{ratio}: {value:.2%}")

# 6. Convert to DataFrame
df = processor.to_dataframe(fin_data)
print(f"\nFinancial data rows: {len(df)}")
print(df[['account_nm', 'account_detail', 'thstrm_amount', 'frmtrm_amount']].head(10))
```

---

## 7. Error Handling

### Common Error Codes

| Status Code | Message | Meaning | Solution |
|-------------|---------|---------|----------|
| 000 | 정상 | Success | Normal response |
| 010 | 검색 결과가 없습니다 | No search results | Try different search terms |
| 011 | 필수 항목이 누락되었습니다 | Missing required parameter | Check all required params |
| 013 | 조회되는 정보가 없습니다 | No data found | Corp code or year may be invalid |
| 014 | 중복된 공시입니다 | Duplicate filing | Filtered by DART system |
| 100 | 정상 처리되었습니다 | Processing | Response still valid |
| 200 | 500 오류 | Server error | Retry request |

### Error Handling Example

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_api_call(client, method_name, *args, **kwargs):
    """Wrapper for API calls with error handling"""
    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            method = getattr(client, method_name)
            return method(*args, **kwargs)

        except ValueError as e:
            error_msg = str(e)

            if "No search results" in error_msg:
                logger.warning(f"No data found: {error_msg}")
                return None

            elif "Missing required" in error_msg:
                logger.error(f"Invalid parameters: {error_msg}")
                raise

            else:
                logger.error(f"API error: {error_msg}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise

    return None

# Usage
try:
    result = safe_api_call(client, 'get_financial_statements',
                          corp_code=samsung_code,
                          bsns_year="2023")
except Exception as e:
    logger.critical(f"Failed to get financial data: {str(e)}")
```

---

## 8. Best Practices

### 1. Rate Limiting Strategy

```python
from datetime import datetime, timedelta
from collections import deque

class RateLimiter:
    """Advanced rate limiter for DART API"""

    def __init__(self, max_requests: int = 10000,
                 window_minutes: int = 1440):  # 24 hours
        self.max_requests = max_requests
        self.window_seconds = window_minutes * 60
        self.request_times = deque()

    def wait_if_needed(self) -> float:
        """Return wait time needed before next request"""
        now = time.time()

        # Remove old requests outside window
        while self.request_times and self.request_times[0] < now - self.window_seconds:
            self.request_times.popleft()

        if len(self.request_times) >= self.max_requests:
            oldest = self.request_times[0]
            wait_time = self.window_seconds - (now - oldest)
            return max(0, wait_time)

        return 0

    def record_request(self):
        """Record timestamp of request"""
        self.request_times.append(time.time())
```

### 2. Caching Strategy

```python
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

class CachingClient(DartAPIClient):
    """DART API client with intelligent caching"""

    def __init__(self, api_key: str, cache_dir: str = "./dart_cache",
                 cache_ttl_hours: int = 24):
        super().__init__(api_key)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_ttl = timedelta(hours=cache_ttl_hours)

    def _get_cache_path(self, endpoint: str, params: Dict) -> Path:
        """Generate cache file path"""
        cache_key = json.dumps({endpoint: params}, sort_keys=True)
        hash_key = hashlib.md5(cache_key.encode()).hexdigest()
        return self.cache_dir / f"{endpoint}_{hash_key}.json"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache file is still valid"""
        if not cache_path.exists():
            return False

        mod_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - mod_time < self.cache_ttl

    def _request(self, endpoint: str, params: Dict = None) -> Dict:
        """Override to add caching"""
        cache_path = self._get_cache_path(endpoint, params or {})

        # Try cache first
        if self._is_cache_valid(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        # Fetch from API
        data = super()._request(endpoint, params)

        # Cache result
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return data
```

### 3. Data Validation

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class CompanyData:
    """Validated company data structure"""
    corp_code: str
    corp_name: str
    stock_code: str
    modify_date: str

    def __post_init__(self):
        """Validate data on initialization"""
        if not self.corp_code or len(self.corp_code) != 8:
            raise ValueError(f"Invalid corp_code: {self.corp_code}")

        if not self.stock_code or len(self.stock_code) != 6:
            raise ValueError(f"Invalid stock_code: {self.stock_code}")

    @classmethod
    def from_api_response(cls, data: Dict) -> 'CompanyData':
        """Create instance from API response"""
        return cls(
            corp_code=data.get('corp_code', ''),
            corp_name=data.get('corp_name', ''),
            stock_code=data.get('stock_code', ''),
            modify_date=data.get('modify_date', '')
        )

@dataclass
class FinancialStatement:
    """Validated financial statement"""
    corp_code: str
    bsns_year: str
    reprt_code: str
    statement_type: str  # BS, IS, CF
    accounts: Dict[str, int]

    def validate_accounts(self) -> bool:
        """Validate all account values are numeric"""
        return all(isinstance(v, int) for v in self.accounts.values())
```

---

## 9. API Limitations & Workarounds

### Known Limitations

1. **No Full-Text Search**: Company names must match exactly
2. **No Direct Stock Code Lookup**: Must use corp_code
3. **Historical Data Lag**: Reports posted 1-3 months after fiscal period end
4. **Statement Delay**: Financial statements posted after audit completion
5. **Korean Language Only**: Most company names are in Korean

### Workarounds

```python
def find_company_flexible(client, search_term):
    """
    Flexible company search handling multiple formats
    """
    # Try exact match first
    try:
        result = client.search_company(search_term, page_count=1)
        if result.get('total_count', 0) > 0:
            return result['list'][0]
    except:
        pass

    # Try partial match with wildcards
    partial_results = []
    for keyword in search_term.split():
        try:
            result = client.search_company(keyword, page_count=10)
            partial_results.extend(result.get('list', []))
        except:
            continue

    if partial_results:
        return partial_results[0]

    raise ValueError(f"Company not found: {search_term}")
```

---

## 10. FAQ & Troubleshooting

### Q: How do I get an API key?
A: Visit https://opendart.fss.or.kr/, create a free account, and request an API key. It's issued instantly.

### Q: What's the difference between corp_code and stock_code?
A:
- `corp_code`: 8-digit unique corporate identifier (used for API calls)
- `stock_code`: 6-digit stock exchange code (for trading)

### Q: How often is data updated?
A: Financial statements updated quarterly/annually after filing. Most updates within 24 hours of disclosure.

### Q: Can I bulk download all companies?
A: Yes, use `/corpCode.json` endpoint which returns a zip file with all companies.

### Q: How do I get historical financials?
A: Use `bsns_year` parameter with past years (e.g., "2022", "2021", etc.)

### Q: What's the data format for amounts?
A: All amounts are in Korean Won (KRW) as strings. Convert to int/float for calculations.

### Q: Is there a difference between consolidated and non-consolidated?
A: Yes. Consolidated includes subsidiaries. Non-consolidated is parent company only. Use `fs_div` parameter.

---

## 11. Additional Resources

- Official Guide: https://opendart.fss.or.kr/guide/main.do
- API Sandbox: https://opendart.fss.or.kr/api/main.do
- Company Search: https://opendart.fss.or.kr/dsab001/main.do
- Sample Python Libraries:
  - [dart-fss](https://github.com/FinanceData/dart-fss) - Comprehensive DART wrapper
  - [OpenDartReader](https://github.com/HyunsuLee/OpenDartReader) - Simple reader

---

## 12. Rate Limit Implementation

```python
class DartAPIClientAdvanced(DartAPIClient):
    """Enhanced client with rate limiting and retry logic"""

    def __init__(self, api_key: str,
                 max_concurrent: int = 10,
                 daily_limit: int = 10000):
        super().__init__(api_key)
        self.max_concurrent = max_concurrent
        self.daily_limit = daily_limit
        self.request_count_today = 0
        self.last_reset = datetime.now()

    def _check_daily_limit(self):
        """Check and reset daily limit"""
        now = datetime.now()
        if (now - self.last_reset).days >= 1:
            self.request_count_today = 0
            self.last_reset = now

        if self.request_count_today >= self.daily_limit:
            raise RuntimeError(
                f"Daily limit ({self.daily_limit}) exceeded. "
                f"Reset at: {self.last_reset + timedelta(days=1)}"
            )

    def _request(self, endpoint: str, params: Dict = None) -> Dict:
        """Override request with daily limit check"""
        self._check_daily_limit()

        result = super()._request(endpoint, params)
        self.request_count_today += 1

        return result
```

This comprehensive documentation provides everything needed to integrate with the Open DART API effectively.

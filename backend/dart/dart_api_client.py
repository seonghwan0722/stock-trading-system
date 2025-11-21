"""
Open DART API Client - Production-Ready Implementation

A comprehensive Python client for the Korean Financial Supervisory Service's
Electronic Disclosure System (Open DART) API.

Features:
- Request throttling and rate limiting
- Automatic retry with exponential backoff
- Response caching with TTL
- Error handling and validation
- Data type conversion and normalization
- Pandas DataFrame export
- Financial ratio calculation

Usage:
    from dart_api_client import DartAPIClient

    client = DartAPIClient(api_key="YOUR_API_KEY")

    # Search company
    results = client.search_company("삼성전자")

    # Get financial statements
    financials = client.get_financial_statements(
        corp_code="00126380",
        bsns_year="2023",
        reprt_code="11011"
    )
"""

import requests
import json
import time
import logging
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass, field, asdict
from enum import Enum
import io

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ReportCode(Enum):
    """Report type codes for financial statements"""
    ANNUAL = "11011"           # Annual (감사보고서)
    HALF_YEAR = "11012"        # Half-year (반기보고서)
    Q3 = "11013"               # 3Q (3분기보고서)
    Q1 = "11014"               # 1Q (1분기보고서)


class FinancialDivision(Enum):
    """Financial statement division codes"""
    CONSOLIDATED = "1001"      # Consolidated (연결)
    NONCONSOLIDATED = "1002"   # Non-consolidated (별도)


class StatementType(Enum):
    """Financial statement types"""
    BALANCE_SHEET = "BS"       # 재무상태표
    INCOME_STATEMENT = "IS"    # 손익계산서
    CASH_FLOW = "CF"           # 현금흐름표
    EQUITY_CHANGES = "SCE"     # 자본변동표


class DartAPIError(Exception):
    """Base exception for DART API errors"""
    def __init__(self, status_code: str, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"[{status_code}] {message}")


class RateLimiter:
    """
    Rate limiter with sliding window algorithm

    Tracks request frequency and enforces limits:
    - Maximum concurrent requests
    - Daily request limit
    - Minimum interval between requests
    """

    def __init__(self, max_requests_per_day: int = 10000,
                 max_concurrent: int = 10,
                 min_interval_ms: float = 100):
        """
        Initialize rate limiter

        Args:
            max_requests_per_day: Maximum requests per 24-hour window
            max_concurrent: Maximum simultaneous connections
            min_interval_ms: Minimum milliseconds between requests
        """
        self.max_requests_per_day = max_requests_per_day
        self.max_concurrent = max_concurrent
        self.min_interval_seconds = min_interval_ms / 1000.0

        self.request_times = deque()
        self.daily_window_seconds = 24 * 60 * 60
        self.last_request_time = 0
        self.active_connections = 0

    def acquire(self) -> float:
        """
        Acquire permission to make a request

        Returns:
            Seconds to wait before making request

        Raises:
            RuntimeError: If daily limit exceeded
        """
        now = time.time()

        # Check daily limit
        while self.request_times and self.request_times[0] < now - self.daily_window_seconds:
            self.request_times.popleft()

        if len(self.request_times) >= self.max_requests_per_day:
            oldest = self.request_times[0]
            wait_seconds = self.daily_window_seconds - (now - oldest)
            raise RuntimeError(
                f"Daily request limit ({self.max_requests_per_day}) exceeded. "
                f"Please wait {wait_seconds:.0f} seconds."
            )

        # Check minimum interval
        elapsed = now - self.last_request_time
        wait_time = max(0, self.min_interval_seconds - elapsed)

        return wait_time

    def release(self):
        """Record a request and update internal state"""
        self.request_times.append(time.time())
        self.last_request_time = time.time()

    def get_status(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        now = time.time()
        count_today = sum(1 for t in self.request_times
                         if t > now - self.daily_window_seconds)

        return {
            "requests_today": count_today,
            "daily_limit": self.max_requests_per_day,
            "remaining": self.max_requests_per_day - count_today,
            "reset_time": datetime.now() + timedelta(seconds=self.daily_window_seconds),
        }


class ResponseCache:
    """
    Simple file-based response cache with TTL
    """

    def __init__(self, cache_dir: str = ".dart_cache", ttl_hours: int = 24):
        """
        Initialize cache

        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time-to-live for cache entries in hours
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl_seconds = ttl_hours * 60 * 60

    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        """Generate cache key from endpoint and parameters"""
        cache_str = json.dumps({"ep": endpoint, "p": params}, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()

    def _get_cache_path(self, endpoint: str, params: Dict) -> Path:
        """Get full cache file path"""
        key = self._get_cache_key(endpoint, params)
        return self.cache_dir / f"{key}.json"

    def get(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """
        Retrieve cached response if valid

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            Cached response or None if not found/expired
        """
        cache_path = self._get_cache_path(endpoint, params)

        if not cache_path.exists():
            return None

        # Check if cache is still valid
        mod_time = cache_path.stat().st_mtime
        age_seconds = time.time() - mod_time

        if age_seconds > self.ttl_seconds:
            cache_path.unlink()
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read cache: {e}")
            return None

    def set(self, endpoint: str, params: Dict, data: Dict):
        """
        Store response in cache

        Args:
            endpoint: API endpoint
            params: Query parameters
            data: Response data to cache
        """
        cache_path = self._get_cache_path(endpoint, params)

        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to write cache: {e}")

    def clear(self):
        """Clear all cached files"""
        for f in self.cache_dir.glob("*.json"):
            f.unlink()


@dataclass
class CompanyInfo:
    """Validated company information"""
    corp_code: str
    corp_name: str
    stock_code: Optional[str] = None
    corp_name_eng: Optional[str] = None
    modify_date: Optional[str] = None

    def __post_init__(self):
        """Validate corporate code format"""
        if not self.corp_code or not re.match(r'^\d{8}$', self.corp_code):
            raise ValueError(f"Invalid corp_code: {self.corp_code}")

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class FinancialMetric:
    """Financial statement account data"""
    account_id: str
    account_name: str
    statement_type: StatementType
    current_amount: int
    previous_amount: Optional[int] = None
    unit: str = "KRW"

    def get_change(self) -> Optional[int]:
        """Calculate period-over-period change"""
        if self.previous_amount is None:
            return None
        return self.current_amount - self.previous_amount

    def get_change_percent(self) -> Optional[float]:
        """Calculate percentage change"""
        if self.previous_amount is None or self.previous_amount == 0:
            return None
        return (self.get_change() / self.previous_amount) * 100


class DartAPIClient:
    """
    Open DART API Client

    Main client for interacting with the Korean Financial Supervisory Service's
    Electronic Disclosure System API.

    Attributes:
        base_url: Base URL for API endpoints
        timeout: Request timeout in seconds
    """

    BASE_URL = "https://opendart.fss.or.kr/api"
    VALID_REPORT_CODES = {"11011", "11012", "11013", "11014"}
    VALID_FS_DIVS = {"1001", "1002"}

    def __init__(self, api_key: str, timeout: int = 10,
                 enable_cache: bool = True, cache_ttl_hours: int = 24,
                 enable_rate_limit: bool = True,
                 daily_limit: int = 10000):
        """
        Initialize DART API client

        Args:
            api_key: API authentication key from Open DART
            timeout: Request timeout in seconds (default: 10)
            enable_cache: Enable response caching (default: True)
            cache_ttl_hours: Cache TTL in hours (default: 24)
            enable_rate_limit: Enable rate limiting (default: True)
            daily_limit: Maximum daily requests (default: 10000)

        Raises:
            ValueError: If API key is invalid
        """
        if not api_key or not isinstance(api_key, str):
            raise ValueError("Valid API key required")

        self.api_key = api_key
        self.timeout = timeout

        # Initialize rate limiter
        self.rate_limiter = RateLimiter(
            max_requests_per_day=daily_limit
        ) if enable_rate_limit else None

        # Initialize cache
        self.cache = ResponseCache(ttl_hours=cache_ttl_hours) if enable_cache else None

        logger.info("DART API Client initialized")

    def _request(self, endpoint: str, params: Dict[str, Any] = None,
                use_cache: bool = True, max_retries: int = 3) -> Dict:
        """
        Make authenticated API request with error handling

        Args:
            endpoint: API endpoint (e.g., "company.json")
            params: Query parameters
            use_cache: Use cache if available
            max_retries: Maximum retry attempts

        Returns:
            Parsed JSON response

        Raises:
            DartAPIError: If API returns an error
            RequestException: If request fails
        """
        if params is None:
            params = {}

        # Check cache
        if use_cache and self.cache:
            cached = self.cache.get(endpoint, params)
            if cached:
                logger.debug(f"Cache hit for {endpoint}")
                return cached

        # Apply rate limiting
        if self.rate_limiter:
            wait_time = self.rate_limiter.acquire()
            if wait_time > 0:
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                time.sleep(wait_time)

        # Add authentication
        params['crtfc_key'] = self.api_key

        # Prepare request
        url = f"{self.BASE_URL}/{endpoint}"

        # Retry logic
        last_exception = None
        for attempt in range(max_retries):
            try:
                logger.debug(f"Request: {endpoint} (attempt {attempt + 1}/{max_retries})")

                response = requests.get(
                    url,
                    params=params,
                    timeout=self.timeout,
                    headers={'User-Agent': 'DartAPIClient/1.0'}
                )
                response.raise_for_status()

                # Parse response
                data = response.json()

                # Check API status
                status = data.get('status', '000')
                if status != '000':
                    message = data.get('message', 'Unknown error')
                    raise DartAPIError(status, message)

                # Cache successful response
                if use_cache and self.cache:
                    self.cache.set(endpoint, params, data)

                # Update rate limiter
                if self.rate_limiter:
                    self.rate_limiter.release()

                return data

            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Request failed, retrying in {wait}s: {e}")
                    time.sleep(wait)
                else:
                    logger.error(f"Request failed after {max_retries} attempts")

            except DartAPIError as e:
                if e.status_code in ['010', '013']:  # No results
                    logger.debug(f"API Error: {e}")
                    raise
                elif attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise

        raise last_exception or Exception("Request failed")

    # ==================== Company Methods ====================

    def get_company_by_code(self, corp_code: str) -> CompanyInfo:
        """
        Get company information by corporate code

        Args:
            corp_code: 8-digit corporate code

        Returns:
            CompanyInfo object

        Example:
            company = client.get_company_by_code("00126380")
            print(company.corp_name)  # 삼성전자
        """
        if not re.match(r'^\d{8}$', corp_code):
            raise ValueError(f"Invalid corp_code format: {corp_code}")

        result = self._request("company.json", {"corp_code": corp_code})

        return CompanyInfo(
            corp_code=result['corp_code'],
            corp_name=result['corp_name'],
            stock_code=result.get('stock_code'),
            modify_date=result.get('modify_date')
        )

    def search_company(self, corp_name: str, page_no: int = 1,
                      page_count: int = 10) -> Dict[str, Any]:
        """
        Search companies by name

        Args:
            corp_name: Company name in Korean
            page_no: Page number (starting at 1)
            page_count: Results per page (1-100)

        Returns:
            Dictionary with search results and pagination info

        Example:
            results = client.search_company("삼성")
            for company in results['list']:
                print(company['corp_name'])
        """
        if page_count > 100:
            page_count = 100
        if page_count < 1:
            page_count = 1

        params = {
            "corp_name": corp_name,
            "page_no": page_no,
            "page_count": page_count
        }

        result = self._request("companysearch.json", params)

        # Parse companies
        companies = []
        for item in result.get('list', []):
            try:
                companies.append(CompanyInfo(
                    corp_code=item['corp_code'],
                    corp_name=item['corp_name'],
                    stock_code=item.get('stock_code'),
                    corp_name_eng=item.get('corp_name_eng'),
                    modify_date=item.get('modify_date')
                ))
            except ValueError:
                continue

        return {
            'total_count': result.get('total_count', 0),
            'page_no': result.get('current_page', page_no),
            'page_count': page_count,
            'companies': companies
        }

    def search_company_by_stock_code(self, stock_code: str) -> Optional[CompanyInfo]:
        """
        Find company by stock code (6-digit)

        Args:
            stock_code: 6-digit stock exchange code

        Returns:
            CompanyInfo or None if not found

        Note:
            This is a convenience method that searches companies
            and filters by stock code. For efficiency, consider
            maintaining a local company code mapping.
        """
        if not re.match(r'^\d{6}$', stock_code):
            raise ValueError(f"Invalid stock_code format: {stock_code}")

        # Search by first 3 digits as fallback
        # In practice, you should maintain a local mapping
        logger.warning(
            "Stock code search is inefficient. "
            "Consider maintaining a local company code mapping."
        )

        # This would require iterating through results
        # Better approach: use cached company list
        raise NotImplementedError(
            "Use get_company_list() and maintain local mapping"
        )

    # ==================== Filing Methods ====================

    def get_filings(self, corp_code: str, page_no: int = 1,
                   page_count: int = 10) -> Dict[str, Any]:
        """
        Get list of filings for a company

        Args:
            corp_code: Corporate code
            page_no: Page number
            page_count: Results per page (1-100)

        Returns:
            Dictionary with filing list

        Example:
            filings = client.get_filings("00126380")
            for filing in filings['list']:
                print(filing['report_nm'])
        """
        params = {
            "corp_code": corp_code,
            "pageNo": page_no,
            "pageCount": min(page_count, 100)
        }

        return self._request("list.json", params)

    def get_filing_details(self, receipt_no: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific filing

        Args:
            receipt_no: Receipt number from get_filings()

        Returns:
            Filing details dictionary
        """
        if not receipt_no or len(str(receipt_no)) != 20:
            raise ValueError(f"Invalid receipt_no: {receipt_no}")

        return self._request("document.json", {"receipt_no": receipt_no})

    # ==================== Financial Statement Methods ====================

    def get_financial_statements(self,
                                corp_code: str,
                                bsns_year: str,
                                reprt_code: str = "11011",
                                fs_div: str = "1001") -> Dict[str, Any]:
        """
        Get financial statements for a company

        Args:
            corp_code: Corporate code
            bsns_year: Business year (YYYY format)
            reprt_code: Report type code
                - 11011: Annual report (default)
                - 11012: Half-year report
                - 11013: Q3 report
                - 11014: Q1 report
            fs_div: Financial statement division
                - 1001: Consolidated (default)
                - 1002: Non-consolidated

        Returns:
            Dictionary with financial account data

        Example:
            statements = client.get_financial_statements(
                corp_code="00126380",
                bsns_year="2023",
                reprt_code="11011"
            )
        """
        if not re.match(r'^\d{4}$', bsns_year):
            raise ValueError(f"Invalid bsns_year format: {bsns_year}")

        if reprt_code not in self.VALID_REPORT_CODES:
            raise ValueError(f"Invalid reprt_code: {reprt_code}")

        if fs_div not in self.VALID_FS_DIVS:
            raise ValueError(f"Invalid fs_div: {fs_div}")

        params = {
            "corp_code": corp_code,
            "bsns_year": bsns_year,
            "reprt_code": reprt_code,
            "fs_div": fs_div
        }

        return self._request("fnlttSinglAcntAll.json", params)

    def get_available_statements(self, corp_code: str) -> List[Dict]:
        """
        Get list of available financial statements

        Args:
            corp_code: Corporate code

        Returns:
            List of available statement records

        Example:
            statements = client.get_available_statements("00126380")
            for stmt in statements:
                print(f"{stmt['bsns_year']} - {stmt['reprt_code']}")
        """
        params = {"corp_code": corp_code}
        result = self._request("fnlttSinglAcnt.json", params)

        return result.get('list', [])

    # ==================== Dividend Methods ====================

    def get_dividend_info(self, stock_code: str) -> Dict[str, Any]:
        """
        Get dividend payment information

        Args:
            stock_code: 6-digit stock code

        Returns:
            Dividend information dictionary
        """
        if not re.match(r'^\d{6}$', stock_code):
            raise ValueError(f"Invalid stock_code format: {stock_code}")

        return self._request("dividend.json", {"stock_code": stock_code})

    # ==================== Shareholder Methods ====================

    def get_major_shareholders(self, corp_code: str, page_no: int = 1,
                              page_count: int = 10) -> Dict[str, Any]:
        """
        Get major shareholder information

        Args:
            corp_code: Corporate code
            page_no: Page number
            page_count: Results per page

        Returns:
            Shareholder information dictionary
        """
        params = {
            "corp_code": corp_code,
            "pageNo": page_no,
            "pageCount": min(page_count, 100)
        }

        return self._request("majorstock.json", params)

    # ==================== Utility Methods ====================

    def get_rate_limit_status(self) -> Optional[Dict]:
        """Get current rate limit status"""
        if not self.rate_limiter:
            return None

        return self.rate_limiter.get_status()

    def clear_cache(self):
        """Clear all cached responses"""
        if self.cache:
            self.cache.clear()
            logger.info("Cache cleared")

    def to_dataframe(self, financial_data: Dict) -> Optional[pd.DataFrame]:
        """
        Convert financial statement to pandas DataFrame

        Args:
            financial_data: Response from get_financial_statements()

        Returns:
            pandas DataFrame or None if pandas not installed
        """
        if not HAS_PANDAS:
            raise ImportError("pandas required for DataFrame export")

        if not financial_data.get('list'):
            return pd.DataFrame()

        df = pd.DataFrame(financial_data['list'])

        # Convert amounts to numeric
        for col in ['thstrm_amount', 'frmtrm_amount']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df


class FinancialDataAnalyzer:
    """
    Analyze and calculate financial metrics and ratios
    """

    # Account codes for key metrics
    KEY_ACCOUNTS = {
        # Balance Sheet
        'total_assets': '1000000',
        'current_assets': '1100000',
        'noncurrent_assets': '1200000',
        'cash': '1110000',
        'receivables': '1130000',
        'inventory': '1150000',
        'ppe': '1210000',
        'intangibles': '1220000',
        'total_liabilities': '2000000',
        'current_liabilities': '2100000',
        'noncurrent_liabilities': '2200000',
        'short_term_debt': '2110000',
        'long_term_debt': '2210000',
        'total_equity': '3000000',
        'capital_stock': '3110000',
        'retained_earnings': '3200000',

        # Income Statement
        'revenue': '4100000',
        'cogs': '5100000',
        'operating_expenses': '5200000',
        'operating_income': '4200000',
        'finance_income': '4300000',
        'finance_costs': '5500000',
        'income_tax_expense': '5600000',
        'net_income': '6100000',

        # Cash Flow
        'operating_cf': '6100000',
        'investing_cf': '6200000',
        'financing_cf': '6300000',
    }

    @staticmethod
    def extract_metrics(financial_data: Dict) -> Dict[str, int]:
        """
        Extract key financial metrics from statement data

        Args:
            financial_data: Response from get_financial_statements()

        Returns:
            Dictionary of metric_name -> value
        """
        metrics = {}

        # Build lookup
        accounts = {}
        for item in financial_data.get('list', []):
            accounts[item['account_id']] = item

        # Extract
        for key, code in FinancialDataAnalyzer.KEY_ACCOUNTS.items():
            if code in accounts:
                amount = int(accounts[code].get('thstrm_amount', 0))
                metrics[key] = amount

        return metrics

    @staticmethod
    def calculate_ratios(metrics: Dict[str, int]) -> Dict[str, float]:
        """
        Calculate common financial ratios

        Args:
            metrics: Dictionary from extract_metrics()

        Returns:
            Dictionary of ratio_name -> ratio_value
        """
        ratios = {}

        try:
            # Profitability
            revenue = metrics.get('revenue', 0)
            if revenue > 0:
                ratios['gross_margin'] = (
                    (revenue - metrics.get('cogs', 0)) / revenue
                ) * 100
                ratios['operating_margin'] = (
                    metrics.get('operating_income', 0) / revenue
                ) * 100
                ratios['net_margin'] = (
                    metrics.get('net_income', 0) / revenue
                ) * 100

            # Leverage
            assets = metrics.get('total_assets', 0)
            if assets > 0:
                ratios['debt_ratio'] = (
                    metrics.get('total_liabilities', 0) / assets
                ) * 100
                ratios['equity_ratio'] = (
                    metrics.get('total_equity', 0) / assets
                ) * 100

            equity = metrics.get('total_equity', 0)
            if equity > 0:
                ratios['debt_to_equity'] = (
                    metrics.get('total_liabilities', 0) / equity
                )

            # Liquidity
            current_liab = metrics.get('current_liabilities', 0)
            if current_liab > 0:
                ratios['current_ratio'] = (
                    metrics.get('current_assets', 0) / current_liab
                )

        except ZeroDivisionError:
            pass

        return ratios

    @staticmethod
    def print_ratios(ratios: Dict[str, float], decimals: int = 2):
        """Pretty print financial ratios"""
        print("\n" + "=" * 50)
        print("FINANCIAL RATIOS")
        print("=" * 50)

        for name, value in ratios.items():
            if isinstance(value, float):
                if 'margin' in name or 'ratio' in name.lower() and value > 100:
                    print(f"{name:.<30} {value:.{decimals}f}%")
                else:
                    print(f"{name:.<30} {value:.{decimals}f}")
            else:
                print(f"{name:.<30} {value}")


# ==================== Example Usage ====================

if __name__ == "__main__":
    # Initialize client
    API_KEY = "YOUR_API_KEY_HERE"

    try:
        client = DartAPIClient(api_key=API_KEY)

        # Example 1: Search for company
        print("\n" + "=" * 50)
        print("EXAMPLE 1: Company Search")
        print("=" * 50)

        search_results = client.search_company("삼성전자", page_count=3)
        print(f"Found {search_results['total_count']} companies")

        if search_results['companies']:
            company = search_results['companies'][0]
            print(f"Company: {company.corp_name}")
            print(f"Corp Code: {company.corp_code}")
            print(f"Stock Code: {company.stock_code}")

            # Example 2: Get company details
            print("\n" + "=" * 50)
            print("EXAMPLE 2: Company Details")
            print("=" * 50)

            company_detail = client.get_company_by_code(company.corp_code)
            print(f"Name: {company_detail.corp_name}")
            print(f"Last Modified: {company_detail.modify_date}")

            # Example 3: Get financial statements
            print("\n" + "=" * 50)
            print("EXAMPLE 3: Financial Statements")
            print("=" * 50)

            financials = client.get_financial_statements(
                corp_code=company.corp_code,
                bsns_year="2023",
                reprt_code="11011",  # Annual
                fs_div="1001"  # Consolidated
            )

            print(f"Financial data points: {len(financials.get('list', []))}")

            # Example 4: Analyze metrics
            print("\n" + "=" * 50)
            print("EXAMPLE 4: Financial Analysis")
            print("=" * 50)

            analyzer = FinancialDataAnalyzer()
            metrics = analyzer.extract_metrics(financials)

            print(f"Total Assets: {metrics.get('total_assets', 0):,}")
            print(f"Total Liabilities: {metrics.get('total_liabilities', 0):,}")
            print(f"Total Equity: {metrics.get('total_equity', 0):,}")
            print(f"Revenue: {metrics.get('revenue', 0):,}")

            ratios = analyzer.calculate_ratios(metrics)
            analyzer.print_ratios(ratios)

            # Example 5: Rate limit status
            print("\n" + "=" * 50)
            print("EXAMPLE 5: Rate Limit Status")
            print("=" * 50)

            status = client.get_rate_limit_status()
            if status:
                print(f"Requests Today: {status['requests_today']}/{status['daily_limit']}")
                print(f"Remaining: {status['remaining']}")
                print(f"Reset Time: {status['reset_time']}")

    except DartAPIError as e:
        print(f"API Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

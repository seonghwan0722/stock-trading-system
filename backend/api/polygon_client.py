#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Polygon.io API 클라이언트
실시간 및 과거 주식 데이터 제공

API 문서: https://polygon.io/docs/stocks
무료 티어: 5 calls/minute
"""

import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from backend.config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Config = get_config()


class PolygonClient:
    """Polygon.io API 클라이언트"""

    BASE_URL = "https://api.polygon.io"

    def __init__(self, api_key: Optional[str] = None):
        """
        Polygon 클라이언트 초기화

        Args:
            api_key: Polygon API 키 (없으면 환경변수에서 읽음)
        """
        self.api_key = api_key or Config.POLYGON_API_KEY

        if not self.api_key:
            logger.warning("⚠️  POLYGON_API_KEY가 설정되지 않았습니다.")
            logger.warning("    .env 파일에 POLYGON_API_KEY를 추가하세요.")
            logger.warning("    API 키 발급: https://polygon.io/dashboard/signup")

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """
        API 요청 실행

        Args:
            endpoint: API 엔드포인트
            params: 쿼리 파라미터

        Returns:
            API 응답 데이터
        """
        if not self.api_key:
            return {'status': 'ERROR', 'message': 'API key not configured'}

        url = f"{self.BASE_URL}{endpoint}"
        params = params or {}
        params['apiKey'] = self.api_key

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Polygon API 요청 실패: {e}")
            return {'status': 'ERROR', 'message': str(e)}

    def get_ticker_details(self, ticker: str) -> Dict[str, Any]:
        """
        종목 상세 정보 조회

        Args:
            ticker: 종목 심볼 (예: "AAPL")

        Returns:
            종목 상세 정보
        """
        endpoint = f"/v3/reference/tickers/{ticker}"
        data = self._make_request(endpoint)

        if data.get('status') == 'OK':
            results = data.get('results', {})
            return {
                'success': True,
                'ticker': results.get('ticker'),
                'name': results.get('name'),
                'market': results.get('market'),
                'primary_exchange': results.get('primary_exchange'),
                'currency': results.get('currency_name'),
                'type': results.get('type'),
                'description': results.get('description'),
                'homepage_url': results.get('homepage_url'),
                'total_employees': results.get('total_employees'),
                'list_date': results.get('list_date'),
                'market_cap': results.get('market_cap'),
            }

        return {'success': False, 'message': data.get('message', 'Unknown error')}

    def get_quote(self, ticker: str) -> Dict[str, Any]:
        """
        실시간 시세 조회 (Last Trade)

        Args:
            ticker: 종목 심볼

        Returns:
            현재 시세 정보
        """
        endpoint = f"/v2/last/trade/{ticker}"
        data = self._make_request(endpoint)

        if data.get('status') == 'OK':
            results = data.get('results', {})
            return {
                'success': True,
                'ticker': ticker,
                'price': results.get('p'),  # Price
                'size': results.get('s'),  # Size (shares)
                'exchange': results.get('x'),  # Exchange ID
                'timestamp': results.get('t'),  # Unix timestamp
            }

        return {'success': False, 'message': data.get('message', 'Unknown error')}

    def get_aggregates(self, ticker: str, multiplier: int = 1, timespan: str = 'day',
                       from_date: str = None, to_date: str = None, limit: int = 120) -> Dict[str, Any]:
        """
        집계 데이터 (OHLCV) 조회

        Args:
            ticker: 종목 심볼
            multiplier: 시간 단위 배수 (예: 1)
            timespan: 시간 단위 (minute/hour/day/week/month/quarter/year)
            from_date: 시작일 (YYYY-MM-DD)
            to_date: 종료일 (YYYY-MM-DD)
            limit: 최대 결과 수 (기본 120)

        Returns:
            OHLCV 데이터 리스트
        """
        # 기본 날짜 설정
        if not to_date:
            to_date = datetime.now().strftime('%Y-%m-%d')
        if not from_date:
            from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        endpoint = f"/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        params = {'limit': limit, 'sort': 'desc'}

        data = self._make_request(endpoint, params)

        if data.get('status') == 'OK' and data.get('resultsCount', 0) > 0:
            results = data.get('results', [])
            return {
                'success': True,
                'ticker': ticker,
                'count': len(results),
                'bars': [
                    {
                        'timestamp': bar.get('t'),
                        'open': bar.get('o'),
                        'high': bar.get('h'),
                        'low': bar.get('l'),
                        'close': bar.get('c'),
                        'volume': bar.get('v'),
                        'vwap': bar.get('vw'),  # Volume Weighted Average Price
                        'transactions': bar.get('n'),  # Number of transactions
                    }
                    for bar in results
                ]
            }

        return {'success': False, 'message': data.get('message', 'No data available')}

    def get_previous_close(self, ticker: str) -> Dict[str, Any]:
        """
        전일 종가 조회

        Args:
            ticker: 종목 심볼

        Returns:
            전일 OHLCV 데이터
        """
        endpoint = f"/v2/aggs/ticker/{ticker}/prev"
        data = self._make_request(endpoint)

        if data.get('status') == 'OK' and data.get('resultsCount', 0) > 0:
            results = data.get('results', [])[0]
            return {
                'success': True,
                'ticker': ticker,
                'timestamp': results.get('t'),
                'open': results.get('o'),
                'high': results.get('h'),
                'low': results.get('l'),
                'close': results.get('c'),
                'volume': results.get('v'),
                'vwap': results.get('vw'),
            }

        return {'success': False, 'message': data.get('message', 'No data available')}

    def get_snapshot(self, ticker: str) -> Dict[str, Any]:
        """
        종목 스냅샷 (현재가, 당일 변화, 전일 종가 포함)

        Args:
            ticker: 종목 심볼

        Returns:
            종합 시세 정보
        """
        endpoint = f"/v2/snapshot/locale/us/markets/stocks/tickers/{ticker}"
        data = self._make_request(endpoint)

        if data.get('status') == 'OK':
            ticker_data = data.get('ticker', {})
            day = ticker_data.get('day', {})
            prev_day = ticker_data.get('prevDay', {})
            last_trade = ticker_data.get('lastTrade', {})

            return {
                'success': True,
                'ticker': ticker,
                'updated': ticker_data.get('updated'),
                # 당일 데이터
                'today': {
                    'open': day.get('o'),
                    'high': day.get('h'),
                    'low': day.get('l'),
                    'close': day.get('c'),
                    'volume': day.get('v'),
                    'vwap': day.get('vw'),
                },
                # 전일 데이터
                'previous': {
                    'open': prev_day.get('o'),
                    'high': prev_day.get('h'),
                    'low': prev_day.get('l'),
                    'close': prev_day.get('c'),
                    'volume': prev_day.get('v'),
                    'vwap': prev_day.get('vw'),
                },
                # 마지막 거래
                'last_trade': {
                    'price': last_trade.get('p'),
                    'size': last_trade.get('s'),
                    'timestamp': last_trade.get('t'),
                },
                # 변화율
                'change_percent': ticker_data.get('todaysChangePerc', 0),
                'change': ticker_data.get('todaysChange', 0),
            }

        return {'success': False, 'message': data.get('message', 'Unknown error')}

    def search_tickers(self, search: str, limit: int = 10) -> Dict[str, Any]:
        """
        종목 검색

        Args:
            search: 검색어 (회사명 또는 심볼)
            limit: 최대 결과 수

        Returns:
            검색 결과 리스트
        """
        endpoint = "/v3/reference/tickers"
        params = {
            'search': search,
            'limit': limit,
            'active': True
        }

        data = self._make_request(endpoint, params)

        if data.get('status') == 'OK':
            results = data.get('results', [])
            return {
                'success': True,
                'count': len(results),
                'results': [
                    {
                        'ticker': r.get('ticker'),
                        'name': r.get('name'),
                        'market': r.get('market'),
                        'primary_exchange': r.get('primary_exchange'),
                        'type': r.get('type'),
                    }
                    for r in results
                ]
            }

        return {'success': False, 'message': data.get('message', 'Unknown error')}


# 싱글톤 인스턴스
_polygon_client = None


def get_polygon_client() -> PolygonClient:
    """Polygon 클라이언트 싱글톤 인스턴스 반환"""
    global _polygon_client
    if _polygon_client is None:
        _polygon_client = PolygonClient()
    return _polygon_client


if __name__ == "__main__":
    # 테스트
    client = get_polygon_client()

    print("\n=== Apple (AAPL) 종목 정보 ===")
    details = client.get_ticker_details("AAPL")
    if details.get('success'):
        print(f"Name: {details['name']}")
        print(f"Market: {details['market']}")
        print(f"Employees: {details.get('total_employees', 'N/A')}")

    print("\n=== Apple (AAPL) 스냅샷 ===")
    snapshot = client.get_snapshot("AAPL")
    if snapshot.get('success'):
        today = snapshot['today']
        print(f"Open: ${today['open']}")
        print(f"High: ${today['high']}")
        print(f"Low: ${today['low']}")
        print(f"Close: ${today['close']}")
        print(f"Change: {snapshot['change_percent']:.2f}%")

    print("\n=== 종목 검색: Tesla ===")
    search_results = client.search_tickers("Tesla", limit=3)
    if search_results.get('success'):
        for result in search_results['results']:
            print(f"{result['ticker']}: {result['name']}")

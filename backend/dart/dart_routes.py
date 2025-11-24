"""
DART API Routes for Flask Application
Open DART 금융감독원 전자공시 시스템 API 라우트
"""

from flask import Blueprint, jsonify, request
import sys
import os
from typing import Dict, List
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.auth import token_required
from backend.dart.dart_api_client import DartAPIClient, FinancialDataAnalyzer
from backend.database.mongo_db import get_database
from backend.config import get_config

logger = logging.getLogger(__name__)

# Get configuration
config = get_config()

# Blueprint 생성
dart_bp = Blueprint('dart', __name__, url_prefix='/api/dart')

# DART API 클라이언트 초기화
DART_API_KEY = config.DART_API_KEY
dart_client = DartAPIClient(api_key=DART_API_KEY) if DART_API_KEY else None

# MongoDB 초기화
db = None
try:
    db = get_database()
    logger.info('✅ DART routes: MongoDB initialized')
except Exception as e:
    logger.error(f'❌ DART routes: MongoDB initialization failed: {e}')

# Companies collection
dart_companies = db.dart_companies if db else None


# ==================== 종목 검색 API ====================

@dart_bp.route('/stocks/all', methods=['GET'])
def get_all_stocks():
    """
    모든 상장 종목 조회

    Query Parameters:
        market: (optional) 시장 구분 (KOSPI, KOSDAQ, KONEX)

    Returns:
        {
            "success": true,
            "data": [...],
            "count": 1234,
            "market_stats": {"KOSPI": 800, "KOSDAQ": 400}
        }
    """
    if dart_companies is None:
        return jsonify({'success': False, 'error': 'Database not available'}), 503

    try:
        market_type = request.args.get('market')

        # Query MongoDB
        query = {}
        if market_type:
            query['market_type'] = market_type

        stocks = list(dart_companies.find(query, {'_id': 0}).limit(5000))

        # Transform data to match frontend expectations
        transformed_stocks = []
        for stock in stocks:
            transformed_stocks.append({
                'stock_code': stock.get('stock_code'),
                'corp_code': stock.get('corp_code'),
                'company_name': stock.get('name'),  # Transform 'name' to 'company_name'
                'market_type': stock.get('market_type', 'UNKNOWN'),
                'modify_date': stock.get('modify_date')
            })

        # Calculate market stats
        market_stats = {}
        for market in ['KOSPI', 'KOSDAQ', 'KONEX']:
            count = dart_companies.count_documents({'market_type': market})
            if count > 0:
                market_stats[market] = count

        return jsonify({
            'success': True,
            'data': transformed_stocks,
            'count': len(transformed_stocks),
            'market_stats': market_stats
        })

    except Exception as e:
        logger.error(f"Get all stocks error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'종목 조회 실패: {str(e)}'
        }), 500


@dart_bp.route('/stocks/search', methods=['GET'])
def search_stocks():
    """
    종목 검색 (이름, 코드, 초성)

    Query Parameters:
        q: 검색어 (최소 2글자)
        limit: 결과 제한 (기본: 20)

    Returns:
        {
            "success": true,
            "data": [...],
            "count": 5,
            "query": "삼성"
        }
    """
    if dart_companies is None:
        return jsonify({'success': False, 'error': 'Database not available'}), 503

    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 20))

        if len(query) < 2:
            return jsonify({
                'success': False,
                'message': '최소 2글자 이상 입력하세요.',
                'data': []
            }), 400

        # MongoDB regex search
        search_query = {
            '$or': [
                {'name': {'$regex': query, '$options': 'i'}},
                {'stock_code': {'$regex': query}},
                {'corp_code': {'$regex': query}}
            ]
        }

        results = list(dart_companies.find(search_query, {'_id': 0}).limit(min(limit, 100)))

        # Transform data to match frontend expectations
        # Database stores 'name', but frontend expects 'company_name'
        transformed_results = []
        for result in results:
            transformed_results.append({
                'stock_code': result.get('stock_code'),
                'corp_code': result.get('corp_code'),
                'company_name': result.get('name'),  # Transform 'name' to 'company_name'
                'market_type': result.get('market_type', 'UNKNOWN'),
                'modify_date': result.get('modify_date')
            })

        return jsonify({
            'success': True,
            'data': transformed_results,
            'count': len(transformed_results),
            'query': query
        })

    except Exception as e:
        logger.error(f"Stock search error: {e}")
        return jsonify({
            'success': False,
            'message': f'검색 실패: {str(e)}',
            'data': []
        }), 500


@dart_bp.route('/stocks/<stock_code>', methods=['GET'])
def get_stock_by_code(stock_code: str):
    """
    종목 코드로 종목 정보 조회

    Parameters:
        stock_code: 6자리 종목 코드

    Returns:
        {
            "success": true,
            "data": {...}
        }
    """
    try:
        stock = dart_companies.find_one({'stock_code': stock_code}, {'_id': 0})

        if not stock:
            return jsonify({
                'success': False,
                'message': '종목을 찾을 수 없습니다.'
            }), 404

        # Transform data to match frontend expectations
        transformed_stock = {
            'stock_code': stock.get('stock_code'),
            'corp_code': stock.get('corp_code'),
            'company_name': stock.get('name'),  # Transform 'name' to 'company_name'
            'market_type': stock.get('market_type', 'UNKNOWN'),
            'modify_date': stock.get('modify_date')
        }

        return jsonify({
            'success': True,
            'data': transformed_stock
        })

    except Exception as e:
        logger.error(f"Get stock error: {e}")
        return jsonify({
            'success': False,
            'message': f'조회 실패: {str(e)}'
        }), 500


# ==================== DART 재무제표 API ====================

@dart_bp.route('/financials/<corp_code>', methods=['GET'])
@token_required
def get_financial_statements(corp_code: str):
    """
    재무제표 조회

    Parameters:
        corp_code: 8자리 DART 고유번호

    Query Parameters:
        year: 사업연도 (YYYY)
        report_type: 보고서 종류 (11011: 사업보고서, 11012: 반기, 11013: 3분기, 11014: 1분기)
        fs_div: 재무제표 구분 (1001: 연결, 1002: 별도)

    Returns:
        {
            "success": true,
            "company": {...},
            "financials": {...},
            "metrics": {...},
            "ratios": {...}
        }
    """
    if not dart_client:
        return jsonify({
            'success': False,
            'message': 'DART API 키가 설정되지 않았습니다.'
        }), 500

    try:
        year = request.args.get('year', '2023')
        report_type = request.args.get('report_type', '11011')
        fs_div = request.args.get('fs_div', '1001')

        # 회사 정보 조회
        company_info = dart_client.get_company_by_code(corp_code)

        # 재무제표 조회
        financial_data = dart_client.get_financial_statements(
            corp_code=corp_code,
            bsns_year=year,
            reprt_code=report_type,
            fs_div=fs_div
        )

        # 재무 지표 추출
        analyzer = FinancialDataAnalyzer()
        metrics = analyzer.extract_metrics(financial_data)
        ratios = analyzer.calculate_ratios(metrics)

        return jsonify({
            'success': True,
            'company': company_info.to_dict(),
            'financials': financial_data,
            'metrics': metrics,
            'ratios': ratios,
            'year': year,
            'report_type': report_type
        })

    except Exception as e:
        logger.error(f"Get financials error: {e}")
        return jsonify({
            'success': False,
            'message': f'재무제표 조회 실패: {str(e)}'
        }), 500


@dart_bp.route('/financials/<corp_code>/available', methods=['GET'])
@token_required
def get_available_statements(corp_code: str):
    """
    이용 가능한 재무제표 목록 조회

    Parameters:
        corp_code: 8자리 DART 고유번호

    Returns:
        {
            "success": true,
            "statements": [...]
        }
    """
    if not dart_client:
        return jsonify({
            'success': False,
            'message': 'DART API 키가 설정되지 않았습니다.'
        }), 500

    try:
        statements = dart_client.get_available_statements(corp_code)

        return jsonify({
            'success': True,
            'statements': statements,
            'count': len(statements)
        })

    except Exception as e:
        logger.error(f"Get available statements error: {e}")
        return jsonify({
            'success': False,
            'message': f'재무제표 목록 조회 실패: {str(e)}'
        }), 500


@dart_bp.route('/company/<corp_code>', methods=['GET'])
@token_required
def get_company_info(corp_code: str):
    """
    기업 정보 조회

    Parameters:
        corp_code: 8자리 DART 고유번호

    Returns:
        {
            "success": true,
            "company": {...}
        }
    """
    if not dart_client:
        return jsonify({
            'success': False,
            'message': 'DART API 키가 설정되지 않았습니다.'
        }), 500

    try:
        company = dart_client.get_company_by_code(corp_code)

        return jsonify({
            'success': True,
            'company': company.to_dict()
        })

    except Exception as e:
        logger.error(f"Get company info error: {e}")
        return jsonify({
            'success': False,
            'message': f'기업 정보 조회 실패: {str(e)}'
        }), 500


@dart_bp.route('/filings/<corp_code>', methods=['GET'])
@token_required
def get_filings(corp_code: str):
    """
    공시 목록 조회

    Parameters:
        corp_code: 8자리 DART 고유번호

    Query Parameters:
        page: 페이지 번호 (기본: 1)
        count: 페이지당 결과 수 (기본: 10)

    Returns:
        {
            "success": true,
            "filings": [...]
        }
    """
    if not dart_client:
        return jsonify({
            'success': False,
            'message': 'DART API 키가 설정되지 않았습니다.'
        }), 500

    try:
        page = int(request.args.get('page', 1))
        count = int(request.args.get('count', 10))

        filings = dart_client.get_filings(
            corp_code=corp_code,
            page_no=page,
            page_count=min(count, 100)
        )

        return jsonify({
            'success': True,
            'filings': filings
        })

    except Exception as e:
        logger.error(f"Get filings error: {e}")
        return jsonify({
            'success': False,
            'message': f'공시 조회 실패: {str(e)}'
        }), 500


# ==================== 배당 정보 API ====================

@dart_bp.route('/dividend/<stock_code>', methods=['GET'])
@token_required
def get_dividend_info(stock_code: str):
    """
    배당 정보 조회

    Parameters:
        stock_code: 6자리 종목 코드

    Returns:
        {
            "success": true,
            "dividend": {...}
        }
    """
    if not dart_client:
        return jsonify({
            'success': False,
            'message': 'DART API 키가 설정되지 않았습니다.'
        }), 500

    try:
        dividend = dart_client.get_dividend_info(stock_code)

        return jsonify({
            'success': True,
            'dividend': dividend
        })

    except Exception as e:
        logger.error(f"Get dividend error: {e}")
        return jsonify({
            'success': False,
            'message': f'배당 정보 조회 실패: {str(e)}'
        }), 500


# ==================== 주주 정보 API ====================

@dart_bp.route('/shareholders/<corp_code>', methods=['GET'])
@token_required
def get_major_shareholders(corp_code: str):
    """
    주요 주주 정보 조회

    Parameters:
        corp_code: 8자리 DART 고유번호

    Query Parameters:
        page: 페이지 번호 (기본: 1)
        count: 페이지당 결과 수 (기본: 10)

    Returns:
        {
            "success": true,
            "shareholders": {...}
        }
    """
    if not dart_client:
        return jsonify({
            'success': False,
            'message': 'DART API 키가 설정되지 않았습니다.'
        }), 500

    try:
        page = int(request.args.get('page', 1))
        count = int(request.args.get('count', 10))

        shareholders = dart_client.get_major_shareholders(
            corp_code=corp_code,
            page_no=page,
            page_count=min(count, 100)
        )

        return jsonify({
            'success': True,
            'shareholders': shareholders
        })

    except Exception as e:
        logger.error(f"Get shareholders error: {e}")
        return jsonify({
            'success': False,
            'message': f'주주 정보 조회 실패: {str(e)}'
        }), 500


# ==================== 시스템 상태 API ====================

@dart_bp.route('/status', methods=['GET'])
def get_dart_status():
    """
    DART API 상태 조회

    Returns:
        {
            "api_configured": true,
            "database_ready": true,
            "stock_count": 1234,
            "rate_limit_status": {...}
        }
    """
    try:
        status = {
            'api_configured': dart_client is not None,
            'database_ready': True,
            'stock_count': dart_companies.count_documents({}),
            'last_update': 'N/A',  # MongoDB doesn't track this automatically
            'market_stats': {'kospi': 0, 'kosdaq': 0}  # Simplified
        }

        if dart_client:
            rate_limit = dart_client.get_rate_limit_status()
            if rate_limit:
                status['rate_limit_status'] = rate_limit

        return jsonify(status)

    except Exception as e:
        logger.error(f"Get status error: {e}")
        return jsonify({
            'api_configured': False,
            'database_ready': False,
            'error': str(e)
        }), 500


# ==================== 유틸리티 함수 ====================

def format_financial_data(financial_data: Dict) -> Dict:
    """
    재무 데이터를 UI에 표시하기 좋은 형태로 변환

    Args:
        financial_data: Raw financial data from DART API

    Returns:
        Formatted data dictionary
    """
    # 재무 항목을 카테고리별로 그룹화
    balance_sheet = []
    income_statement = []
    cash_flow = []

    for item in financial_data.get('list', []):
        sj_div = item.get('sj_div', '')

        if 'BS' in sj_div:  # Balance Sheet
            balance_sheet.append(item)
        elif 'IS' in sj_div:  # Income Statement
            income_statement.append(item)
        elif 'CF' in sj_div:  # Cash Flow
            cash_flow.append(item)

    return {
        'balance_sheet': balance_sheet,
        'income_statement': income_statement,
        'cash_flow': cash_flow
    }


def initialize_dart_module():
    """DART 모듈 초기화 함수 (앱 시작 시 호출)"""
    global dart_client

    # API 키 확인
    if not DART_API_KEY:
        logger.warning("DART_API_KEY not configured")

    # MongoDB 연결 확인
    try:
        count = dart_companies.count_documents({})
        logger.info(f"DART companies database ready with {count} companies")
    except Exception as e:
        logger.error(f"DART companies database initialization error: {e}")


# Blueprint에 초기화 함수 추가
# Flask 3.0+에서는 before_app_first_request가 제거됨
# app.py에서 직접 호출하도록 변경

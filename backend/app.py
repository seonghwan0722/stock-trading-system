from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
import schedule
import threading
import time
from datetime import datetime
import sys
import os
import logging
from logging.handlers import RotatingFileHandler

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# New imports - MongoDB and Free APIs
from backend.config import get_config
from backend.auth import token_required, get_auth_manager
from backend.database.mongo_db import get_database, get_user_manager, get_trading_manager
from backend.api.finnhub_client import get_finnhub_client
from backend.api.alphavantage_client import get_alphavantage_client
from backend.api.kiwoom_rest_client import get_kiwoom_rest_client
from backend.routes.user_routes import user_bp

# Existing imports
from backend.trading.buy_strategy import BuyStrategy
from backend.trading.sell_strategy import SellStrategy
from backend.news.news_summary import NewsSummarizer
from backend.telegram_notifier.bot import TelegramNotifier, get_telegram_notifier
from backend.trading.strategy_manager import get_strategy_manager
from backend.scraper.capitol_trades_scraper import CapitolTradesScraper
from backend.scraper.stocknear_scraper import scrape_stocknear_sync
from backend.scraper.stock_analysis_scraper import StockAnalysisScraper
from backend.scraper.chart_exchange_scraper import ChartExchangeScraper
from backend.dart.dart_routes import dart_bp, initialize_dart_module

# Initialize configuration
config = get_config()

# Initialize Flask app
app = Flask(__name__, static_folder='../frontend')
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

# Security: CORS with whitelist
CORS(app, resources={
    r"/api/*": {
        "origins": config.CORS_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "max_age": 3600
    }
})

# Security: Rate Limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[config.RATELIMIT_DEFAULT],
    storage_uri=config.RATELIMIT_STORAGE_URL,
    enabled=config.RATELIMIT_ENABLED
)

# Security: HTTPS enforcement and headers (only in production)
if config.ENVIRONMENT == 'production':
    Talisman(app, force_https=True, strict_transport_security=True)

# Security: Add security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# Logging setup
if not os.path.exists('logs'):
    os.makedirs('logs')

file_handler = RotatingFileHandler(
    config.LOG_FILE,
    maxBytes=10240000,  # 10MB
    backupCount=10
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)

app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info(f'Stock Trading System startup - Environment: {config.ENVIRONMENT}')

# Register Blueprints
app.register_blueprint(dart_bp)
app.register_blueprint(user_bp)  # NEW: User management routes

# Initialize DART module (Flask 3.0+ compatibility)
with app.app_context():
    initialize_dart_module()

# Initialize services
try:
    # New MongoDB-based services
    db = get_database()
    user_manager = get_user_manager()
    trading_manager = get_trading_manager()
    auth_manager = get_auth_manager()

    # New Free API clients
    finnhub_client = get_finnhub_client()
    alphavantage_client = get_alphavantage_client()

    app.logger.info('✅ MongoDB and Free API clients initialized')
except Exception as e:
    app.logger.error(f'❌ Failed to initialize MongoDB/APIs: {e}')
    # Continue without MongoDB for now (degraded mode)
    db = None
    finnhub_client = None
    alphavantage_client = None

# Existing services
buy_strategy = BuyStrategy()
sell_strategy = SellStrategy()
news_summarizer = NewsSummarizer()
telegram_notifier = TelegramNotifier()
strategy_manager = get_strategy_manager()


# ==================== 인증 API (DEPRECATED - Use /api/user/login) ====================

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")  # Rate limiting for brute force protection
def login():
    """
    DEPRECATED: Use /api/user/login instead
    Legacy login endpoint for backwards compatibility
    """
    app.logger.warning('Legacy /api/auth/login endpoint used. Migrate to /api/user/login')

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Use new auth manager
    result = auth_manager.authenticate(username, password) if auth_manager else None

    if result and result.get('success'):
        return jsonify({
            'success': True,
            'token': result.get('access_token'),
            'refresh_token': result.get('refresh_token'),
            'message': '로그인 성공'
        })
    else:
        return jsonify({
            'success': False,
            'message': '아이디 또는 비밀번호가 올바르지 않습니다.'
        }), 401


# ==================== 계좌 정보 API (MongoDB) ====================

@app.route('/api/account/balance', methods=['GET'])
@token_required
def get_balance(current_user):
    """계좌 잔고 조회 - 키움 REST API에서 실제 계좌 정보 가져오기"""
    try:
        # 키움 REST API 클라이언트 가져오기
        kiwoom_client = get_kiwoom_rest_client(is_mock=True)

        # 토큰이 없으면 발급
        if not kiwoom_client.access_token:
            token_result = kiwoom_client.get_access_token()
            if not token_result.get('success'):
                # 토큰 발급 실패 시 MongoDB 데이터 사용
                app.logger.warning('키움 API 토큰 발급 실패, MongoDB 데이터 사용')
                return get_balance_from_mongodb(current_user)

        # 키움 API에서 계좌 정보 가져오기
        balance_result = kiwoom_client.get_account_balance()

        if balance_result.get('success'):
            return jsonify({
                'success': True,
                'total_balance': balance_result.get('total_balance', 0),
                'total_purchase': balance_result.get('total_purchase', 0),
                'total_profit_loss': balance_result.get('total_profit_loss', 0),
                'available_cash': balance_result.get('total_balance', 0) - balance_result.get('total_purchase', 0),
                'positions': balance_result.get('positions', [])
            })
        else:
            # 키움 API 실패 시 MongoDB 데이터 사용
            app.logger.warning(f'키움 API 조회 실패: {balance_result.get("message")}, MongoDB 데이터 사용')
            return get_balance_from_mongodb(current_user)

    except Exception as e:
        app.logger.error(f'키움 API 오류: {e}', exc_info=True)
        # 오류 발생 시 MongoDB 데이터 사용
        return get_balance_from_mongodb(current_user)


def get_balance_from_mongodb(current_user):
    """MongoDB에서 포트폴리오 조회 (백업용)"""
    if not trading_manager:
        return jsonify({'success': False, 'error': 'Database not available'}), 503

    try:
        portfolio = trading_manager.get_portfolio(current_user['user_id'])

        total_value = 0
        for position in portfolio:
            # Get current price from Finnhub
            if finnhub_client:
                quote = finnhub_client.get_quote(position['stock_code'])
                current_price = quote.get('c', position['avg_price'])
                position['current_price'] = current_price
                position['profit_loss'] = (current_price - position['avg_price']) * position['quantity']
                total_value += current_price * position['quantity']

        return jsonify({
            'success': True,
            'total_balance': total_value,
            'total_purchase': sum(p['avg_price'] * p['quantity'] for p in portfolio),
            'total_profit_loss': sum(p.get('profit_loss', 0) for p in portfolio),
            'available_cash': 0,
            'positions': portfolio
        })

    except Exception as e:
        app.logger.error(f'Error getting balance from MongoDB: {e}', exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to retrieve balance'}), 500


@app.route('/api/stocks/hot', methods=['GET'])
@token_required
def get_hot_stocks(current_user):
    """실시간 인기 주식 조회"""
    try:
        # 한국 인기 주식 (코스피 대장주)
        hot_stocks = [
            {'code': '005930', 'name': '삼성전자', 'market': 'KOSPI'},
            {'code': '000660', 'name': 'SK하이닉스', 'market': 'KOSPI'},
            {'code': '035420', 'name': 'NAVER', 'market': 'KOSPI'},
            {'code': '005380', 'name': '현대차', 'market': 'KOSPI'},
            {'code': '006400', 'name': '삼성SDI', 'market': 'KOSPI'},
            {'code': '035720', 'name': '카카오', 'market': 'KOSDAQ'},
            {'code': '051910', 'name': 'LG화학', 'market': 'KOSPI'},
            {'code': '068270', 'name': '셀트리온', 'market': 'KOSDAQ'},
        ]

        # 키움 REST API로 각 종목의 현재가 조회
        kiwoom_client = get_kiwoom_rest_client(is_mock=True)
        if not kiwoom_client.access_token:
            kiwoom_client.get_access_token()

        enriched_stocks = []
        for stock in hot_stocks:
            price_result = kiwoom_client.get_stock_price(stock['code'])
            if price_result.get('success'):
                enriched_stocks.append({
                    'code': stock['code'],
                    'name': stock['name'],
                    'market': stock['market'],
                    'current_price': price_result.get('current_price', 0),
                    'change_rate': price_result.get('change_rate', 0),
                    'volume': price_result.get('volume', 0)
                })
            else:
                # API 실패 시 기본 정보만 반환
                enriched_stocks.append(stock)

        return jsonify({
            'success': True,
            'stocks': enriched_stocks
        })

    except Exception as e:
        app.logger.error(f'인기 주식 조회 오류: {e}', exc_info=True)
        # 오류 시 기본 리스트 반환
        return jsonify({
            'success': True,
            'stocks': [
                {'code': '005930', 'name': '삼성전자', 'market': 'KOSPI'},
                {'code': '000660', 'name': 'SK하이닉스', 'market': 'KOSPI'},
                {'code': '035420', 'name': 'NAVER', 'market': 'KOSPI'},
                {'code': '005380', 'name': '현대차', 'market': 'KOSPI'},
            ]
        })


@app.route('/api/account/positions', methods=['GET'])
@token_required
def get_positions(current_user):
    """보유 종목 조회"""
    if not trading_manager:
        return jsonify({'success': False, 'error': 'Database not available'}), 503

    try:
        portfolio = trading_manager.get_portfolio(current_user['user_id'])

        return jsonify({
            'success': True,
            'positions': portfolio
        })

    except Exception as e:
        app.logger.error(f'Error getting positions: {e}', exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to retrieve positions'}), 500


# ==================== 주식 정보 API (Finnhub) ====================

@app.route('/api/stock/price/<stock_code>', methods=['GET'])
@token_required
def get_stock_price(stock_code, current_user):
    """주식 현재가 조회 - Finnhub API 사용"""
    if not finnhub_client:
        return jsonify({'success': False, 'error': 'Stock API not available'}), 503

    try:
        # Get quote from Finnhub
        quote = finnhub_client.get_quote(stock_code)

        if quote and not quote.get('error'):
            return jsonify({
                'success': True,
                'data': {
                    'current_price': quote.get('c'),
                    'high': quote.get('h'),
                    'low': quote.get('l'),
                    'open': quote.get('o'),
                    'previous_close': quote.get('pc'),
                    'timestamp': quote.get('t')
                }
            })
        else:
            return jsonify({'success': False, 'message': '종목 정보를 가져올 수 없습니다.'})

    except Exception as e:
        app.logger.error(f'Error getting stock price: {e}', exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to retrieve stock price'}), 500


@app.route('/api/stock/detail/<stock_code>', methods=['GET'])
@token_required
def get_stock_detail(stock_code):
    """주식 상세정보 조회 (재무제표, 밸류에이션 등)"""
    try:
        # 기본 가격 정보
        price_info = kis_api.get_current_price(stock_code)
        if not price_info:
            return jsonify({'success': False, 'message': '종목 정보를 가져올 수 없습니다.'})

        # 상세 정보를 구성 (실제로는 KIS API나 다른 금융 데이터 API 호출 필요)
        # 여기서는 데모용으로 샘플 데이터를 반환
        stock_detail = {
            # 기본 정보
            'current_price': price_info.get('current_price', 0),
            'change_rate': price_info.get('change_rate', 0),
            'volume': price_info.get('volume', 0),
            'trading_value': price_info.get('volume', 0) * price_info.get('current_price', 0),

            # 시가총액 및 주식 정보
            'market_cap': price_info.get('current_price', 0) * 1000000000,  # 예시
            'listed_shares': 1000000000,  # 예시
            'week52_high': int(price_info.get('current_price', 0) * 1.3),
            'week52_low': int(price_info.get('current_price', 0) * 0.7),

            # 재무제표 - 손익계산서 (억원 단위)
            'revenue': 500000000000,  # 예시: 5조원
            'operating_profit': 100000000000,  # 예시: 1조원
            'net_income': 80000000000,  # 예시: 8천억원
            'operating_margin': 20.0,  # 영업이익률 20%
            'net_margin': 16.0,  # 순이익률 16%

            # 재무제표 - 재무상태표
            'total_assets': 1000000000000,  # 예시: 10조원
            'total_liabilities': 300000000000,  # 예시: 3조원
            'total_equity': 700000000000,  # 예시: 7조원
            'debt_ratio': 42.86,  # 부채비율 = (부채/자본) * 100

            # 밸류에이션 지표
            'per': 12.5,  # 주가수익비율
            'pbr': 1.2,  # 주가순자산비율
            'psr': 0.8,  # 주가매출비율
            'pcr': 8.0,  # 주가현금흐름비율
            'roe': 14.3,  # 자기자본이익률
            'roa': 8.0,  # 총자산이익률
            'eps': 5000,  # 주당순이익
            'bps': 35000,  # 주당순자산
            'dividend_yield': 2.5,  # 배당수익률

            # 업종 평균 (비교용)
            'sector_avg_per': 15.0,
            'sector_avg_pbr': 1.5,

            # 기술적 지표
            'rsi': 55.0,  # RSI (14일)
            'macd': 120.0,  # MACD
            'macd_signal': '상승',
            'ma20': int(price_info.get('current_price', 0) * 0.98),  # 20일 이동평균
            'ma60': int(price_info.get('current_price', 0) * 0.95),  # 60일 이동평균
            'bb_upper': int(price_info.get('current_price', 0) * 1.05),  # 볼린저밴드 상단
            'bb_lower': int(price_info.get('current_price', 0) * 0.95),  # 볼린저밴드 하단
        }

        # 실제 구현 시에는 kis_api에 메서드를 추가하거나
        # 별도의 금융 데이터 API를 호출하여 실제 데이터를 가져와야 합니다
        # 예: dart_api (전자공시), fnguide, investing.com 등

        return jsonify({
            'success': True,
            'data': stock_detail
        })

    except Exception as e:
        print(f"주식 상세정보 조회 오류: {e}")
        return jsonify({
            'success': False,
            'message': f'상세정보 조회 중 오류 발생: {str(e)}'
        })


# ==================== AI 매매 분석 API ====================

@app.route('/api/trading/analyze-buy', methods=['POST'])
@token_required
def analyze_buy():
    """매수 분석"""
    data = request.get_json()
    stock_code = data.get('stock_code')
    stock_name = data.get('stock_name')
    additional_info = data.get('additional_info')

    if not stock_code or not stock_name:
        return jsonify({'success': False, 'message': '종목 코드와 이름을 입력해주세요.'})

    result = buy_strategy.analyze_stock_for_buy(stock_code, stock_name, additional_info)
    return jsonify({'success': True, 'analysis': result})


@app.route('/api/trading/analyze-sell', methods=['POST'])
@token_required
def analyze_sell():
    """매도 분석"""
    data = request.get_json()
    position = data.get('position')
    additional_info = data.get('additional_info')

    if not position:
        return jsonify({'success': False, 'message': '포지션 정보를 입력해주세요.'})

    result = sell_strategy.analyze_stock_for_sell(position, additional_info)
    return jsonify({'success': True, 'analysis': result})


# ==================== 매매 실행 API ====================

@app.route('/api/trading/buy', methods=['POST'])
@token_required
def execute_buy():
    """매수 실행"""
    data = request.get_json()
    stock_code = data.get('stock_code')
    stock_name = data.get('stock_name', stock_code)
    quantity = data.get('quantity')
    price = data.get('price', 0)

    if not stock_code or not quantity:
        return jsonify({'success': False, 'message': '종목 코드와 수량을 입력해주세요.'})

    # 매수 실행
    result = kis_api.buy_stock(stock_code, quantity, price)

    # 텔레그램 알림
    if result.get('success'):
        telegram_notifier.send_trade_notification(
            'BUY', stock_code, stock_name, quantity, price or 0,
            reason="수동 매수"
        )

    return jsonify(result)


@app.route('/api/trading/sell', methods=['POST'])
@token_required
def execute_sell():
    """매도 실행"""
    data = request.get_json()
    stock_code = data.get('stock_code')
    stock_name = data.get('stock_name', stock_code)
    quantity = data.get('quantity')
    price = data.get('price', 0)

    if not stock_code or not quantity:
        return jsonify({'success': False, 'message': '종목 코드와 수량을 입력해주세요.'})

    # 매도 실행
    result = kis_api.sell_stock(stock_code, quantity, price)

    # 텔레그램 알림
    if result.get('success'):
        telegram_notifier.send_trade_notification(
            'SELL', stock_code, stock_name, quantity, price or 0,
            reason="수동 매도"
        )

    return jsonify(result)


# ==================== 뉴스 API ====================

@app.route('/api/news/summary', methods=['GET'])
@token_required
def get_news_summary():
    """뉴스 요약 조회"""
    news_list = news_summarizer.gather_all_news()
    summary = news_summarizer.summarize_news_with_ai(news_list)

    return jsonify({
        'success': True,
        'summary': summary,
        'news_count': len(news_list)
    })


@app.route('/api/news/sentiment', methods=['GET'])
@token_required
def get_market_sentiment(current_user):
    """시장 심리 분석"""
    news_list = news_summarizer.gather_all_news()
    sentiment = news_summarizer.get_market_sentiment(news_list)

    return jsonify({
        'success': True,
        'sentiment': sentiment
    })


@app.route('/api/recommendations/stocks', methods=['GET'])
@token_required
def get_stock_recommendations():
    """AI 기반 추천 종목 조회"""
    try:
        # 샘플 추천 종목 목록 (실제로는 AI 분석 기반으로 추천)
        # 실제 구현 시에는 buy_strategy.recommend_stocks() 등의 메서드 사용
        sample_recommendations = [
            {
                'stock_code': '005930',
                'stock_name': '삼성전자',
                'current_price': 70000,
                'confidence': 85,
                'expected_return': 15,
                'target_price': 80500,
                'investment_period': '3-6개월',
                'reason': '반도체 시장 회복세와 함께 메모리 가격 상승세가 지속되고 있습니다. AI 및 데이터센터 수요 증가로 HBM 사업 확대가 예상됩니다.',
                'pros': [
                    '글로벌 반도체 시장 1위 기업',
                    'AI 반도체 수요 증가로 수혜 전망',
                    '안정적인 배당 정책',
                    '강력한 브랜드 파워와 기술력'
                ],
                'risks': [
                    '중국 경기 둔화 영향',
                    '반도체 업황 사이클 변동성',
                    '환율 변동 리스크'
                ]
            },
            {
                'stock_code': '000660',
                'stock_name': 'SK하이닉스',
                'current_price': 145000,
                'confidence': 82,
                'expected_return': 20,
                'target_price': 174000,
                'investment_period': '6-12개월',
                'reason': 'HBM3 등 고부가 메모리 제품 수요 급증과 데이터센터향 제품 판매 확대가 예상됩니다. AI 붐으로 인한 수혜가 지속될 전망입니다.',
                'pros': [
                    'HBM 시장 선도 기업',
                    '엔비디아와의 협력 강화',
                    '메모리 업황 개선',
                    '높은 영업이익률'
                ],
                'risks': [
                    '경쟁 심화',
                    '설비투자 부담',
                    '재고 증가 우려'
                ]
            },
            {
                'stock_code': '035420',
                'stock_name': 'NAVER',
                'current_price': 220000,
                'confidence': 78,
                'expected_return': 12,
                'target_price': 246400,
                'investment_period': '3-6개월',
                'reason': 'AI 기반 검색 서비스 강화와 커머스 사업 성장이 지속되고 있습니다. 클라우드 및 핀테크 사업 확대로 수익 다각화가 진행 중입니다.',
                'pros': [
                    '국내 최대 포털 사이트',
                    'AI 기술력 확보',
                    '다양한 수익원 보유',
                    '해외 진출 확대'
                ],
                'risks': [
                    '규제 리스크',
                    '경쟁 심화',
                    '광고 시장 변동성'
                ]
            }
        ]

        return jsonify({
            'success': True,
            'recommendations': sample_recommendations,
            'updated_at': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"추천 종목 조회 오류: {e}")
        return jsonify({
            'success': False,
            'message': f'추천 종목 조회 중 오류 발생: {str(e)}'
        })


@app.route('/api/news/category/<category>', methods=['GET'])
@token_required
def get_news_by_category(current_user, category):
    """카테고리별 뉴스 조회"""
    category_mapping = {
        'popular': '인기',
        'economy': '경제',
        'stock': '증시',
        'tech': 'IT',
        'international': '국제',
        'industry': '산업'
    }

    # 실제로는 뉴스 API에서 카테고리별로 가져와야 하지만,
    # 현재는 모든 뉴스를 가져온 후 카테고리로 필터링
    news_list = news_summarizer.gather_all_news()

    # 카테고리별로 뉴스를 필터링하거나 분류
    # 여기서는 간단히 일부 뉴스를 반환하도록 구현
    filtered_news = []

    if news_list:
        # 실제로는 뉴스 제목이나 내용을 기반으로 필터링해야 함
        # 데모용으로 간단히 일부만 반환
        category_keyword = category_mapping.get(category, '')

        for news in news_list[:20]:  # 최대 20개까지
            if category == 'popular':
                # 인기 뉴스는 모든 뉴스에서 선별
                filtered_news.append(news)
            elif category_keyword and (
                category_keyword in news.get('title', '') or
                category_keyword in news.get('description', '')
            ):
                filtered_news.append(news)

    # 카테고리에 해당하는 뉴스가 없으면 일부 뉴스라도 반환
    if not filtered_news and news_list:
        filtered_news = news_list[:10]

    return jsonify({
        'success': True,
        'category': category,
        'news': filtered_news
    })


# ==================== 설정 저장 API ====================

@app.route('/api/settings/strategy', methods=['POST'])
@token_required
def save_strategy_settings():
    """기본 전략 설정 저장"""
    try:
        data = request.get_json()
        # 설정을 파일이나 데이터베이스에 저장
        # 현재는 간단히 메모리에만 저장하거나 로그만 출력
        print(f"전략 설정 저장: {data}")

        return jsonify({
            'success': True,
            'message': '전략 설정이 저장되었습니다.',
            'settings': data
        })
    except Exception as e:
        print(f"전략 설정 저장 오류: {e}")
        return jsonify({
            'success': False,
            'message': f'설정 저장 중 오류 발생: {str(e)}'
        })


@app.route('/api/settings/all-strategies', methods=['POST'])
@token_required
def save_all_strategies():
    """모든 전략 설정 저장 (단기/중기/장기)"""
    try:
        data = request.get_json()
        # 모든 전략 설정을 파일이나 데이터베이스에 저장
        print(f"모든 전략 설정 저장: {data}")

        return jsonify({
            'success': True,
            'message': '모든 전략 설정이 저장되었습니다.',
            'settings': data
        })
    except Exception as e:
        print(f"전략 설정 저장 오류: {e}")
        return jsonify({
            'success': False,
            'message': f'설정 저장 중 오류 발생: {str(e)}'
        })


# ==================== 전략 관리 API ====================

@app.route('/api/strategy/list', methods=['GET'])
@token_required
def get_strategy_list():
    """사용 가능한 모든 전략 목록 조회"""
    strategies = strategy_manager.get_all_available_strategies()
    return jsonify({
        'success': True,
        'strategies': strategies
    })


@app.route('/api/strategy/current', methods=['GET'])
@token_required
def get_current_strategy():
    """현재 설정된 전략 조회"""
    config = strategy_manager.get_current_config()
    return jsonify({
        'success': True,
        'config': config
    })


@app.route('/api/strategy/buy/set', methods=['POST'])
@token_required
def set_buy_strategy():
    """매수 전략 설정"""
    data = request.get_json()
    strategy_name = data.get('strategy_name')
    params = data.get('params', {})
    allocation_basis = data.get('allocation_basis')
    allocation_ratio = data.get('allocation_ratio')

    if not strategy_name:
        return jsonify({'success': False, 'message': '전략 이름을 입력해주세요.'})

    success = strategy_manager.set_buy_strategy(
        strategy_name,
        params,
        allocation_basis,
        allocation_ratio
    )

    if success:
        return jsonify({
            'success': True,
            'message': f'매수 전략이 {strategy_name}으로 변경되었습니다.',
            'config': strategy_manager.get_current_config()
        })
    else:
        return jsonify({
            'success': False,
            'message': '유효하지 않은 전략입니다.'
        })


@app.route('/api/strategy/sell/set', methods=['POST'])
@token_required
def set_sell_strategy():
    """매도 전략 설정"""
    data = request.get_json()
    strategy_name = data.get('strategy_name')
    params = data.get('params', {})

    if not strategy_name:
        return jsonify({'success': False, 'message': '전략 이름을 입력해주세요.'})

    success = strategy_manager.set_sell_strategy(strategy_name, params)

    if success:
        return jsonify({
            'success': True,
            'message': f'매도 전략이 {strategy_name}으로 변경되었습니다.',
            'config': strategy_manager.get_current_config()
        })
    else:
        return jsonify({
            'success': False,
            'message': '유효하지 않은 전략입니다.'
        })


@app.route('/api/strategy/buy/params', methods=['PUT'])
@token_required
def update_buy_params():
    """매수 전략 파라미터 업데이트"""
    data = request.get_json()
    params = data.get('params', {})

    success = strategy_manager.update_buy_params(params)

    if success:
        return jsonify({
            'success': True,
            'message': '매수 전략 파라미터가 업데이트되었습니다.',
            'config': strategy_manager.get_current_config()
        })
    else:
        return jsonify({
            'success': False,
            'message': '파라미터 업데이트 실패'
        })


@app.route('/api/strategy/sell/params', methods=['PUT'])
@token_required
def update_sell_params():
    """매도 전략 파라미터 업데이트"""
    data = request.get_json()
    params = data.get('params', {})

    success = strategy_manager.update_sell_params(params)

    if success:
        return jsonify({
            'success': True,
            'message': '매도 전략 파라미터가 업데이트되었습니다.',
            'config': strategy_manager.get_current_config()
        })
    else:
        return jsonify({
            'success': False,
            'message': '파라미터 업데이트 실패'
        })


@app.route('/api/strategy/auto-trading/toggle', methods=['POST'])
@token_required
def toggle_auto_trading():
    """자동 매매 활성화/비활성화"""
    data = request.get_json()
    enabled = data.get('enabled', False)

    strategy_manager.enable_auto_trading(enabled)

    return jsonify({
        'success': True,
        'message': f'자동 매매가 {"활성화" if enabled else "비활성화"}되었습니다.',
        'auto_trading_enabled': enabled
    })


@app.route('/api/strategy/analyze-buy', methods=['POST'])
@token_required
def strategy_analyze_buy():
    """현재 전략으로 매수 분석"""
    data = request.get_json()
    stock_code = data.get('stock_code')

    if not stock_code:
        return jsonify({'success': False, 'message': '종목 코드를 입력해주세요.'})

    # 주식 정보 조회
    stock_info = kis_api.get_current_price(stock_code)
    if not stock_info:
        return jsonify({'success': False, 'message': '주식 정보를 가져올 수 없습니다.'})

    # 계좌 정보 조회
    balance_info = kis_api.get_balance()

    # 전략 분석 실행
    analysis = strategy_manager.analyze_buy(stock_info, balance_info)

    return jsonify({
        'success': True,
        'analysis': analysis,
        'stock_info': stock_info,
        'current_strategy': strategy_manager.config.get('buy_strategy', {})
    })


@app.route('/api/strategy/analyze-sell', methods=['POST'])
@token_required
def strategy_analyze_sell():
    """현재 전략으로 매도 분석"""
    data = request.get_json()
    position = data.get('position')

    if not position:
        return jsonify({'success': False, 'message': '포지션 정보를 입력해주세요.'})

    # 현재 주식 정보 조회
    stock_info = kis_api.get_current_price(position['stock_code'])
    if not stock_info:
        return jsonify({'success': False, 'message': '주식 정보를 가져올 수 없습니다.'})

    # 전략 분석 실행
    analysis = strategy_manager.analyze_sell(position, stock_info)

    return jsonify({
        'success': True,
        'analysis': analysis,
        'stock_info': stock_info,
        'current_strategy': strategy_manager.config.get('sell_strategy', {})
    })


# ==================== 자동 매매 API ====================

@app.route('/api/auto-trading/run', methods=['POST'])
@token_required
def run_auto_trading():
    """자동 매매 실행 (현재 전략 사용)"""
    data = request.get_json()
    stock_code = data.get('stock_code')
    stock_name = data.get('stock_name')

    if not stock_code or not stock_name:
        return jsonify({'success': False, 'message': '종목 정보를 입력해주세요.'})

    # 자동 매매 활성화 확인
    if not strategy_manager.is_auto_trading_enabled():
        return jsonify({
            'success': False,
            'message': '자동 매매가 비활성화되어 있습니다.'
        })

    # 주식 정보 조회
    stock_info = kis_api.get_current_price(stock_code)
    if not stock_info:
        return jsonify({'success': False, 'message': '주식 정보를 가져올 수 없습니다.'})

    # 계좌 정보 조회
    balance_info = kis_api.get_balance()

    # 매수 분석 (현재 전략 사용)
    buy_analysis = strategy_manager.analyze_buy(stock_info, balance_info)

    if buy_analysis['should_buy'] and buy_analysis['confidence'] > 0.6:
        # 매수 실행
        result = kis_api.buy_stock(stock_code, buy_analysis['recommended_quantity'], price=0)

        if result.get('success'):
            telegram_notifier.send_trade_notification(
                'BUY', stock_code, stock_name,
                buy_analysis['recommended_quantity'],
                buy_analysis.get('target_price', 0),
                reason=buy_analysis['reason']
            )

        return jsonify({
            'success': True,
            'action': 'BUY',
            'analysis': buy_analysis,
            'execution': result
        })
    else:
        return jsonify({
            'success': True,
            'action': 'HOLD',
            'analysis': buy_analysis,
            'message': '매수 조건 미충족'
        })


# ==================== 정적 파일 제공 ====================

@app.route('/')
def index():
    """메인 페이지"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def static_files(path):
    """정적 파일 제공"""
    return send_from_directory(app.static_folder, path)


# ==================== 백그라운드 작업 ====================

def send_news_summary_job():
    """뉴스 요약 정기 전송"""
    print(f"[{datetime.now()}] 뉴스 요약 작업 시작")
    news_list = news_summarizer.gather_all_news()
    summary = news_summarizer.summarize_news_with_ai(news_list)
    telegram_notifier.send_news_summary(summary)
    print(f"[{datetime.now()}] 뉴스 요약 전송 완료")


def check_positions_job():
    """보유 종목 체크 (손절/익절) - 전략 관리자 사용"""
    print(f"[{datetime.now()}] 포지션 체크 작업 시작")

    # 자동 매매 비활성화 시 체크만 수행
    auto_trading_enabled = strategy_manager.is_auto_trading_enabled()

    balance = kis_api.get_balance()

    if balance.get('success'):
        positions = balance.get('positions', [])

        for position in positions:
            try:
                # 현재 주식 정보 조회
                stock_info = kis_api.get_current_price(position['stock_code'])
                if not stock_info:
                    continue

                # 전략 관리자로 매도 분석
                sell_analysis = strategy_manager.analyze_sell(position, stock_info)

                # 매도 신호 발생
                if sell_analysis['should_sell']:
                    print(f"매도 신호: {position['stock_name']} - {sell_analysis['reason'][:50]}...")

                    # 자동 매매가 활성화된 경우에만 실제 매도
                    if auto_trading_enabled and sell_analysis['urgency'] in ['high', 'medium']:
                        result = kis_api.sell_stock(
                            position['stock_code'],
                            sell_analysis['recommended_quantity'],
                            price=0
                        )

                        if result.get('success'):
                            telegram_notifier.send_trade_notification(
                                'SELL',
                                position['stock_code'],
                                position['stock_name'],
                                sell_analysis['recommended_quantity'],
                                stock_info.get('current_price', 0),
                                reason=sell_analysis['reason']
                            )
                            print(f"자동 매도 실행 완료: {position['stock_name']}")
                        else:
                            print(f"자동 매도 실패: {position['stock_name']}")
                    else:
                        print(f"매도 신호 감지됨 (자동 매매 {'비활성' if not auto_trading_enabled else '대기중'})")

            except Exception as e:
                print(f"포지션 체크 오류 ({position.get('stock_name', 'Unknown')}): {e}")


def run_scheduler():
    """스케줄러 실행"""
    # 뉴스 요약 전송 (매일 오전 9시, 오후 3시)
    schedule.every().day.at("09:00").do(send_news_summary_job)
    schedule.every().day.at("15:00").do(send_news_summary_job)

    # 포지션 체크 (매 30분마다)
    schedule.every(30).minutes.do(check_positions_job)

    while True:
        schedule.run_pending()
        time.sleep(60)


def start_background_jobs():
    """백그라운드 작업 시작"""
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("백그라운드 작업 시작됨")


# ==================== 스크래퍼 API ====================

@app.route('/api/scraper/capitol-trades', methods=['GET'])
@token_required
def get_capitol_trades():
    """Capitol Trades 정치인 주식 거래 데이터"""
    try:
        scraper = CapitolTradesScraper()
        politician = request.args.get('politician', None)
        limit = int(request.args.get('limit', 50))

        trades = scraper.get_recent_trades(politician=politician, limit=limit)
        scraper.close()

        return jsonify({
            'success': True,
            'trades': trades,
            'count': len(trades)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'크롤링 오류: {str(e)}',
            'trades': []
        })


@app.route('/api/scraper/capitol-trades/<politician_slug>', methods=['GET'])
@token_required
def get_politician_trades(politician_slug):
    """특정 정치인의 거래 데이터"""
    try:
        scraper = CapitolTradesScraper()
        limit = int(request.args.get('limit', 50))

        trades = scraper.get_politician_trades(politician_slug, limit=limit)
        scraper.close()

        return jsonify({
            'success': True,
            'politician': politician_slug,
            'trades': trades,
            'count': len(trades)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'크롤링 오류: {str(e)}',
            'trades': []
        })


@app.route('/api/scraper/stocknear', methods=['GET'])
@token_required
def get_stocknear_data():
    """StockNear 데이터 (봇 감지 우회)"""
    try:
        # 비동기 스크래핑 실행
        data = scrape_stocknear_sync()

        return jsonify({
            'success': True,
            'trending': data.get('trending', []),
            'volume': data.get('volume', []),
            'insider': data.get('insider', []),
            'detail': data.get('detail', {})
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'크롤링 오류: {str(e)}',
            'trending': [],
            'volume': [],
            'insider': [],
            'detail': {}
        })


@app.route('/api/scraper/stock-analysis', methods=['GET'])
@token_required
def get_stock_analysis_data():
    """StockAnalysis 시장 개요"""
    try:
        scraper = StockAnalysisScraper()
        overview = scraper.get_market_overview()
        scraper.close()

        return jsonify({
            'success': True,
            'metrics': overview.get('indices', {}),
            'financials': {},
            'valuation': {},
            'trending': overview.get('trending', [])
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'크롤링 오류: {str(e)}',
            'metrics': {},
            'financials': {},
            'valuation': {}
        })


@app.route('/api/scraper/stock-analysis/<symbol>', methods=['GET'])
@token_required
def get_stock_analysis_symbol(symbol):
    """특정 종목의 StockAnalysis 데이터"""
    try:
        scraper = StockAnalysisScraper()
        data = scraper.get_stock_overview(symbol.upper())
        scraper.close()

        return jsonify({
            'success': True,
            'data': data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'크롤링 오류: {str(e)}',
            'data': {}
        })


@app.route('/api/scraper/chart-exchange', methods=['GET'])
@token_required
def get_chart_exchange_data():
    """ChartExchange 시장 개요"""
    try:
        scraper = ChartExchangeScraper()
        overview = scraper.get_market_overview()
        scraper.close()

        return jsonify({
            'success': True,
            'technicals': {},
            'patterns': [],
            'trading': {},
            'trending': overview.get('trending', []),
            'active': overview.get('active', [])
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'크롤링 오류: {str(e)}',
            'technicals': {},
            'patterns': [],
            'trading': {}
        })


@app.route('/api/scraper/chart-exchange/<path:symbol>', methods=['GET'])
@token_required
def get_chart_exchange_symbol(symbol):
    """특정 종목의 ChartExchange 데이터"""
    try:
        scraper = ChartExchangeScraper()
        data = scraper.get_symbol_data(symbol)
        scraper.close()

        return jsonify({
            'success': True,
            'data': data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'크롤링 오류: {str(e)}',
            'data': {}
        })


# ==================== 앱 시작 ====================

if __name__ == '__main__':
    # 백그라운드 작업 시작
    start_background_jobs()

    # Flask 앱 실행
    print("=" * 50)
    print("주식 자동매매 시스템 시작")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=False)

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """애플리케이션 설정"""

    # Flask 설정
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-this')

    # 키움증권 OpenAPI 설정 (메인)
    KIWOOM_ACCOUNT_NO = os.getenv('KIWOOM_ACCOUNT_NO')  # 계좌번호
    KIWOOM_USER_ID = os.getenv('KIWOOM_USER_ID')  # 사용자 ID (로그인용 - 옵션)
    KIWOOM_USER_PW = os.getenv('KIWOOM_USER_PW')  # 사용자 비밀번호 (로그인용 - 옵션)

    # 한국투자증권 API 설정 (백업용)
    KIS_APP_KEY = os.getenv('KIS_APP_KEY')
    KIS_APP_SECRET = os.getenv('KIS_APP_SECRET')
    KIS_ACCOUNT_NO = os.getenv('KIS_ACCOUNT_NO')
    KIS_CANO = os.getenv('KIS_CANO')  # 계좌번호 앞 8자리
    KIS_ACNT_PRDT_CD = os.getenv('KIS_ACNT_PRDT_CD')  # 계좌번호 뒤 2자리
    KIS_BASE_URL = os.getenv('KIS_BASE_URL', 'https://openapi.koreainvestment.com:9443')

    # Telegram 설정
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

    # Claude AI 설정
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

    # 사용자 인증 설정
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'changeme123')

    # 매매 설정
    MAX_POSITION_SIZE = int(os.getenv('MAX_POSITION_SIZE', '1000000'))  # 최대 포지션 크기 (원)
    MAX_POSITIONS = int(os.getenv('MAX_POSITIONS', '5'))  # 최대 보유 종목 수

    # 뉴스 크롤링 설정
    NEWS_CHECK_INTERVAL = int(os.getenv('NEWS_CHECK_INTERVAL', '3600'))  # 뉴스 확인 간격 (초)
    NEWS_SOURCES = [
        'https://finance.naver.com/news/',
        'https://www.mk.co.kr/news/economy/',
        'https://www.hankyung.com/economy'
    ]

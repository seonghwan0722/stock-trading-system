#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
키움 증권 API 클라이언트 (시뮬레이션 모드)

참고:
- 키움 증권 OpenAPI는 Windows 전용 ActiveX 기반입니다.
- 실제 거래를 위해서는 pykiwoom 라이브러리와 키움 계좌가 필요합니다.
- 이 구현은 시뮬레이션 모드로 작동합니다.

실제 구현을 위해서는:
1. pip install pykiwoom
2. 키움증권 OpenAPI 설치 (https://www.kiwoom.com)
3. 모의투자 또는 실제 계좌 로그인
"""

import sys
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KiwoomClient:
    """키움 증권 API 클라이언트 (시뮬레이션)"""

    def __init__(self, account_no: Optional[str] = None, simulation_mode: bool = True):
        """
        키움 증권 클라이언트 초기화

        Args:
            account_no: 계좌번호 (시뮬레이션 모드에서는 무시됨)
            simulation_mode: 시뮬레이션 모드 활성화 (기본값: True)
        """
        self.account_no = account_no or "0000000000"
        self.simulation_mode = simulation_mode
        self.connected = False

        if not simulation_mode:
            logger.warning("⚠️  키움 증권 실제 API는 Windows 환경에서만 작동합니다.")
            logger.warning("⚠️  pykiwoom 라이브러리가 필요합니다: pip install pykiwoom")
            logger.warning("⚠️  현재는 시뮬레이션 모드로 전환합니다.")
            self.simulation_mode = True

        logger.info(f"✅ 키움 증권 클라이언트 초기화 (시뮬레이션 모드: {self.simulation_mode})")

    def connect(self) -> Dict[str, Any]:
        """
        키움 API 연결

        Returns:
            연결 결과
        """
        if self.simulation_mode:
            self.connected = True
            return {
                'success': True,
                'message': '시뮬레이션 모드로 연결되었습니다.',
                'account_no': self.account_no
            }

        # 실제 구현 (Windows + pykiwoom 필요)
        try:
            # from pykiwoom.kiwoom import Kiwoom
            # self.kiwoom = Kiwoom()
            # self.kiwoom.CommConnect()
            # self.connected = True
            pass
        except Exception as e:
            logger.error(f"키움 API 연결 실패: {e}")
            return {'success': False, 'message': str(e)}

    def get_stock_price(self, stock_code: str) -> Dict[str, Any]:
        """
        주식 현재가 조회

        Args:
            stock_code: 종목 코드 (6자리, 예: "005930" for 삼성전자)

        Returns:
            주식 시세 정보
        """
        if not self.connected:
            return {'success': False, 'message': 'Not connected'}

        if self.simulation_mode:
            # 시뮬레이션 데이터 반환
            import random
            base_price = random.randint(50000, 100000)
            change = random.randint(-1000, 1000)

            return {
                'success': True,
                'stock_code': stock_code,
                'current_price': base_price + change,
                'open_price': base_price,
                'high_price': base_price + abs(change),
                'low_price': base_price - abs(change),
                'volume': random.randint(1000000, 10000000),
                'change_rate': round((change / base_price) * 100, 2),
                'timestamp': datetime.now().isoformat()
            }

        # 실제 구현 (pykiwoom 사용)
        # return self.kiwoom.GetCodeCurrentPrice(stock_code)

    def buy_stock(self, stock_code: str, quantity: int, price: Optional[int] = None) -> Dict[str, Any]:
        """
        주식 매수

        Args:
            stock_code: 종목 코드
            quantity: 수량
            price: 가격 (None이면 시장가)

        Returns:
            주문 결과
        """
        if not self.connected:
            return {'success': False, 'message': 'Not connected'}

        if self.simulation_mode:
            order_type = "시장가" if price is None else "지정가"
            return {
                'success': True,
                'message': f'매수 주문이 시뮬레이션되었습니다 (실제 거래 아님)',
                'stock_code': stock_code,
                'quantity': quantity,
                'price': price or 0,
                'order_type': order_type,
                'timestamp': datetime.now().isoformat()
            }

        # 실제 구현
        # order_type = "00" if price is None else "03"  # 00: 지정가, 03: 시장가
        # return self.kiwoom.SendOrder(
        #     "매수", "0101", self.account_no, 1,
        #     stock_code, quantity, price or 0, order_type, ""
        # )

    def sell_stock(self, stock_code: str, quantity: int, price: Optional[int] = None) -> Dict[str, Any]:
        """
        주식 매도

        Args:
            stock_code: 종목 코드
            quantity: 수량
            price: 가격 (None이면 시장가)

        Returns:
            주문 결과
        """
        if not self.connected:
            return {'success': False, 'message': 'Not connected'}

        if self.simulation_mode:
            order_type = "시장가" if price is None else "지정가"
            return {
                'success': True,
                'message': f'매도 주문이 시뮬레이션되었습니다 (실제 거래 아님)',
                'stock_code': stock_code,
                'quantity': quantity,
                'price': price or 0,
                'order_type': order_type,
                'timestamp': datetime.now().isoformat()
            }

        # 실제 구현
        # order_type = "00" if price is None else "03"
        # return self.kiwoom.SendOrder(
        #     "매도", "0101", self.account_no, 2,
        #     stock_code, quantity, price or 0, order_type, ""
        # )

    def get_account_info(self) -> Dict[str, Any]:
        """
        계좌 정보 조회

        Returns:
            계좌 잔고 및 보유 종목
        """
        if not self.connected:
            return {'success': False, 'message': 'Not connected'}

        if self.simulation_mode:
            return {
                'success': True,
                'account_no': self.account_no,
                'total_balance': 10000000,  # 1천만원
                'available_cash': 8000000,  # 800만원
                'total_profit_loss': 200000,  # 20만원 수익
                'positions': [
                    {
                        'stock_code': '005930',
                        'stock_name': '삼성전자',
                        'quantity': 10,
                        'average_price': 70000,
                        'current_price': 72000,
                        'profit_loss': 20000
                    },
                    {
                        'stock_code': '000660',
                        'stock_name': 'SK하이닉스',
                        'quantity': 5,
                        'average_price': 120000,
                        'current_price': 125000,
                        'profit_loss': 25000
                    }
                ]
            }

        # 실제 구현
        # return self.kiwoom.GetAccountInfo(self.account_no)

    def get_stock_list(self, market: str = "0") -> List[Dict[str, str]]:
        """
        종목 리스트 조회

        Args:
            market: 시장 구분 (0: 코스피, 10: 코스닥)

        Returns:
            종목 코드 및 이름 리스트
        """
        if self.simulation_mode:
            # 샘플 종목 리스트
            if market == "0":  # 코스피
                return [
                    {'code': '005930', 'name': '삼성전자'},
                    {'code': '000660', 'name': 'SK하이닉스'},
                    {'code': '035420', 'name': 'NAVER'},
                    {'code': '051910', 'name': 'LG화학'},
                    {'code': '006400', 'name': '삼성SDI'}
                ]
            else:  # 코스닥
                return [
                    {'code': '035720', 'name': '카카오'},
                    {'code': '293490', 'name': '카카오게임즈'},
                    {'code': '068270', 'name': '셀트리온'},
                    {'code': '247540', 'name': '에코프로비엠'},
                    {'code': '357780', 'name': '솔브레인'}
                ]

        # 실제 구현
        # return self.kiwoom.GetCodeListByMarket(market)

    def disconnect(self):
        """API 연결 해제"""
        if self.connected:
            self.connected = False
            logger.info("✅ 키움 API 연결이 해제되었습니다.")


# 싱글톤 인스턴스
_kiwoom_client = None


def get_kiwoom_client(account_no: Optional[str] = None) -> KiwoomClient:
    """키움 클라이언트 싱글톤 인스턴스 반환"""
    global _kiwoom_client
    if _kiwoom_client is None:
        _kiwoom_client = KiwoomClient(account_no=account_no)
        _kiwoom_client.connect()
    return _kiwoom_client


if __name__ == "__main__":
    # 테스트
    client = get_kiwoom_client()

    print("\n=== 계좌 정보 ===")
    account_info = client.get_account_info()
    print(account_info)

    print("\n=== 삼성전자 시세 ===")
    price = client.get_stock_price("005930")
    print(price)

    print("\n=== 코스피 종목 리스트 ===")
    stocks = client.get_stock_list("0")
    for stock in stocks[:5]:
        print(f"{stock['code']}: {stock['name']}")

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
키움증권 REST API 클라이언트
OpenAPI+와 달리 OS에 구애받지 않는 REST API 방식

API 문서: https://openapi.kiwoom.com/guide/apiguide
계정 신청: https://www.kiwoom.com (OpenAPI 신청)
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from backend.config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Config = get_config()


class KiwoomRestAPI:
    """키움증권 REST API 클라이언트"""

    # API 엔드포인트
    BASE_URL_PROD = "https://api.kiwoom.com"  # 실전
    BASE_URL_MOCK = "https://mockapi.kiwoom.com"  # 모의투자

    def __init__(self, app_key: str = None, secret_key: str = None, account_no: str = None, is_mock: bool = True):
        """
        키움증권 REST API 클라이언트 초기화

        Args:
            app_key: 앱 키
            secret_key: 시크릿 키
            account_no: 계좌번호
            is_mock: 모의투자 여부 (기본값: True)
        """
        self.app_key = app_key or getattr(Config, 'KIWOOM_APP_KEY', '')
        self.secret_key = secret_key or getattr(Config, 'KIWOOM_SECRET_KEY', '')
        self.account_no = account_no or getattr(Config, 'KIWOOM_ACCOUNT_NO', '')
        self.is_mock = is_mock

        self.base_url = self.BASE_URL_MOCK if is_mock else self.BASE_URL_PROD
        self.access_token = None
        self.token_expires_at = None

        if not self.app_key or not self.secret_key:
            logger.warning("⚠️  키움 REST API 키가 설정되지 않았습니다.")
            logger.warning("    .env 파일에 KIWOOM_APP_KEY, KIWOOM_SECRET_KEY를 추가하세요.")

    def _get_headers(self, require_token: bool = True) -> Dict[str, str]:
        """
        요청 헤더 생성

        Args:
            require_token: 토큰 필요 여부

        Returns:
            헤더 딕셔너리
        """
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
        }

        if require_token:
            if not self.access_token or self._is_token_expired():
                self.get_access_token()

            headers["Authorization"] = f"Bearer {self.access_token}"

        return headers

    def _is_token_expired(self) -> bool:
        """토큰 만료 여부 확인"""
        if not self.token_expires_at:
            return True
        return datetime.now() >= self.token_expires_at

    def _make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None, require_token: bool = True) -> Dict[str, Any]:
        """
        API 요청 실행

        Args:
            method: HTTP 메서드 (GET, POST, etc.)
            endpoint: API 엔드포인트
            data: 요청 바디
            params: 쿼리 파라미터
            require_token: 토큰 필요 여부

        Returns:
            API 응답
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(require_token)

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"키움 REST API 요청 실패: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def get_access_token(self) -> Dict[str, Any]:
        """
        OAuth 토큰 발급

        Returns:
            토큰 정보
        """
        endpoint = "/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "secretkey": self.secret_key
        }

        headers = {
            "Content-Type": "application/json;charset=UTF-8"
        }

        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()

            result = response.json()

            if 'access_token' in result:
                self.access_token = result['access_token']
                expires_in = result.get('expires_in', 86400)  # 기본 24시간
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)

                logger.info("✅ 키움 REST API 토큰 발급 성공")
                return {
                    'success': True,
                    'access_token': self.access_token,
                    'expires_in': expires_in,
                    'token_type': result.get('token_type', 'Bearer')
                }
            else:
                logger.error("❌ 토큰 발급 실패")
                return {
                    'success': False,
                    'message': '토큰 발급 실패'
                }

        except Exception as e:
            logger.error(f"토큰 발급 오류: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    # ==================== 주문 API ====================

    def buy_stock(self, stock_code: str, quantity: int, price: int = 0, order_type: str = "00") -> Dict[str, Any]:
        """
        주식 매수

        Args:
            stock_code: 종목코드 (6자리)
            quantity: 수량
            price: 가격 (0이면 시장가)
            order_type: 주문유형 ("00": 지정가, "01": 시장가)

        Returns:
            주문 결과
        """
        endpoint = "/uapi/domestic-stock/v1/trading/order-cash"

        data = {
            "CANO": self.account_no,  # 계좌번호
            "ACNT_PRDT_CD": "01",  # 계좌상품코드
            "PDNO": stock_code,  # 종목코드
            "ORD_DVSN": order_type,  # 주문구분
            "ORD_QTY": str(quantity),  # 주문수량
            "ORD_UNPR": str(price) if price > 0 else "0",  # 주문단가
            "CTAC_TLNO": "",  # 연락전화번호
            "SLL_TYPE": "01",  # 매도유형 (01: 보통)
        }

        result = self._make_request("POST", endpoint, data=data)

        if result.get('rt_cd') == '0':
            return {
                'success': True,
                'message': '매수 주문 성공',
                'order_no': result.get('output', {}).get('ODNO'),
                'stock_code': stock_code,
                'quantity': quantity,
                'price': price
            }
        else:
            return {
                'success': False,
                'message': result.get('msg1', '매수 주문 실패')
            }

    def sell_stock(self, stock_code: str, quantity: int, price: int = 0, order_type: str = "00") -> Dict[str, Any]:
        """
        주식 매도

        Args:
            stock_code: 종목코드 (6자리)
            quantity: 수량
            price: 가격 (0이면 시장가)
            order_type: 주문유형 ("00": 지정가, "01": 시장가)

        Returns:
            주문 결과
        """
        endpoint = "/uapi/domestic-stock/v1/trading/order-cash"

        data = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": "01",
            "PDNO": stock_code,
            "ORD_DVSN": order_type,
            "ORD_QTY": str(quantity),
            "ORD_UNPR": str(price) if price > 0 else "0",
            "CTAC_TLNO": "",
            "SLL_TYPE": "01",
        }

        result = self._make_request("POST", endpoint, data=data)

        if result.get('rt_cd') == '0':
            return {
                'success': True,
                'message': '매도 주문 성공',
                'order_no': result.get('output', {}).get('ODNO'),
                'stock_code': stock_code,
                'quantity': quantity,
                'price': price
            }
        else:
            return {
                'success': False,
                'message': result.get('msg1', '매도 주문 실패')
            }

    def cancel_order(self, order_no: str, stock_code: str, quantity: int, order_type: str = "00") -> Dict[str, Any]:
        """
        주문 취소

        Args:
            order_no: 주문번호
            stock_code: 종목코드
            quantity: 수량
            order_type: 원주문 구분

        Returns:
            취소 결과
        """
        endpoint = "/uapi/domestic-stock/v1/trading/order-rvsecncl"

        data = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": "01",
            "KRX_FWDG_ORD_ORGNO": "",  # 거래소 원주문조직번호
            "ORGN_ODNO": order_no,  # 원주문번호
            "ORD_DVSN": order_type,
            "RVSE_CNCL_DVSN_CD": "02",  # 정정취소구분 (02: 취소)
            "ORD_QTY": "0",  # 주문수량 (취소 시 0)
            "ORD_UNPR": "0",  # 주문단가 (취소 시 0)
            "QTY_ALL_ORD_YN": "Y",  # 잔량전부주문여부
        }

        result = self._make_request("POST", endpoint, data=data)

        if result.get('rt_cd') == '0':
            return {
                'success': True,
                'message': '주문 취소 성공',
                'order_no': order_no
            }
        else:
            return {
                'success': False,
                'message': result.get('msg1', '주문 취소 실패')
            }

    # ==================== 계좌 API ====================

    def get_account_balance(self) -> Dict[str, Any]:
        """
        계좌 잔고 조회

        Returns:
            계좌 잔고 정보
        """
        endpoint = "/uapi/domestic-stock/v1/trading/inquire-balance"

        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": "01",
            "AFHR_FLPR_YN": "N",  # 시간외단일가여부
            "OFL_YN": "",  # 오프라인여부
            "INQR_DVSN": "01",  # 조회구분 (01: 대출일별, 02: 종목별)
            "UNPR_DVSN": "01",  # 단가구분
            "FUND_STTL_ICLD_YN": "N",  # 펀드결제분포함여부
            "FNCG_AMT_AUTO_RDPT_YN": "N",  # 융자금액자동상환여부
            "PRCS_DVSN": "00",  # 처리구분
            "CTX_AREA_FK100": "",  # 연속조회검색조건100
            "CTX_AREA_NK100": ""  # 연속조회키100
        }

        result = self._make_request("GET", endpoint, params=params)

        if result.get('rt_cd') == '0':
            output1 = result.get('output1', [])
            output2 = result.get('output2', [{}])[0]

            positions = []
            for item in output1:
                positions.append({
                    'stock_code': item.get('pdno', ''),
                    'stock_name': item.get('prdt_name', ''),
                    'quantity': int(item.get('hldg_qty', 0)),
                    'average_price': float(item.get('pchs_avg_pric', 0)),
                    'current_price': float(item.get('prpr', 0)),
                    'profit_loss': float(item.get('evlu_pfls_amt', 0)),
                    'profit_rate': float(item.get('evlu_pfls_rt', 0))
                })

            return {
                'success': True,
                'account_no': self.account_no,
                'total_balance': float(output2.get('tot_evlu_amt', 0)),
                'total_purchase': float(output2.get('pchs_amt_smtl_amt', 0)),
                'total_profit_loss': float(output2.get('evlu_pfls_smtl_amt', 0)),
                'positions': positions
            }
        else:
            return {
                'success': False,
                'message': result.get('msg1', '계좌 조회 실패')
            }

    def get_orders(self) -> Dict[str, Any]:
        """
        미체결 주문 조회

        Returns:
            미체결 주문 리스트
        """
        endpoint = "/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl"

        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
            "INQR_DVSN_1": "0",  # 조회구분1 (0: 전체)
            "INQR_DVSN_2": "0"  # 조회구분2
        }

        result = self._make_request("GET", endpoint, params=params)

        if result.get('rt_cd') == '0':
            output = result.get('output', [])
            orders = []

            for item in output:
                orders.append({
                    'order_no': item.get('odno', ''),
                    'stock_code': item.get('pdno', ''),
                    'stock_name': item.get('prdt_name', ''),
                    'order_type': item.get('sll_buy_dvsn_cd_name', ''),
                    'quantity': int(item.get('ord_qty', 0)),
                    'price': float(item.get('ord_unpr', 0)),
                    'executed_quantity': int(item.get('tot_ccld_qty', 0)),
                    'order_time': item.get('ord_tmd', '')
                })

            return {
                'success': True,
                'orders': orders
            }
        else:
            return {
                'success': False,
                'message': result.get('msg1', '주문 조회 실패')
            }

    # ==================== 시세 API ====================

    def get_stock_price(self, stock_code: str) -> Dict[str, Any]:
        """
        주식 현재가 조회

        Args:
            stock_code: 종목코드 (6자리)

        Returns:
            시세 정보
        """
        endpoint = "/uapi/domestic-stock/v1/quotations/inquire-price"

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # 시장구분코드
            "FID_INPUT_ISCD": stock_code  # 종목코드
        }

        result = self._make_request("GET", endpoint, params=params)

        if result.get('rt_cd') == '0':
            output = result.get('output', {})

            return {
                'success': True,
                'stock_code': stock_code,
                'current_price': int(output.get('stck_prpr', 0)),
                'open_price': int(output.get('stck_oprc', 0)),
                'high_price': int(output.get('stck_hgpr', 0)),
                'low_price': int(output.get('stck_lwpr', 0)),
                'prev_close': int(output.get('stck_sdpr', 0)),
                'volume': int(output.get('acml_vol', 0)),
                'change_rate': float(output.get('prdy_ctrt', 0)),
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'message': result.get('msg1', '시세 조회 실패')
            }

    def get_daily_chart(self, stock_code: str, days: int = 30) -> Dict[str, Any]:
        """
        일봉 차트 조회

        Args:
            stock_code: 종목코드
            days: 조회 일수

        Returns:
            일봉 데이터
        """
        endpoint = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stock_code,
            "FID_PERIOD_DIV_CODE": "D",  # 기간구분 (D: 일, W: 주, M: 월)
            "FID_ORG_ADJ_PRC": "0"  # 수정주가 (0: 수정주가반영안함)
        }

        result = self._make_request("GET", endpoint, params=params)

        if result.get('rt_cd') == '0':
            output = result.get('output', [])
            chart_data = []

            for item in output[:days]:
                chart_data.append({
                    'date': item.get('stck_bsop_date', ''),
                    'open': int(item.get('stck_oprc', 0)),
                    'high': int(item.get('stck_hgpr', 0)),
                    'low': int(item.get('stck_lwpr', 0)),
                    'close': int(item.get('stck_clpr', 0)),
                    'volume': int(item.get('acml_vol', 0))
                })

            return {
                'success': True,
                'stock_code': stock_code,
                'chart_data': chart_data
            }
        else:
            return {
                'success': False,
                'message': result.get('msg1', '차트 조회 실패')
            }


# 싱글톤 인스턴스
_kiwoom_rest_client = None


def get_kiwoom_rest_client(app_key: str = None, secret_key: str = None, account_no: str = None, is_mock: bool = True) -> KiwoomRestAPI:
    """
    키움 REST API 클라이언트 싱글톤 인스턴스 반환

    Args:
        app_key: 앱 키
        secret_key: 시크릿 키
        account_no: 계좌번호
        is_mock: 모의투자 여부
    """
    global _kiwoom_rest_client
    if _kiwoom_rest_client is None:
        _kiwoom_rest_client = KiwoomRestAPI(app_key, secret_key, account_no, is_mock)
    return _kiwoom_rest_client


if __name__ == "__main__":
    # 테스트
    print("키움증권 REST API 클라이언트")
    print("실제 사용을 위해서는 .env에 API 키를 설정하세요.")

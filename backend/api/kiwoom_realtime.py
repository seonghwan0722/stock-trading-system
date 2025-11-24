#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
키움 증권 실시간 데이터 및 주문 조회 기능
"""

import sys
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

# Windows 환경 체크
IS_WINDOWS = sys.platform == 'win32'

if IS_WINDOWS:
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QAxContainer import QAxWidget
        from PyQt5.QtCore import QEventLoop
        PYQT_AVAILABLE = True
    except ImportError:
        PYQT_AVAILABLE = False
else:
    PYQT_AVAILABLE = False


class KiwoomRealtimeAPI:
    """키움 증권 실시간 데이터 및 주문 조회 API"""

    def __init__(self, ocx: 'QAxWidget'):
        """
        Args:
            ocx: 키움 OpenAPI OCX 객체
        """
        self.ocx = ocx
        self.tr_event_loop = QEventLoop()

        # 실시간 데이터 콜백
        self.realtime_callbacks = defaultdict(list)

        # 체결 데이터 콜백
        self.chejan_callbacks = []

    def set_real_reg(self, screen_no: str, code_list: str, fid_list: str, real_type: str):
        """
        실시간 등록

        Args:
            screen_no: 화면번호
            code_list: 종목코드 리스트 (';'로 구분)
            fid_list: FID 리스트 (';'로 구분)
            real_type: "0": 추가등록, "1": 삭제등록
        """
        self.ocx.dynamicCall(
            "SetRealReg(QString, QString, QString, QString)",
            screen_no, code_list, fid_list, real_type
        )

    def set_real_remove(self, screen_no: str, del_code: str):
        """
        실시간 해제

        Args:
            screen_no: 화면번호
            del_code: 종목코드 (전체 해제는 "ALL")
        """
        self.ocx.dynamicCall("SetRealRemove(QString, QString)", screen_no, del_code)

    def get_comm_real_data(self, code: str, fid: int):
        """실시간 데이터 조회"""
        data = self.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid)
        return data.strip()

    def subscribe_realtime_price(self, stock_codes: List[str], callback: Callable):
        """
        실시간 시세 구독

        Args:
            stock_codes: 종목코드 리스트
            callback: 데이터 수신 시 호출할 콜백 함수
        """
        # FID 리스트 (현재가, 등락률, 거래량, 고가, 저가, 시가)
        fid_list = "10;11;12;13;27;28"

        code_list = ";".join(stock_codes)
        self.set_real_reg("1000", code_list, fid_list, "0")

        # 콜백 등록
        for code in stock_codes:
            self.realtime_callbacks[code].append(callback)

    def unsubscribe_realtime_price(self, stock_codes: List[str] = None):
        """
        실시간 시세 구독 해제

        Args:
            stock_codes: 종목코드 리스트 (None이면 전체 해제)
        """
        if stock_codes:
            for code in stock_codes:
                self.set_real_remove("1000", code)
                if code in self.realtime_callbacks:
                    del self.realtime_callbacks[code]
        else:
            self.set_real_remove("1000", "ALL")
            self.realtime_callbacks.clear()

    def subscribe_chejan(self, callback: Callable):
        """
        체결/잔고 데이터 구독

        Args:
            callback: 체결 데이터 수신 시 호출할 콜백 함수
        """
        self.chejan_callbacks.append(callback)

    def get_order_list(self) -> List[Dict[str, Any]]:
        """
        미체결 주문 조회

        Returns:
            미체결 주문 리스트
        """
        # opt10075: 미체결내역조회
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "계좌번호", "")
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "체결구분", "1")  # 1: 미체결
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")  # 0: 전체

        self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", "미체결조회", "opt10075", 0, "0102")
        self.tr_event_loop.exec_()

        # 결과 파싱 (실제 구현에서는 OnReceiveTrData에서 처리)
        return []

    def get_executed_orders(self, date: str = None) -> List[Dict[str, Any]]:
        """
        체결 내역 조회

        Args:
            date: 조회 날짜 (YYYYMMDD, None이면 당일)

        Returns:
            체결 내역 리스트
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")

        # opt10076: 체결내역조회
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "계좌번호", "")
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "시작일자", date)
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "종료일자", date)

        self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", "체결조회", "opt10076", 0, "0103")
        self.tr_event_loop.exec_()

        # 결과 파싱 (실제 구현에서는 OnReceiveTrData에서 처리)
        return []

    def cancel_order(self, org_order_no: str, stock_code: str, quantity: int, order_type: int):
        """
        주문 취소

        Args:
            org_order_no: 원주문번호
            stock_code: 종목코드
            quantity: 수량
            order_type: 1: 매수취소, 2: 매도취소
        """
        result = self.ocx.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            ["주문취소", "0104", "", order_type + 2, stock_code, quantity, 0, "00", org_order_no]
        )
        return result == 0

    def modify_order(self, org_order_no: str, stock_code: str, quantity: int, price: int, order_type: int):
        """
        주문 정정

        Args:
            org_order_no: 원주문번호
            stock_code: 종목코드
            quantity: 수량
            price: 가격
            order_type: 1: 매수정정, 2: 매도정정
        """
        result = self.ocx.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            ["주문정정", "0105", "", order_type + 4, stock_code, quantity, price, "00", org_order_no]
        )
        return result == 0


class KiwoomOrderManager:
    """키움 주문 관리자"""

    def __init__(self, kiwoom_client):
        """
        Args:
            kiwoom_client: KiwoomClient 인스턴스
        """
        self.client = kiwoom_client
        self.orders = {}  # 주문 내역 저장
        self.order_callbacks = []

    def place_market_buy(self, stock_code: str, quantity: int) -> Dict[str, Any]:
        """시장가 매수"""
        return self.client.buy_stock(stock_code, quantity, 0, "시장가")

    def place_limit_buy(self, stock_code: str, quantity: int, price: int) -> Dict[str, Any]:
        """지정가 매수"""
        return self.client.buy_stock(stock_code, quantity, price, "지정가")

    def place_market_sell(self, stock_code: str, quantity: int) -> Dict[str, Any]:
        """시장가 매도"""
        return self.client.sell_stock(stock_code, quantity, 0, "시장가")

    def place_limit_sell(self, stock_code: str, quantity: int, price: int) -> Dict[str, Any]:
        """지정가 매도"""
        return self.client.sell_stock(stock_code, quantity, price, "지정가")

    def get_pending_orders(self) -> List[Dict[str, Any]]:
        """미체결 주문 조회"""
        if self.client.simulation_mode:
            return []

        # 실제 API 호출
        return []

    def get_executed_orders(self, date: str = None) -> List[Dict[str, Any]]:
        """체결 내역 조회"""
        if self.client.simulation_mode:
            return []

        # 실제 API 호출
        return []

    def cancel_order(self, order_no: str) -> bool:
        """주문 취소"""
        if self.client.simulation_mode:
            logger.info(f"[시뮬레이션] 주문 취소: {order_no}")
            return True

        # 실제 API 호출
        return False

    def modify_order(self, order_no: str, new_price: int, new_quantity: int = None) -> bool:
        """주문 정정"""
        if self.client.simulation_mode:
            logger.info(f"[시뮬레이션] 주문 정정: {order_no}, 가격: {new_price}")
            return True

        # 실제 API 호출
        return False


# 실시간 데이터 처리 예제
def handle_realtime_price(code: str, data: Dict[str, Any]):
    """실시간 시세 처리 콜백"""
    logger.info(f"[실시간] {code}: {data['current_price']}원 ({data['change_rate']}%)")


def handle_chejan(gubun: str, data: Dict[str, Any]):
    """체결/잔고 처리 콜백"""
    if gubun == "0":  # 체결
        logger.info(f"[체결] {data['stock_code']}: {data['quantity']}주 @ {data['price']}원")
    elif gubun == "1":  # 잔고
        logger.info(f"[잔고] {data['stock_code']}: {data['quantity']}주")


if __name__ == "__main__":
    # 테스트 코드
    print("키움 실시간 API 모듈")
    print("실제 사용 시에는 KiwoomClient와 함께 사용하세요.")

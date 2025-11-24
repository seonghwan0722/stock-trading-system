#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
키움 증권 OpenAPI 클라이언트 (실제 매매 가능)

요구사항:
1. Windows OS
2. 키움증권 OpenAPI+ 설치 (https://www1.kiwoom.com/nkw.templateFrameSet.do?m=m1408000000)
3. pip install pyqt5
4. 키움증권 계좌 (모의투자 또는 실계좌)

설치 방법:
1. 키움증권 OpenAPI+ 다운로드 및 설치
2. pip install PyQt5
3. 모의투자 신청: https://www1.kiwoom.com/nkw.templateFrameSet.do?m=m1408030000
"""

import sys
import os
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import logging
from collections import defaultdict

# 로깅 설정
logging.basicConfig(level=logging.INFO)
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
        logger.warning("⚠️  PyQt5가 설치되어 있지 않습니다. pip install PyQt5")
        PYQT_AVAILABLE = False
else:
    logger.warning("⚠️  키움 OpenAPI는 Windows 전용입니다.")
    PYQT_AVAILABLE = False


class KiwoomAPI:
    """키움 증권 OpenAPI 래퍼"""

    def __init__(self):
        """키움 OpenAPI 초기화"""
        if not PYQT_AVAILABLE:
            raise RuntimeError("PyQt5가 필요합니다. pip install PyQt5")

        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)

        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.connected = False
        self.account_list = []

        # 이벤트 루프
        self.login_event_loop = QEventLoop()
        self.tr_event_loop = QEventLoop()

        # TR 데이터 저장
        self.tr_data = {}

        # 시그널 연결
        self._connect_signals()

    def _connect_signals(self):
        """이벤트 시그널 연결"""
        self.ocx.OnEventConnect.connect(self._on_event_connect)
        self.ocx.OnReceiveTrData.connect(self._on_receive_tr_data)
        self.ocx.OnReceiveMsg.connect(self._on_receive_msg)
        self.ocx.OnReceiveChejanData.connect(self._on_receive_chejan_data)
        self.ocx.OnReceiveRealData.connect(self._on_receive_real_data)

    def _on_event_connect(self, err_code):
        """로그인 이벤트"""
        if err_code == 0:
            logger.info("✅ 키움 OpenAPI 로그인 성공")
            self.connected = True
        else:
            logger.error(f"❌ 키움 OpenAPI 로그인 실패: {err_code}")
            self.connected = False

        self.login_event_loop.exit()

    def _on_receive_tr_data(self, screen_no, rqname, trcode, record_name, prev_next, data_len, err_code, msg, splm_msg):
        """TR 데이터 수신"""
        if err_code == 0:
            self.tr_data[rqname] = {
                'trcode': trcode,
                'prev_next': prev_next
            }
        else:
            logger.error(f"TR 데이터 수신 오류: {err_code} - {msg}")

        self.tr_event_loop.exit()

    def _on_receive_msg(self, screen_no, rqname, trcode, msg):
        """메시지 수신"""
        logger.info(f"[메시지] {msg}")

    def _on_receive_chejan_data(self, gubun, item_cnt, fid_list):
        """체결/잔고 데이터 수신"""
        logger.info(f"[체결/잔고] 구분: {gubun}")

    def _on_receive_real_data(self, code, real_type, real_data):
        """실시간 데이터 수신"""
        pass  # 실시간 데이터 처리 (필요 시 구현)

    def comm_connect(self):
        """로그인 요청"""
        self.ocx.dynamicCall("CommConnect()")
        self.login_event_loop.exec_()
        return self.connected

    def get_login_info(self, tag):
        """로그인 정보 조회"""
        return self.ocx.dynamicCall("GetLoginInfo(QString)", tag)

    def get_account_list(self):
        """계좌번호 리스트"""
        accounts = self.get_login_info("ACCNO")
        self.account_list = accounts.split(';')[:-1] if accounts else []
        return self.account_list

    def send_order(self, rqname, screen_no, acc_no, order_type, code, qty, price, hoga_gb, org_order_no=""):
        """
        주문 전송

        Args:
            rqname: 요청명
            screen_no: 화면번호
            acc_no: 계좌번호
            order_type: 주문유형 (1:신규매수, 2:신규매도, 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정)
            code: 종목코드
            qty: 수량
            price: 가격 (0이면 시장가)
            hoga_gb: 호가유형 (00:지정가, 03:시장가, 05:조건부지정가, 등)
            org_order_no: 원주문번호 (정정/취소 시)
        """
        result = self.ocx.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [rqname, screen_no, acc_no, order_type, code, qty, price, hoga_gb, org_order_no]
        )
        return result

    def set_input_value(self, key, value):
        """TR 입력값 설정"""
        self.ocx.dynamicCall("SetInputValue(QString, QString)", key, value)

    def comm_rq_data(self, rqname, trcode, prev_next, screen_no):
        """TR 요청"""
        self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, prev_next, screen_no)
        self.tr_event_loop.exec_()

    def get_comm_data(self, trcode, rqname, index, item_name):
        """TR 데이터 조회"""
        data = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, index, item_name)
        return data.strip()

    def get_repeat_cnt(self, trcode, rqname):
        """반복 데이터 개수"""
        return self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)

    def disconnect(self):
        """연결 종료"""
        if self.connected:
            self.ocx.dynamicCall("CommTerminate()")
            self.connected = False
            logger.info("✅ 키움 OpenAPI 연결 종료")


class KiwoomClient:
    """키움 증권 OpenAPI 클라이언트 (고수준 인터페이스)"""

    def __init__(self, account_no: Optional[str] = None, simulation_mode: bool = False):
        """
        키움 증권 클라이언트 초기화

        Args:
            account_no: 계좌번호 (None이면 첫 번째 계좌 사용)
            simulation_mode: 시뮬레이션 모드 (실제 API 미사용)
        """
        self.simulation_mode = simulation_mode
        self.account_no = account_no
        self.api = None
        self.connected = False

        if simulation_mode:
            logger.info("✅ 키움 클라이언트 - 시뮬레이션 모드")
            self.account_no = account_no or "8888888888"
            self.connected = True
        else:
            if not IS_WINDOWS:
                logger.error("❌ 키움 OpenAPI는 Windows 전용입니다.")
                raise RuntimeError("Windows OS가 필요합니다.")

            if not PYQT_AVAILABLE:
                logger.error("❌ PyQt5가 설치되어 있지 않습니다.")
                raise RuntimeError("pip install PyQt5")

    def connect(self) -> Dict[str, Any]:
        """키움 API 연결"""
        if self.simulation_mode:
            return {
                'success': True,
                'message': '시뮬레이션 모드로 연결되었습니다.',
                'account_no': self.account_no,
                'accounts': [self.account_no]
            }

        try:
            self.api = KiwoomAPI()
            self.connected = self.api.comm_connect()

            if self.connected:
                # 계좌 목록 조회
                accounts = self.api.get_account_list()

                # 계좌번호가 지정되지 않았으면 첫 번째 계좌 사용
                if not self.account_no and accounts:
                    self.account_no = accounts[0]

                user_name = self.api.get_login_info("USER_NAME")
                user_id = self.api.get_login_info("USER_ID")

                return {
                    'success': True,
                    'message': '키움 OpenAPI 연결 성공',
                    'user_name': user_name,
                    'user_id': user_id,
                    'account_no': self.account_no,
                    'accounts': accounts
                }
            else:
                return {
                    'success': False,
                    'message': '로그인 실패'
                }

        except Exception as e:
            logger.error(f"연결 오류: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def buy_stock(self, stock_code: str, quantity: int, price: int = 0, order_type: str = "지정가") -> Dict[str, Any]:
        """
        주식 매수

        Args:
            stock_code: 종목코드 (6자리)
            quantity: 수량
            price: 가격 (0이면 시장가)
            order_type: 주문유형 ("지정가" or "시장가")

        Returns:
            주문 결과
        """
        if not self.connected:
            return {'success': False, 'message': '연결되지 않음'}

        if self.simulation_mode:
            return {
                'success': True,
                'message': f'[시뮬레이션] 매수 주문: {stock_code} {quantity}주',
                'stock_code': stock_code,
                'quantity': quantity,
                'price': price,
                'order_type': order_type,
                'timestamp': datetime.now().isoformat()
            }

        try:
            # 호가 유형 결정
            hoga_gb = "00" if order_type == "지정가" else "03"

            # 주문 전송
            result = self.api.send_order(
                rqname="매수주문",
                screen_no="0101",
                acc_no=self.account_no,
                order_type=1,  # 1: 신규매수
                code=stock_code,
                qty=quantity,
                price=price,
                hoga_gb=hoga_gb,
                org_order_no=""
            )

            if result == 0:
                return {
                    'success': True,
                    'message': f'매수 주문 성공: {stock_code} {quantity}주',
                    'stock_code': stock_code,
                    'quantity': quantity,
                    'price': price,
                    'order_type': order_type
                }
            else:
                return {
                    'success': False,
                    'message': f'매수 주문 실패: 오류 코드 {result}'
                }

        except Exception as e:
            logger.error(f"매수 주문 오류: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def sell_stock(self, stock_code: str, quantity: int, price: int = 0, order_type: str = "지정가") -> Dict[str, Any]:
        """
        주식 매도

        Args:
            stock_code: 종목코드 (6자리)
            quantity: 수량
            price: 가격 (0이면 시장가)
            order_type: 주문유형 ("지정가" or "시장가")

        Returns:
            주문 결과
        """
        if not self.connected:
            return {'success': False, 'message': '연결되지 않음'}

        if self.simulation_mode:
            return {
                'success': True,
                'message': f'[시뮬레이션] 매도 주문: {stock_code} {quantity}주',
                'stock_code': stock_code,
                'quantity': quantity,
                'price': price,
                'order_type': order_type,
                'timestamp': datetime.now().isoformat()
            }

        try:
            # 호가 유형 결정
            hoga_gb = "00" if order_type == "지정가" else "03"

            # 주문 전송
            result = self.api.send_order(
                rqname="매도주문",
                screen_no="0101",
                acc_no=self.account_no,
                order_type=2,  # 2: 신규매도
                code=stock_code,
                qty=quantity,
                price=price,
                hoga_gb=hoga_gb,
                org_order_no=""
            )

            if result == 0:
                return {
                    'success': True,
                    'message': f'매도 주문 성공: {stock_code} {quantity}주',
                    'stock_code': stock_code,
                    'quantity': quantity,
                    'price': price,
                    'order_type': order_type
                }
            else:
                return {
                    'success': False,
                    'message': f'매도 주문 실패: 오류 코드 {result}'
                }

        except Exception as e:
            logger.error(f"매도 주문 오류: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def get_stock_price(self, stock_code: str) -> Dict[str, Any]:
        """
        주식 현재가 조회

        Args:
            stock_code: 종목코드 (6자리)

        Returns:
            시세 정보
        """
        if not self.connected:
            return {'success': False, 'message': '연결되지 않음'}

        if self.simulation_mode:
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

        try:
            # opt10001: 주식기본정보요청
            self.api.set_input_value("종목코드", stock_code)
            self.api.comm_rq_data("주식기본정보", "opt10001", 0, "0101")

            # 데이터 파싱
            current_price = int(self.api.get_comm_data("opt10001", "주식기본정보", 0, "현재가"))
            open_price = int(self.api.get_comm_data("opt10001", "주식기본정보", 0, "시가"))
            high_price = int(self.api.get_comm_data("opt10001", "주식기본정보", 0, "고가"))
            low_price = int(self.api.get_comm_data("opt10001", "주식기본정보", 0, "저가"))
            volume = int(self.api.get_comm_data("opt10001", "주식기본정보", 0, "거래량"))

            return {
                'success': True,
                'stock_code': stock_code,
                'current_price': abs(current_price),
                'open_price': abs(open_price),
                'high_price': abs(high_price),
                'low_price': abs(low_price),
                'volume': volume,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"시세 조회 오류: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def get_account_info(self) -> Dict[str, Any]:
        """
        계좌 잔고 조회

        Returns:
            계좌 정보 및 보유 종목
        """
        if not self.connected:
            return {'success': False, 'message': '연결되지 않음'}

        if self.simulation_mode:
            return {
                'success': True,
                'account_no': self.account_no,
                'total_balance': 10000000,
                'available_cash': 8000000,
                'total_profit_loss': 200000,
                'positions': [
                    {
                        'stock_code': '005930',
                        'stock_name': '삼성전자',
                        'quantity': 10,
                        'average_price': 70000,
                        'current_price': 72000,
                        'profit_loss': 20000
                    }
                ]
            }

        try:
            # opw00018: 계좌평가잔고내역요청
            self.api.set_input_value("계좌번호", self.account_no)
            self.api.set_input_value("비밀번호", "")
            self.api.set_input_value("비밀번호입력매체구분", "00")
            self.api.set_input_value("조회구분", "1")
            self.api.comm_rq_data("계좌평가잔고", "opw00018", 0, "0101")

            # 예수금 조회
            total_balance = int(self.api.get_comm_data("opw00018", "계좌평가잔고", 0, "총평가금액"))

            # 보유 종목 조회
            cnt = self.api.get_repeat_cnt("opw00018", "계좌평가잔고")
            positions = []

            for i in range(cnt):
                stock_code = self.api.get_comm_data("opw00018", "계좌평가잔고", i, "종목번호")
                stock_name = self.api.get_comm_data("opw00018", "계좌평가잔고", i, "종목명")
                quantity = int(self.api.get_comm_data("opw00018", "계좌평가잔고", i, "보유수량"))
                avg_price = int(self.api.get_comm_data("opw00018", "계좌평가잔고", i, "매입가"))
                current_price = int(self.api.get_comm_data("opw00018", "계좌평가잔고", i, "현재가"))
                profit_loss = int(self.api.get_comm_data("opw00018", "계좌평가잔고", i, "평가손익"))

                positions.append({
                    'stock_code': stock_code.strip(),
                    'stock_name': stock_name.strip(),
                    'quantity': quantity,
                    'average_price': avg_price,
                    'current_price': abs(current_price),
                    'profit_loss': profit_loss
                })

            return {
                'success': True,
                'account_no': self.account_no,
                'total_balance': total_balance,
                'positions': positions
            }

        except Exception as e:
            logger.error(f"계좌 조회 오류: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def disconnect(self):
        """연결 종료"""
        if self.api:
            self.api.disconnect()
        self.connected = False


# 싱글톤 인스턴스
_kiwoom_client = None


def get_kiwoom_client(account_no: Optional[str] = None, simulation_mode: bool = True) -> KiwoomClient:
    """
    키움 클라이언트 싱글톤 인스턴스 반환

    Args:
        account_no: 계좌번호
        simulation_mode: 시뮬레이션 모드 (기본값: True)
    """
    global _kiwoom_client
    if _kiwoom_client is None:
        _kiwoom_client = KiwoomClient(account_no=account_no, simulation_mode=simulation_mode)
        if simulation_mode:
            _kiwoom_client.connect()
    return _kiwoom_client


if __name__ == "__main__":
    # 테스트 (시뮬레이션 모드)
    client = get_kiwoom_client(simulation_mode=True)

    print("\n=== 연결 정보 ===")
    conn_info = client.connect()
    print(conn_info)

    print("\n=== 삼성전자 시세 ===")
    price = client.get_stock_price("005930")
    print(price)

    print("\n=== 계좌 정보 ===")
    account = client.get_account_info()
    print(account)

    print("\n=== 매수 주문 (시뮬레이션) ===")
    buy_result = client.buy_stock("005930", 10, 70000, "지정가")
    print(buy_result)

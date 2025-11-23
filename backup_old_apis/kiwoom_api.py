"""
키움증권 OpenAPI+ 클라이언트
PyQt5 기반 Active-X 연동 모듈
"""

import sys
import os
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QEventLoop
import time
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config


class KiwoomAPI:
    """키움증권 OpenAPI 클라이언트"""

    def __init__(self):
        """초기화"""
        self.app = QApplication.instance()
        if not self.app:
            self.app = QApplication(sys.argv)

        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.connected = False
        self.account_list = []
        self.account_no = Config.KIWOOM_ACCOUNT_NO

        # TR 요청 데이터 저장
        self.tr_data = {}
        self.order_data = {}

        # 이벤트 루프
        self.login_event_loop = QEventLoop()
        self.tr_event_loop = QEventLoop()
        self.order_event_loop = QEventLoop()

        # 이벤트 슬롯 연결
        self._connect_slots()

    def _connect_slots(self):
        """이벤트 슬롯 연결"""
        self.ocx.OnEventConnect.connect(self._on_event_connect)
        self.ocx.OnReceiveTrData.connect(self._on_receive_tr_data)
        self.ocx.OnReceiveChejanData.connect(self._on_receive_chejan_data)
        self.ocx.OnReceiveMsg.connect(self._on_receive_msg)

    # ==================== 로그인 ====================

    def comm_connect(self):
        """로그인 요청"""
        self.ocx.dynamicCall("CommConnect()")
        self.login_event_loop.exec_()
        return self.connected

    def _on_event_connect(self, err_code):
        """로그인 이벤트 핸들러"""
        if err_code == 0:
            print("로그인 성공")
            self.connected = True
            self.account_list = self.get_login_info("ACCLIST").split(';')[:-1]
            if not self.account_no and self.account_list:
                self.account_no = self.account_list[0]
        else:
            print(f"로그인 실패: {err_code}")
            self.connected = False

        self.login_event_loop.exit()

    def get_login_info(self, tag):
        """로그인 정보 조회"""
        return self.ocx.dynamicCall("GetLoginInfo(QString)", tag)

    def get_connect_state(self):
        """연결 상태 확인"""
        return self.ocx.dynamicCall("GetConnectState()")

    # ==================== TR 데이터 요청 ====================

    def set_input_value(self, item_name, item_value):
        """TR 입력값 설정"""
        self.ocx.dynamicCall("SetInputValue(QString, QString)", item_name, item_value)

    def comm_rq_data(self, rq_name, tr_code, prev_next, screen_no):
        """TR 데이터 요청"""
        self.ocx.dynamicCall(
            "CommRqData(QString, QString, int, QString)",
            rq_name, tr_code, prev_next, screen_no
        )
        self.tr_event_loop.exec_()

    def _on_receive_tr_data(self, screen_no, rq_name, tr_code, record_name, prev_next):
        """TR 데이터 수신"""
        if rq_name == "주식기본정보":
            self._get_stock_basic_info(tr_code, rq_name)
        elif rq_name == "계좌평가잔고":
            self._get_account_balance(tr_code, rq_name)
        elif rq_name == "예수금상세현황":
            self._get_deposit(tr_code, rq_name)

        self.tr_event_loop.exit()

    def get_comm_data(self, tr_code, rq_name, index, item_name):
        """TR 데이터 추출"""
        return self.ocx.dynamicCall(
            "GetCommData(QString, QString, int, QString)",
            tr_code, rq_name, index, item_name
        ).strip()

    def get_repeat_cnt(self, tr_code, rq_name):
        """반복 데이터 개수 조회"""
        return self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", tr_code, rq_name)

    # ==================== 현재가 조회 ====================

    def get_current_price(self, stock_code):
        """주식 현재가 조회 (OPT10001)"""
        self.set_input_value("종목코드", stock_code)
        self.comm_rq_data("주식기본정보", "OPT10001", 0, "0101")

        time.sleep(0.2)  # TR 요청 제한 (초당 5회)

        return self.tr_data.get('주식기본정보', None)

    def _get_stock_basic_info(self, tr_code, rq_name):
        """주식 기본 정보 파싱"""
        stock_code = self.get_comm_data(tr_code, rq_name, 0, "종목코드")
        current_price = abs(int(self.get_comm_data(tr_code, rq_name, 0, "현재가")))
        open_price = abs(int(self.get_comm_data(tr_code, rq_name, 0, "시가")))
        high_price = abs(int(self.get_comm_data(tr_code, rq_name, 0, "고가")))
        low_price = abs(int(self.get_comm_data(tr_code, rq_name, 0, "저가")))
        volume = abs(int(self.get_comm_data(tr_code, rq_name, 0, "거래량")))
        change_rate = float(self.get_comm_data(tr_code, rq_name, 0, "등락율"))

        self.tr_data['주식기본정보'] = {
            'stock_code': stock_code,
            'current_price': current_price,
            'open_price': open_price,
            'high_price': high_price,
            'low_price': low_price,
            'volume': volume,
            'change_rate': change_rate
        }

    # ==================== 계좌 정보 ====================

    def get_balance(self):
        """계좌 잔고 조회 (OPW00018)"""
        if not self.account_no:
            return {'success': False, 'message': '계좌번호가 설정되지 않았습니다.'}

        # 예수금 조회
        self.set_input_value("계좌번호", self.account_no)
        self.comm_rq_data("예수금상세현황", "OPW00001", 0, "0102")
        time.sleep(0.2)

        # 잔고 조회
        self.set_input_value("계좌번호", self.account_no)
        self.set_input_value("비밀번호", "")
        self.set_input_value("비밀번호입력매체구분", "00")
        self.set_input_value("조회구분", "2")
        self.comm_rq_data("계좌평가잔고", "OPW00018", 0, "0103")
        time.sleep(0.2)

        deposit_data = self.tr_data.get('예수금상세현황', {})
        balance_data = self.tr_data.get('계좌평가잔고', {})

        return {
            'success': True,
            'positions': balance_data.get('positions', []),
            'total_eval_amount': balance_data.get('total_eval_amount', 0),
            'total_purchase_amount': balance_data.get('total_purchase_amount', 0),
            'total_profit_loss': balance_data.get('total_profit_loss', 0),
            'cash_balance': deposit_data.get('cash_balance', 0)
        }

    def _get_deposit(self, tr_code, rq_name):
        """예수금 파싱"""
        cash_balance = abs(int(self.get_comm_data(tr_code, rq_name, 0, "예수금")))
        d2_deposit = abs(int(self.get_comm_data(tr_code, rq_name, 0, "d+2출금가능금액")))

        self.tr_data['예수금상세현황'] = {
            'cash_balance': cash_balance,
            'd2_deposit': d2_deposit
        }

    def _get_account_balance(self, tr_code, rq_name):
        """계좌 잔고 파싱"""
        positions = []
        count = self.get_repeat_cnt(tr_code, rq_name)

        for i in range(count):
            stock_code = self.get_comm_data(tr_code, rq_name, i, "종목번호").strip()
            stock_name = self.get_comm_data(tr_code, rq_name, i, "종목명").strip()
            quantity = abs(int(self.get_comm_data(tr_code, rq_name, i, "보유수량")))
            avg_price = abs(int(self.get_comm_data(tr_code, rq_name, i, "매입가")))
            current_price = abs(int(self.get_comm_data(tr_code, rq_name, i, "현재가")))
            eval_amount = abs(int(self.get_comm_data(tr_code, rq_name, i, "평가금액")))
            profit_loss = int(self.get_comm_data(tr_code, rq_name, i, "평가손익"))
            profit_rate = float(self.get_comm_data(tr_code, rq_name, i, "수익률(%)"))

            positions.append({
                'stock_code': stock_code,
                'stock_name': stock_name,
                'quantity': quantity,
                'avg_price': avg_price,
                'current_price': current_price,
                'eval_amount': eval_amount,
                'profit_loss': profit_loss,
                'profit_rate': profit_rate
            })

        # 계좌 총평가
        total_purchase = abs(int(self.get_comm_data(tr_code, rq_name, 0, "총매입금액")))
        total_eval = abs(int(self.get_comm_data(tr_code, rq_name, 0, "총평가금액")))
        total_profit = int(self.get_comm_data(tr_code, rq_name, 0, "총평가손익금액"))

        self.tr_data['계좌평가잔고'] = {
            'positions': positions,
            'total_purchase_amount': total_purchase,
            'total_eval_amount': total_eval,
            'total_profit_loss': total_profit
        }

    # ==================== 주문 ====================

    def send_order(self, rq_name, screen_no, acc_no, order_type, code, qty, price, hoga_gb, org_order_no):
        """주문 전송

        Args:
            rq_name: 사용자 구분명
            screen_no: 화면번호
            acc_no: 계좌번호
            order_type: 주문 유형 (1:신규매수, 2:신규매도, 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정)
            code: 종목코드
            qty: 주문수량
            price: 주문가격
            hoga_gb: 거래구분 (00:지정가, 03:시장가)
            org_order_no: 원주문번호 (정정/취소 시)
        """
        ret = self.ocx.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [rq_name, screen_no, acc_no, order_type, code, qty, price, hoga_gb, org_order_no]
        )

        self.order_event_loop.exec_()

        return self.order_data

    def buy_stock(self, stock_code, quantity, price=0):
        """매수 주문

        Args:
            stock_code: 종목코드
            quantity: 수량
            price: 가격 (0이면 시장가)
        """
        if not self.account_no:
            return {'success': False, 'message': '계좌번호가 설정되지 않았습니다.'}

        hoga_gb = "03" if price == 0 else "00"  # 시장가/지정가
        order_type = 1  # 신규매수

        result = self.send_order(
            "매수주문", "0101", self.account_no,
            order_type, stock_code, quantity, price, hoga_gb, ""
        )

        return result

    def sell_stock(self, stock_code, quantity, price=0):
        """매도 주문

        Args:
            stock_code: 종목코드
            quantity: 수량
            price: 가격 (0이면 시장가)
        """
        if not self.account_no:
            return {'success': False, 'message': '계좌번호가 설정되지 않았습니다.'}

        hoga_gb = "03" if price == 0 else "00"
        order_type = 2  # 신규매도

        result = self.send_order(
            "매도주문", "0101", self.account_no,
            order_type, stock_code, quantity, price, hoga_gb, ""
        )

        return result

    def _on_receive_msg(self, screen_no, rq_name, tr_code, msg):
        """서버 메시지 수신"""
        print(f"[서버] {msg}")

    def _on_receive_chejan_data(self, gubun, item_cnt, fid_list):
        """체결 데이터 수신

        Args:
            gubun: 0:주문체결, 1:잔고
        """
        if gubun == "0":  # 주문체결
            order_no = self.get_chejan_data("9203")  # 주문번호
            order_status = self.get_chejan_data("913")  # 주문상태
            stock_code = self.get_chejan_data("9001")  # 종목코드
            stock_name = self.get_chejan_data("302")  # 종목명
            order_qty = self.get_chejan_data("900")  # 주문수량
            order_price = self.get_chejan_data("901")  # 주문가격
            conclusion_qty = self.get_chejan_data("911")  # 체결수량
            conclusion_price = self.get_chejan_data("910")  # 체결가격

            self.order_data = {
                'success': True,
                'order_no': order_no,
                'order_status': order_status,
                'stock_code': stock_code,
                'stock_name': stock_name,
                'order_qty': order_qty,
                'order_price': order_price,
                'conclusion_qty': conclusion_qty,
                'conclusion_price': conclusion_price,
                'message': f'{stock_name} 주문 완료'
            }

            self.order_event_loop.exit()

    def get_chejan_data(self, fid):
        """체결 데이터 항목별 조회"""
        return self.ocx.dynamicCall("GetChejanData(int)", int(fid)).strip()

    # ==================== 기타 유틸리티 ====================

    def get_code_list_by_market(self, market):
        """시장별 종목코드 리스트

        Args:
            market: 0:장내, 10:코스닥, 8:ETF
        """
        code_list = self.ocx.dynamicCall("GetCodeListByMarket(QString)", market)
        return code_list.split(';')[:-1]

    def get_master_code_name(self, code):
        """종목명 조회"""
        return self.ocx.dynamicCall("GetMasterCodeName(QString)", code)

    def disconnect(self):
        """연결 종료"""
        self.ocx.dynamicCall("CommTerminate()")


# ==================== 싱글톤 인스턴스 ====================

_kiwoom_instance = None


def get_kiwoom_api():
    """키움 API 싱글톤 인스턴스 반환"""
    global _kiwoom_instance
    if _kiwoom_instance is None:
        _kiwoom_instance = KiwoomAPI()
    return _kiwoom_instance

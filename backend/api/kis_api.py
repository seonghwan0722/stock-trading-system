import requests
import json
from datetime import datetime
from backend.config import Config


class KISApi:
    """한국투자증권 OpenAPI 클라이언트"""

    def __init__(self):
        self.base_url = Config.KIS_BASE_URL
        self.app_key = Config.KIS_APP_KEY
        self.app_secret = Config.KIS_APP_SECRET
        self.cano = Config.KIS_CANO
        self.acnt_prdt_cd = Config.KIS_ACNT_PRDT_CD
        self.access_token = None

    def _get_headers(self, tr_id):
        """API 요청 헤더 생성"""
        if not self.access_token:
            self.get_access_token()

        return {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id
        }

    def get_access_token(self):
        """접근 토큰 발급"""
        url = f"{self.base_url}/oauth2/tokenP"
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }

        try:
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
            self.access_token = data.get("access_token")
            return self.access_token
        except Exception as e:
            print(f"토큰 발급 실패: {e}")
            return None

    def get_current_price(self, stock_code):
        """현재가 조회"""
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = self._get_headers("FHKST01010100")

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stock_code
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("rt_cd") == "0":
                output = data.get("output", {})
                return {
                    "stock_code": stock_code,
                    "current_price": int(output.get("stck_prpr", 0)),
                    "change_rate": float(output.get("prdy_ctrt", 0)),
                    "volume": int(output.get("acml_vol", 0)),
                    "high_price": int(output.get("stck_hgpr", 0)),
                    "low_price": int(output.get("stck_lwpr", 0)),
                    "open_price": int(output.get("stck_oprc", 0))
                }
            else:
                print(f"현재가 조회 실패: {data.get('msg1')}")
                return None
        except Exception as e:
            print(f"현재가 조회 오류: {e}")
            return None

    def buy_stock(self, stock_code, quantity, price=0):
        """주식 매수

        Args:
            stock_code: 종목코드
            quantity: 수량
            price: 지정가 (0이면 시장가)
        """
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"
        headers = self._get_headers("TTTC0802U")  # 현금 매수 주문

        order_type = "01" if price > 0 else "01"  # 01: 시장가, 00: 지정가

        body = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "PDNO": stock_code,
            "ORD_DVSN": order_type,
            "ORD_QTY": str(quantity),
            "ORD_UNPR": str(price) if price > 0 else "0"
        }

        try:
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()

            if data.get("rt_cd") == "0":
                return {
                    "success": True,
                    "order_no": data.get("output", {}).get("ODNO"),
                    "message": data.get("msg1")
                }
            else:
                return {
                    "success": False,
                    "message": data.get("msg1")
                }
        except Exception as e:
            print(f"매수 주문 오류: {e}")
            return {"success": False, "message": str(e)}

    def sell_stock(self, stock_code, quantity, price=0):
        """주식 매도

        Args:
            stock_code: 종목코드
            quantity: 수량
            price: 지정가 (0이면 시장가)
        """
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"
        headers = self._get_headers("TTTC0801U")  # 현금 매도 주문

        order_type = "01" if price > 0 else "01"

        body = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "PDNO": stock_code,
            "ORD_DVSN": order_type,
            "ORD_QTY": str(quantity),
            "ORD_UNPR": str(price) if price > 0 else "0"
        }

        try:
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()

            if data.get("rt_cd") == "0":
                return {
                    "success": True,
                    "order_no": data.get("output", {}).get("ODNO"),
                    "message": data.get("msg1")
                }
            else:
                return {
                    "success": False,
                    "message": data.get("msg1")
                }
        except Exception as e:
            print(f"매도 주문 오류: {e}")
            return {"success": False, "message": str(e)}

    def get_balance(self):
        """계좌 잔고 조회"""
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
        headers = self._get_headers("TTTC8434R")

        params = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("rt_cd") == "0":
                output1 = data.get("output1", [])
                output2 = data.get("output2", [{}])[0]

                positions = []
                for item in output1:
                    positions.append({
                        "stock_code": item.get("pdno"),
                        "stock_name": item.get("prdt_name"),
                        "quantity": int(item.get("hldg_qty", 0)),
                        "avg_price": float(item.get("pchs_avg_pric", 0)),
                        "current_price": float(item.get("prpr", 0)),
                        "eval_amount": int(item.get("evlu_amt", 0)),
                        "profit_loss": int(item.get("evlu_pfls_amt", 0)),
                        "profit_rate": float(item.get("evlu_pfls_rt", 0))
                    })

                return {
                    "success": True,
                    "positions": positions,
                    "total_eval_amount": int(output2.get("tot_evlu_amt", 0)),
                    "total_purchase_amount": int(output2.get("pchs_amt_smtl_amt", 0)),
                    "total_profit_loss": int(output2.get("evlu_pfls_smtl_amt", 0)),
                    "cash_balance": int(output2.get("dnca_tot_amt", 0))
                }
            else:
                return {"success": False, "message": data.get("msg1")}
        except Exception as e:
            print(f"잔고 조회 오류: {e}")
            return {"success": False, "message": str(e)}

    def get_stock_info(self, stock_code):
        """종목 상세 정보 조회"""
        price_info = self.get_current_price(stock_code)

        if price_info:
            return {
                "success": True,
                "data": price_info
            }
        else:
            return {"success": False, "message": "종목 정보 조회 실패"}

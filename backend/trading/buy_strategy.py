import anthropic
from backend.config import Config
from backend.api.kis_api import KISApi


class BuyStrategy:
    """AI 기반 매수 판단 전략"""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.kis_api = KISApi()

    def analyze_stock_for_buy(self, stock_code, stock_name, additional_info=None):
        """주식 매수 판단 분석

        Args:
            stock_code: 종목 코드
            stock_name: 종목 명
            additional_info: 추가 정보 (뉴스, 재무제표 등)

        Returns:
            dict: {
                "should_buy": bool,
                "confidence": float,
                "reason": str,
                "recommended_quantity": int,
                "target_price": int
            }
        """
        # 현재 주식 정보 조회
        stock_info = self.kis_api.get_current_price(stock_code)

        if not stock_info:
            return {
                "should_buy": False,
                "confidence": 0.0,
                "reason": "주식 정보를 가져올 수 없습니다.",
                "recommended_quantity": 0,
                "target_price": 0
            }

        # 계좌 정보 조회
        balance_info = self.kis_api.get_balance()

        # AI에게 분석 요청
        analysis_prompt = self._create_analysis_prompt(
            stock_code, stock_name, stock_info, balance_info, additional_info
        )

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": analysis_prompt}
                ]
            )

            ai_response = message.content[0].text
            result = self._parse_ai_response(ai_response, stock_info)

            return result

        except Exception as e:
            print(f"AI 분석 오류: {e}")
            return {
                "should_buy": False,
                "confidence": 0.0,
                "reason": f"AI 분석 중 오류 발생: {str(e)}",
                "recommended_quantity": 0,
                "target_price": 0
            }

    def _create_analysis_prompt(self, stock_code, stock_name, stock_info, balance_info, additional_info):
        """AI 분석을 위한 프롬프트 생성"""

        prompt = f"""당신은 한국 주식 시장의 전문 투자 분석가입니다. 다음 정보를 바탕으로 매수 여부를 판단해주세요.

## 종목 정보
- 종목코드: {stock_code}
- 종목명: {stock_name}
- 현재가: {stock_info['current_price']:,}원
- 등락률: {stock_info['change_rate']}%
- 거래량: {stock_info['volume']:,}주
- 고가: {stock_info['high_price']:,}원
- 저가: {stock_info['low_price']:,}원
- 시가: {stock_info['open_price']:,}원

## 계좌 정보
- 사용 가능 현금: {balance_info.get('cash_balance', 0):,}원
- 현재 보유 종목 수: {len(balance_info.get('positions', []))}개
- 최대 보유 가능 종목 수: {Config.MAX_POSITIONS}개
- 최대 포지션 크기: {Config.MAX_POSITION_SIZE:,}원
"""

        if additional_info:
            prompt += f"\n## 추가 정보\n{additional_info}\n"

        prompt += """
## 분석 요청사항

다음 형식으로 정확하게 답변해주세요:

**매수 판단**: YES 또는 NO
**신뢰도**: 0.0 ~ 1.0 사이의 숫자
**추천 매수 수량**: 정수 (주)
**목표가**: 정수 (원)
**판단 근거**:
- 기술적 분석 관점
- 거래량 분석
- 가격 추세 분석
- 리스크 평가
- 기타 고려사항

매수 판단 시 고려사항:
1. 계좌 잔고를 초과하지 않을 것
2. 최대 포지션 크기를 초과하지 않을 것
3. 현재 보유 종목 수가 최대치를 넘지 않을 것
4. 기술적 지표가 양호할 것
5. 리스크 대비 수익률이 적절할 것

보수적이고 신중하게 판단해주세요.
"""

        return prompt

    def _parse_ai_response(self, ai_response, stock_info):
        """AI 응답 파싱"""

        should_buy = False
        confidence = 0.0
        recommended_quantity = 0
        target_price = 0
        reason = ai_response

        # 매수 판단 파싱
        if "YES" in ai_response.upper() or "매수" in ai_response:
            should_buy = True

        # 신뢰도 파싱
        try:
            if "신뢰도" in ai_response:
                for line in ai_response.split("\n"):
                    if "신뢰도" in line:
                        confidence_str = line.split(":")[-1].strip()
                        confidence = float(confidence_str.replace("%", "").strip())
                        if confidence > 1.0:
                            confidence = confidence / 100.0
                        break
        except:
            confidence = 0.5

        # 추천 수량 파싱
        try:
            if "추천 매수 수량" in ai_response or "수량" in ai_response:
                for line in ai_response.split("\n"):
                    if "수량" in line and "추천" in line:
                        quantity_str = line.split(":")[-1].strip().replace("주", "").replace(",", "")
                        recommended_quantity = int(quantity_str)
                        break
        except:
            recommended_quantity = 0

        # 목표가 파싱
        try:
            if "목표가" in ai_response:
                for line in ai_response.split("\n"):
                    if "목표가" in line:
                        price_str = line.split(":")[-1].strip().replace("원", "").replace(",", "")
                        target_price = int(price_str)
                        break
        except:
            target_price = stock_info['current_price']

        return {
            "should_buy": should_buy,
            "confidence": confidence,
            "reason": reason,
            "recommended_quantity": recommended_quantity,
            "target_price": target_price
        }

    def execute_buy(self, stock_code, quantity):
        """매수 실행"""
        result = self.kis_api.buy_stock(stock_code, quantity, price=0)
        return result

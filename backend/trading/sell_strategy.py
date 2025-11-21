import anthropic
from backend.config import Config
from backend.api.kis_api import KISApi


class SellStrategy:
    """AI 기반 매도 판단 전략"""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.kis_api = KISApi()

    def analyze_stock_for_sell(self, position, additional_info=None):
        """주식 매도 판단 분석

        Args:
            position: 보유 포지션 정보
                {
                    "stock_code": str,
                    "stock_name": str,
                    "quantity": int,
                    "avg_price": float,
                    "current_price": float,
                    "profit_loss": int,
                    "profit_rate": float
                }
            additional_info: 추가 정보 (뉴스, 시장 상황 등)

        Returns:
            dict: {
                "should_sell": bool,
                "confidence": float,
                "reason": str,
                "recommended_quantity": int,
                "urgency": str  # "high", "medium", "low"
            }
        """
        # 현재 주식 정보 조회
        stock_info = self.kis_api.get_current_price(position['stock_code'])

        if not stock_info:
            return {
                "should_sell": False,
                "confidence": 0.0,
                "reason": "주식 정보를 가져올 수 없습니다.",
                "recommended_quantity": 0,
                "urgency": "low"
            }

        # AI에게 분석 요청
        analysis_prompt = self._create_analysis_prompt(
            position, stock_info, additional_info
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
            result = self._parse_ai_response(ai_response, position)

            return result

        except Exception as e:
            print(f"AI 분석 오류: {e}")
            return {
                "should_sell": False,
                "confidence": 0.0,
                "reason": f"AI 분석 중 오류 발생: {str(e)}",
                "recommended_quantity": 0,
                "urgency": "low"
            }

    def _create_analysis_prompt(self, position, stock_info, additional_info):
        """AI 분석을 위한 프롬프트 생성"""

        prompt = f"""당신은 한국 주식 시장의 전문 투자 분석가입니다. 현재 보유 중인 종목의 매도 여부를 판단해주세요.

## 보유 포지션 정보
- 종목코드: {position['stock_code']}
- 종목명: {position['stock_name']}
- 보유 수량: {position['quantity']:,}주
- 평균 매수가: {position['avg_price']:,.0f}원
- 현재가: {position['current_price']:,.0f}원
- 평가손익: {position['profit_loss']:,}원
- 수익률: {position['profit_rate']:.2f}%

## 현재 시장 정보
- 현재가: {stock_info['current_price']:,}원
- 등락률: {stock_info['change_rate']}%
- 거래량: {stock_info['volume']:,}주
- 고가: {stock_info['high_price']:,}원
- 저가: {stock_info['low_price']:,}원
- 시가: {stock_info['open_price']:,}원
"""

        if additional_info:
            prompt += f"\n## 추가 정보\n{additional_info}\n"

        prompt += """
## 분석 요청사항

다음 형식으로 정확하게 답변해주세요:

**매도 판단**: YES 또는 NO
**신뢰도**: 0.0 ~ 1.0 사이의 숫자
**추천 매도 수량**: 정수 (주) - 전체 또는 일부
**긴급도**: HIGH, MEDIUM, LOW 중 하나
**판단 근거**:
- 수익률 분석
- 기술적 분석 관점
- 추세 전환 신호
- 리스크 평가
- 손절/익절 판단
- 기타 고려사항

매도 판단 시 고려사항:
1. 목표 수익률 달성 여부
2. 손절 라인 도달 여부 (보통 -5% ~ -10%)
3. 기술적 지표 악화
4. 거래량 감소 또는 이상 신호
5. 시장 전반적인 약세
6. 부정적 뉴스나 이슈

**매도 전략**:
- 익절: 수익률이 10% 이상이고 추세가 약화되는 경우
- 손절: 손실률이 7% 이상인 경우
- 부분 매도: 수익은 나지만 불확실성이 높은 경우

보수적이고 신중하게 판단해주세요. 손실을 최소화하는 것이 우선입니다.
"""

        return prompt

    def _parse_ai_response(self, ai_response, position):
        """AI 응답 파싱"""

        should_sell = False
        confidence = 0.0
        recommended_quantity = 0
        urgency = "low"
        reason = ai_response

        # 매도 판단 파싱
        if "YES" in ai_response.upper() or "매도" in ai_response:
            should_sell = True

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
            if "추천 매도 수량" in ai_response or "수량" in ai_response:
                for line in ai_response.split("\n"):
                    if "수량" in line and "추천" in line:
                        quantity_str = line.split(":")[-1].strip().replace("주", "").replace(",", "")
                        if "전체" in quantity_str or "모두" in quantity_str:
                            recommended_quantity = position['quantity']
                        else:
                            recommended_quantity = int(quantity_str)
                        break
        except:
            # 기본값: 전체 매도
            recommended_quantity = position['quantity']

        # 긴급도 파싱
        if "HIGH" in ai_response.upper() or "긴급" in ai_response:
            urgency = "high"
        elif "MEDIUM" in ai_response.upper() or "중간" in ai_response:
            urgency = "medium"
        else:
            urgency = "low"

        return {
            "should_sell": should_sell,
            "confidence": confidence,
            "reason": reason,
            "recommended_quantity": recommended_quantity,
            "urgency": urgency
        }

    def execute_sell(self, stock_code, quantity):
        """매도 실행"""
        result = self.kis_api.sell_stock(stock_code, quantity, price=0)
        return result

    def check_stop_loss(self, position, stop_loss_rate=-7.0):
        """손절 체크

        Args:
            position: 포지션 정보
            stop_loss_rate: 손절 비율 (기본 -7%)

        Returns:
            bool: 손절 필요 여부
        """
        return position['profit_rate'] <= stop_loss_rate

    def check_take_profit(self, position, take_profit_rate=15.0):
        """익절 체크

        Args:
            position: 포지션 정보
            take_profit_rate: 익절 비율 (기본 15%)

        Returns:
            bool: 익절 필요 여부
        """
        return position['profit_rate'] >= take_profit_rate

"""
매매 전략 모음
- 다양한 매수/매도 전략을 정의하고 관리하는 모듈
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.api.finnhub_client import get_finnhub_client


# ==================== 매수 전략 베이스 ====================

class BuyStrategyBase(ABC):
    """매수 전략 베이스 클래스"""

    def __init__(self, params: Dict[str, Any] = None):
        self.params = params or {}
        self.finnhub_client = get_finnhub_client()

    @abstractmethod
    def should_buy(self, stock_info: Dict, balance_info: Dict, additional_info: Dict = None) -> Dict:
        """
        매수 판단 로직

        Returns:
            {
                "should_buy": bool,
                "confidence": float (0.0 ~ 1.0),
                "reason": str,
                "recommended_quantity": int,
                "target_price": int
            }
        """
        pass

    @abstractmethod
    def get_description(self) -> str:
        """전략 설명"""
        pass

    @abstractmethod
    def get_parameters(self) -> Dict:
        """파라미터 정의"""
        pass


# ==================== 매도 전략 베이스 ====================

class SellStrategyBase(ABC):
    """매도 전략 베이스 클래스"""

    def __init__(self, params: Dict[str, Any] = None):
        self.params = params or {}
        self.finnhub_client = get_finnhub_client()

    @abstractmethod
    def should_sell(self, position: Dict, stock_info: Dict, additional_info: Dict = None) -> Dict:
        """
        매도 판단 로직

        Returns:
            {
                "should_sell": bool,
                "confidence": float (0.0 ~ 1.0),
                "reason": str,
                "recommended_quantity": int,
                "urgency": str  # "high", "medium", "low"
            }
        """
        pass

    @abstractmethod
    def get_description(self) -> str:
        """전략 설명"""
        pass

    @abstractmethod
    def get_parameters(self) -> Dict:
        """파라미터 정의"""
        pass


# ==================== 매수 전략 구현 ====================

class MomentumBuyStrategy(BuyStrategyBase):
    """모멘텀 매수 전략 - 상승 추세 포착"""

    def get_description(self) -> str:
        return """
        모멘텀 매수 전략
        - 급격한 상승세와 거래량 증가를 포착하여 매수
        - 단기 급등주 포착에 유리
        - 리스크: 고점 매수 위험
        """

    def get_parameters(self) -> Dict:
        return {
            "min_change_rate": {
                "name": "최소 등락률",
                "description": "매수 기준 최소 등락률 (%)",
                "type": "float",
                "default": 3.0,
                "min": 0.0,
                "max": 30.0
            },
            "min_volume_ratio": {
                "name": "최소 거래량 비율",
                "description": "평균 거래량 대비 최소 비율",
                "type": "float",
                "default": 1.5,
                "min": 1.0,
                "max": 10.0
            },
            "max_position_size": {
                "name": "최대 매수 금액",
                "description": "한 종목당 최대 매수 금액 (원)",
                "type": "int",
                "default": 1000000,
                "min": 100000,
                "max": 10000000
            }
        }

    def should_buy(self, stock_info: Dict, balance_info: Dict, additional_info: Dict = None) -> Dict:
        min_change_rate = self.params.get("min_change_rate", 3.0)
        min_volume_ratio = self.params.get("min_volume_ratio", 1.5)
        max_position_size = self.params.get("max_position_size", 1000000)

        current_price = stock_info.get('current_price', 0)
        change_rate = stock_info.get('change_rate', 0)
        volume = stock_info.get('volume', 0)
        avg_volume = stock_info.get('avg_volume', volume)

        # 거래량 비율 계산
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0

        # 매수 조건 체크
        should_buy = (
            change_rate >= min_change_rate and
            volume_ratio >= min_volume_ratio and
            current_price > 0
        )

        # 신뢰도 계산
        confidence = 0.0
        if should_buy:
            # 등락률 기여도 (최대 0.5)
            confidence += min(change_rate / (min_change_rate * 2), 0.5)
            # 거래량 기여도 (최대 0.5)
            confidence += min((volume_ratio - 1.0) / 4.0, 0.5)

        # 추천 수량 계산
        available_cash = balance_info.get('cash_balance', 0)
        buy_amount = min(max_position_size, available_cash * 0.2)  # 최대 20% 투자
        recommended_quantity = int(buy_amount / current_price) if current_price > 0 else 0

        reason = f"""
모멘텀 전략 분석:
- 등락률: {change_rate}% (기준: {min_change_rate}% 이상)
- 거래량 비율: {volume_ratio:.2f}배 (기준: {min_volume_ratio}배 이상)
- 판단: {"매수 신호 포착" if should_buy else "매수 조건 미충족"}
- 현재가: {current_price:,}원
"""

        return {
            "should_buy": should_buy,
            "confidence": round(confidence, 2),
            "reason": reason,
            "recommended_quantity": recommended_quantity,
            "target_price": int(current_price * 1.1)  # 10% 익절 목표
        }


class ValueBuyStrategy(BuyStrategyBase):
    """가치 매수 전략 - 저평가 종목 발굴"""

    def get_description(self) -> str:
        return """
        가치 매수 전략
        - 하락 후 반등 기회 포착
        - 안정적인 중장기 투자에 유리
        - 리스크: 추가 하락 가능성
        """

    def get_parameters(self) -> Dict:
        return {
            "max_change_rate": {
                "name": "최대 등락률",
                "description": "매수 기준 최대 등락률 (음수, %)",
                "type": "float",
                "default": -3.0,
                "min": -30.0,
                "max": 0.0
            },
            "min_price_ratio": {
                "name": "최소 가격 비율",
                "description": "저가 대비 현재가 비율 (낮을수록 저평가)",
                "type": "float",
                "default": 0.9,
                "min": 0.5,
                "max": 1.0
            },
            "max_position_size": {
                "name": "최대 매수 금액",
                "description": "한 종목당 최대 매수 금액 (원)",
                "type": "int",
                "default": 1000000,
                "min": 100000,
                "max": 10000000
            }
        }

    def should_buy(self, stock_info: Dict, balance_info: Dict, additional_info: Dict = None) -> Dict:
        max_change_rate = self.params.get("max_change_rate", -3.0)
        min_price_ratio = self.params.get("min_price_ratio", 0.9)
        max_position_size = self.params.get("max_position_size", 1000000)

        current_price = stock_info.get('current_price', 0)
        change_rate = stock_info.get('change_rate', 0)
        high_price = stock_info.get('high_price', current_price)

        # 가격 비율 (고가 대비 현재가)
        price_ratio = current_price / high_price if high_price > 0 else 1.0

        # 매수 조건
        should_buy = (
            change_rate <= max_change_rate and  # 하락
            price_ratio <= min_price_ratio and  # 저평가
            current_price > 0
        )

        # 신뢰도
        confidence = 0.0
        if should_buy:
            confidence += min(abs(change_rate) / abs(max_change_rate * 2), 0.5)
            confidence += min((1.0 - price_ratio) / 0.2, 0.5)

        # 추천 수량
        available_cash = balance_info.get('cash_balance', 0)
        buy_amount = min(max_position_size, available_cash * 0.25)
        recommended_quantity = int(buy_amount / current_price) if current_price > 0 else 0

        reason = f"""
가치 전략 분석:
- 등락률: {change_rate}% (기준: {max_change_rate}% 이하)
- 가격 비율: {price_ratio:.2%} (기준: {min_price_ratio:.2%} 이하)
- 판단: {"매수 신호 - 저평가 구간" if should_buy else "매수 조건 미충족"}
- 현재가: {current_price:,}원
"""

        return {
            "should_buy": should_buy,
            "confidence": round(confidence, 2),
            "reason": reason,
            "recommended_quantity": recommended_quantity,
            "target_price": int(current_price * 1.15)
        }


class BreakoutBuyStrategy(BuyStrategyBase):
    """돌파 매수 전략 - 저항선 돌파"""

    def get_description(self) -> str:
        return """
        돌파 매수 전략
        - 고가 돌파 시 추가 상승 기대
        - 강한 상승 모멘텀 포착
        - 리스크: 단기 조정 가능성
        """

    def get_parameters(self) -> Dict:
        return {
            "breakout_threshold": {
                "name": "돌파 기준",
                "description": "전일 고가 대비 돌파 비율 (%)",
                "type": "float",
                "default": 2.0,
                "min": 0.5,
                "max": 10.0
            },
            "min_volume_increase": {
                "name": "최소 거래량 증가율",
                "description": "평균 대비 최소 증가율 (%)",
                "type": "float",
                "default": 50.0,
                "min": 20.0,
                "max": 200.0
            },
            "max_position_size": {
                "name": "최대 매수 금액",
                "description": "한 종목당 최대 매수 금액 (원)",
                "type": "int",
                "default": 1000000,
                "min": 100000,
                "max": 10000000
            }
        }

    def should_buy(self, stock_info: Dict, balance_info: Dict, additional_info: Dict = None) -> Dict:
        breakout_threshold = self.params.get("breakout_threshold", 2.0)
        min_volume_increase = self.params.get("min_volume_increase", 50.0)
        max_position_size = self.params.get("max_position_size", 1000000)

        current_price = stock_info.get('current_price', 0)
        high_price = stock_info.get('high_price', 0)
        prev_high = stock_info.get('prev_high', high_price)  # 전일 고가
        volume = stock_info.get('volume', 0)
        avg_volume = stock_info.get('avg_volume', volume)

        # 돌파율 계산
        breakout_rate = ((current_price - prev_high) / prev_high * 100) if prev_high > 0 else 0
        volume_increase = ((volume - avg_volume) / avg_volume * 100) if avg_volume > 0 else 0

        should_buy = (
            breakout_rate >= breakout_threshold and
            volume_increase >= min_volume_increase and
            current_price > 0
        )

        confidence = 0.0
        if should_buy:
            confidence += min(breakout_rate / (breakout_threshold * 2), 0.5)
            confidence += min(volume_increase / (min_volume_increase * 2), 0.5)

        available_cash = balance_info.get('cash_balance', 0)
        buy_amount = min(max_position_size, available_cash * 0.2)
        recommended_quantity = int(buy_amount / current_price) if current_price > 0 else 0

        reason = f"""
돌파 전략 분석:
- 돌파율: {breakout_rate:.2f}% (기준: {breakout_threshold}% 이상)
- 거래량 증가: {volume_increase:.2f}% (기준: {min_volume_increase}% 이상)
- 판단: {"저항선 돌파 매수 신호" if should_buy else "돌파 조건 미충족"}
- 현재가: {current_price:,}원
"""

        return {
            "should_buy": should_buy,
            "confidence": round(confidence, 2),
            "reason": reason,
            "recommended_quantity": recommended_quantity,
            "target_price": int(current_price * 1.12)
        }


# ==================== 매도 전략 구현 ====================

class FixedRatioSellStrategy(SellStrategyBase):
    """고정 비율 매도 전략 - 손익률 기준"""

    def get_description(self) -> str:
        return """
        고정 비율 매도 전략
        - 설정한 수익률/손실률에 도달 시 자동 매도
        - 명확한 손익 기준으로 안정적 운영
        - 리스크: 추가 상승 기회 놓칠 수 있음
        """

    def get_parameters(self) -> Dict:
        return {
            "take_profit_rate": {
                "name": "익절 비율",
                "description": "목표 수익률 (%)",
                "type": "float",
                "default": 10.0,
                "min": 3.0,
                "max": 50.0
            },
            "stop_loss_rate": {
                "name": "손절 비율",
                "description": "손절 기준 손실률 (음수, %)",
                "type": "float",
                "default": -5.0,
                "min": -30.0,
                "max": -1.0
            },
            "partial_sell_ratio": {
                "name": "부분 매도 비율",
                "description": "익절 시 부분 매도 비율 (0=전체매도, 0.5=절반매도)",
                "type": "float",
                "default": 0.5,
                "min": 0.0,
                "max": 1.0
            }
        }

    def should_sell(self, position: Dict, stock_info: Dict, additional_info: Dict = None) -> Dict:
        take_profit_rate = self.params.get("take_profit_rate", 10.0)
        stop_loss_rate = self.params.get("stop_loss_rate", -5.0)
        partial_sell_ratio = self.params.get("partial_sell_ratio", 0.5)

        profit_rate = position.get('profit_rate', 0.0)
        quantity = position.get('quantity', 0)

        should_sell = False
        urgency = "low"
        reason = ""
        sell_quantity = 0

        # 손절 체크
        if profit_rate <= stop_loss_rate:
            should_sell = True
            urgency = "high"
            sell_quantity = quantity  # 전체 매도
            reason = f"""
손절 실행:
- 현재 수익률: {profit_rate:.2f}%
- 손절 기준: {stop_loss_rate}%
- 판단: 즉시 전체 매도 필요
- 손실 확정하여 추가 손실 방지
"""

        # 익절 체크
        elif profit_rate >= take_profit_rate:
            should_sell = True
            urgency = "medium"
            sell_quantity = int(quantity * partial_sell_ratio) if partial_sell_ratio < 1.0 else quantity
            reason = f"""
익절 실행:
- 현재 수익률: {profit_rate:.2f}%
- 익절 기준: {take_profit_rate}%
- 판단: {"부분" if partial_sell_ratio < 1.0 else "전체"} 매도
- 매도 비율: {partial_sell_ratio * 100:.0f}%
- 수익 실현 및 리스크 관리
"""
        else:
            reason = f"""
보유 유지:
- 현재 수익률: {profit_rate:.2f}%
- 익절 기준: {take_profit_rate}% 이상
- 손절 기준: {stop_loss_rate}% 이하
- 판단: 목표 범위 내 보유
"""

        confidence = 1.0 if should_sell else 0.0

        return {
            "should_sell": should_sell,
            "confidence": confidence,
            "reason": reason,
            "recommended_quantity": sell_quantity,
            "urgency": urgency
        }


class TrailingStopSellStrategy(SellStrategyBase):
    """후행 손절 매도 전략 - 추세 추종"""

    def get_description(self) -> str:
        return """
        후행 손절 매도 전략
        - 고점 대비 일정 비율 하락 시 매도
        - 상승 추세 최대한 활용
        - 리스크: 급락 시 손실 확대 가능
        """

    def get_parameters(self) -> Dict:
        return {
            "trailing_stop_rate": {
                "name": "후행 손절 비율",
                "description": "고점 대비 하락 비율 (%)",
                "type": "float",
                "default": 5.0,
                "min": 2.0,
                "max": 20.0
            },
            "min_profit_activate": {
                "name": "최소 수익률 활성화",
                "description": "후행 손절 활성화 최소 수익률 (%)",
                "type": "float",
                "default": 5.0,
                "min": 0.0,
                "max": 30.0
            },
            "emergency_stop_loss": {
                "name": "긴급 손절",
                "description": "긴급 손절 비율 (음수, %)",
                "type": "float",
                "default": -10.0,
                "min": -30.0,
                "max": -5.0
            }
        }

    def should_sell(self, position: Dict, stock_info: Dict, additional_info: Dict = None) -> Dict:
        trailing_stop_rate = self.params.get("trailing_stop_rate", 5.0)
        min_profit_activate = self.params.get("min_profit_activate", 5.0)
        emergency_stop_loss = self.params.get("emergency_stop_loss", -10.0)

        profit_rate = position.get('profit_rate', 0.0)
        current_price = position.get('current_price', 0)
        high_price = position.get('high_price', current_price)  # 보유 기간 최고가
        avg_price = position.get('avg_price', current_price)
        quantity = position.get('quantity', 0)

        # 고점 대비 하락률
        decline_from_high = ((current_price - high_price) / high_price * 100) if high_price > 0 else 0

        should_sell = False
        urgency = "low"
        reason = ""

        # 긴급 손절
        if profit_rate <= emergency_stop_loss:
            should_sell = True
            urgency = "high"
            reason = f"""
긴급 손절 발동:
- 현재 수익률: {profit_rate:.2f}%
- 긴급 손절 기준: {emergency_stop_loss}%
- 판단: 즉시 전체 매도
"""

        # 후행 손절 (수익 상태일 때만)
        elif profit_rate >= min_profit_activate and decline_from_high <= -trailing_stop_rate:
            should_sell = True
            urgency = "medium"
            reason = f"""
후행 손절 발동:
- 현재 수익률: {profit_rate:.2f}%
- 고점 대비 하락: {decline_from_high:.2f}%
- 후행 손절 기준: {-trailing_stop_rate}%
- 판단: 추세 전환 감지, 매도
"""
        else:
            reason = f"""
보유 유지:
- 현재 수익률: {profit_rate:.2f}%
- 고점 대비: {decline_from_high:.2f}%
- 후행 손절 기준: {-trailing_stop_rate}%
- 판단: {"수익 확대 중" if profit_rate > 0 else "손실 관리 중"}
"""

        confidence = 1.0 if should_sell else 0.0

        return {
            "should_sell": should_sell,
            "confidence": confidence,
            "reason": reason,
            "recommended_quantity": quantity,
            "urgency": urgency
        }


class VolatilityBasedSellStrategy(SellStrategyBase):
    """변동성 기반 매도 전략"""

    def get_description(self) -> str:
        return """
        변동성 기반 매도 전략
        - 급격한 가격 변동 시 매도
        - 리스크 관리 중심
        - 하락 전환 조기 감지
        """

    def get_parameters(self) -> Dict:
        return {
            "max_decline_rate": {
                "name": "최대 하락률",
                "description": "일일 최대 허용 하락률 (음수, %)",
                "type": "float",
                "default": -5.0,
                "min": -20.0,
                "max": -2.0
            },
            "volume_spike_threshold": {
                "name": "거래량 급증 기준",
                "description": "평균 대비 거래량 급증 배수",
                "type": "float",
                "default": 3.0,
                "min": 2.0,
                "max": 10.0
            },
            "take_profit_rate": {
                "name": "익절 비율",
                "description": "목표 수익률 (%)",
                "type": "float",
                "default": 15.0,
                "min": 5.0,
                "max": 50.0
            }
        }

    def should_sell(self, position: Dict, stock_info: Dict, additional_info: Dict = None) -> Dict:
        max_decline_rate = self.params.get("max_decline_rate", -5.0)
        volume_spike_threshold = self.params.get("volume_spike_threshold", 3.0)
        take_profit_rate = self.params.get("take_profit_rate", 15.0)

        profit_rate = position.get('profit_rate', 0.0)
        change_rate = stock_info.get('change_rate', 0.0)
        volume = stock_info.get('volume', 0)
        avg_volume = stock_info.get('avg_volume', volume)
        quantity = position.get('quantity', 0)

        volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0

        should_sell = False
        urgency = "low"
        reason = ""

        # 급락 + 거래량 급증
        if change_rate <= max_decline_rate and volume_ratio >= volume_spike_threshold:
            should_sell = True
            urgency = "high"
            reason = f"""
급락 감지:
- 일일 변동률: {change_rate:.2f}%
- 거래량 비율: {volume_ratio:.2f}배
- 판단: 급락 + 거래량 급증, 즉시 매도
"""

        # 익절
        elif profit_rate >= take_profit_rate:
            should_sell = True
            urgency = "medium"
            reason = f"""
익절 실행:
- 현재 수익률: {profit_rate:.2f}%
- 목표 수익률: {take_profit_rate}%
- 판단: 목표 달성, 매도
"""

        # 급락만 (거래량 정상)
        elif change_rate <= max_decline_rate:
            should_sell = True
            urgency = "medium"
            reason = f"""
하락 감지:
- 일일 변동률: {change_rate:.2f}%
- 판단: 급락 감지, 매도 검토
"""
        else:
            reason = f"""
보유 유지:
- 수익률: {profit_rate:.2f}%
- 일일 변동: {change_rate:.2f}%
- 거래량 비율: {volume_ratio:.2f}배
- 판단: 정상 범위 내
"""

        confidence = 0.9 if should_sell else 0.0

        return {
            "should_sell": should_sell,
            "confidence": confidence,
            "reason": reason,
            "recommended_quantity": quantity,
            "urgency": urgency
        }


# ==================== 전략 레지스트리 ====================

BUY_STRATEGIES = {
    "momentum": MomentumBuyStrategy,
    "value": ValueBuyStrategy,
    "breakout": BreakoutBuyStrategy,
}

SELL_STRATEGIES = {
    "fixed_ratio": FixedRatioSellStrategy,
    "trailing_stop": TrailingStopSellStrategy,
    "volatility": VolatilityBasedSellStrategy,
}


def get_buy_strategy(strategy_name: str, params: Dict = None) -> Optional[BuyStrategyBase]:
    """매수 전략 인스턴스 생성"""
    strategy_class = BUY_STRATEGIES.get(strategy_name)
    if strategy_class:
        return strategy_class(params)
    return None


def get_sell_strategy(strategy_name: str, params: Dict = None) -> Optional[SellStrategyBase]:
    """매도 전략 인스턴스 생성"""
    strategy_class = SELL_STRATEGIES.get(strategy_name)
    if strategy_class:
        return strategy_class(params)
    return None


def get_all_strategies_info() -> Dict:
    """모든 전략 정보 반환"""
    buy_strategies_info = {}
    for name, strategy_class in BUY_STRATEGIES.items():
        instance = strategy_class()
        buy_strategies_info[name] = {
            "name": name,
            "description": instance.get_description(),
            "parameters": instance.get_parameters()
        }

    sell_strategies_info = {}
    for name, strategy_class in SELL_STRATEGIES.items():
        instance = strategy_class()
        sell_strategies_info[name] = {
            "name": name,
            "description": instance.get_description(),
            "parameters": instance.get_parameters()
        }

    return {
        "buy_strategies": buy_strategies_info,
        "sell_strategies": sell_strategies_info
    }

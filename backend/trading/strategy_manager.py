"""
전략 관리 시스템
- 사용자가 선택한 전략과 파라미터를 관리
- 실시간 전략 전환 지원
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path
from backend.trading.strategies import (
    get_buy_strategy,
    get_sell_strategy,
    get_all_strategies_info,
    BuyStrategyBase,
    SellStrategyBase
)


class StrategyManager:
    """전략 관리자"""

    def __init__(self, config_file: str = "strategy_config.json"):
        self.config_file = Path(__file__).parent / config_file
        self.current_buy_strategy: Optional[BuyStrategyBase] = None
        self.current_sell_strategy: Optional[SellStrategyBase] = None
        self.config = self._load_config()
        self._apply_config()

    def _load_config(self) -> Dict:
        """설정 파일 로드"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"설정 파일 로드 실패: {e}")
                return self._get_default_config()
        else:
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """기본 설정 반환"""
        return {
            "buy_strategy": {
                "name": "momentum",
                "params": {
                    "min_change_rate": 3.0,
                    "min_volume_ratio": 1.5,
                    "max_position_size": 1000000
                },
                "allocation_basis": "total",
                "allocation_ratio": 30
            },
            "sell_strategy": {
                "name": "fixed_ratio",
                "params": {
                    "take_profit_rate": 10.0,
                    "stop_loss_rate": -5.0,
                    "partial_sell_ratio": 0.5
                }
            },
            "auto_trading_enabled": False,
            "notification_enabled": True
        }

    def _save_config(self):
        """설정 파일 저장"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"설정 파일 저장 실패: {e}")

    def _apply_config(self):
        """현재 설정 적용"""
        buy_config = self.config.get("buy_strategy", {})
        sell_config = self.config.get("sell_strategy", {})

        self.current_buy_strategy = get_buy_strategy(
            buy_config.get("name", "momentum"),
            buy_config.get("params", {})
        )

        self.current_sell_strategy = get_sell_strategy(
            sell_config.get("name", "fixed_ratio"),
            sell_config.get("params", {})
        )

    def set_buy_strategy(self, strategy_name: str, params: Dict = None, allocation_basis: str = None, allocation_ratio: int = None) -> bool:
        """매수 전략 설정"""
        strategy = get_buy_strategy(strategy_name, params)
        if strategy:
            self.current_buy_strategy = strategy
            self.config["buy_strategy"] = {
                "name": strategy_name,
                "params": params or {}
            }

            # Add allocation ratio information if provided
            if allocation_basis is not None:
                self.config["buy_strategy"]["allocation_basis"] = allocation_basis
            if allocation_ratio is not None:
                self.config["buy_strategy"]["allocation_ratio"] = allocation_ratio

            self._save_config()
            return True
        return False

    def set_sell_strategy(self, strategy_name: str, params: Dict = None) -> bool:
        """매도 전략 설정"""
        strategy = get_sell_strategy(strategy_name, params)
        if strategy:
            self.current_sell_strategy = strategy
            self.config["sell_strategy"] = {
                "name": strategy_name,
                "params": params or {}
            }
            self._save_config()
            return True
        return False

    def update_buy_params(self, params: Dict) -> bool:
        """매수 전략 파라미터 업데이트"""
        if self.current_buy_strategy:
            self.current_buy_strategy.params.update(params)
            self.config["buy_strategy"]["params"].update(params)
            self._save_config()
            return True
        return False

    def update_sell_params(self, params: Dict) -> bool:
        """매도 전략 파라미터 업데이트"""
        if self.current_sell_strategy:
            self.current_sell_strategy.params.update(params)
            self.config["sell_strategy"]["params"].update(params)
            self._save_config()
            return True
        return False

    def get_current_config(self) -> Dict:
        """현재 설정 반환"""
        buy_config = self.config.get("buy_strategy", {})
        return {
            "buy_strategy": buy_config,
            "sell_strategy": self.config.get("sell_strategy", {}),
            "auto_trading_enabled": self.config.get("auto_trading_enabled", False),
            "notification_enabled": self.config.get("notification_enabled", True),
            # Include allocation info for backward compatibility
            "allocation_basis": buy_config.get("allocation_basis", "total"),
            "allocation_ratio": buy_config.get("allocation_ratio", 30)
        }

    def get_allocation_info(self) -> Dict:
        """자동매매 비율 정보 반환"""
        buy_config = self.config.get("buy_strategy", {})
        return {
            "allocation_basis": buy_config.get("allocation_basis", "total"),
            "allocation_ratio": buy_config.get("allocation_ratio", 30)
        }

    def enable_auto_trading(self, enabled: bool):
        """자동 매매 활성화/비활성화"""
        self.config["auto_trading_enabled"] = enabled
        self._save_config()

    def is_auto_trading_enabled(self) -> bool:
        """자동 매매 활성화 여부"""
        return self.config.get("auto_trading_enabled", False)

    def analyze_buy(self, stock_info: Dict, balance_info: Dict, additional_info: Dict = None) -> Dict:
        """매수 분석 실행"""
        if not self.current_buy_strategy:
            return {
                "should_buy": False,
                "confidence": 0.0,
                "reason": "매수 전략이 설정되지 않았습니다.",
                "recommended_quantity": 0,
                "target_price": 0
            }

        return self.current_buy_strategy.should_buy(stock_info, balance_info, additional_info)

    def analyze_sell(self, position: Dict, stock_info: Dict, additional_info: Dict = None) -> Dict:
        """매도 분석 실행"""
        if not self.current_sell_strategy:
            return {
                "should_sell": False,
                "confidence": 0.0,
                "reason": "매도 전략이 설정되지 않았습니다.",
                "recommended_quantity": 0,
                "urgency": "low"
            }

        return self.current_sell_strategy.should_sell(position, stock_info, additional_info)

    def get_all_available_strategies(self) -> Dict:
        """사용 가능한 모든 전략 정보"""
        return get_all_strategies_info()

    def get_strategy_description(self, strategy_type: str, strategy_name: str) -> Optional[str]:
        """특정 전략 설명 조회"""
        all_info = get_all_strategies_info()
        if strategy_type == "buy":
            return all_info["buy_strategies"].get(strategy_name, {}).get("description")
        elif strategy_type == "sell":
            return all_info["sell_strategies"].get(strategy_name, {}).get("description")
        return None

    def reset_to_default(self):
        """기본 설정으로 리셋"""
        self.config = self._get_default_config()
        self._save_config()
        self._apply_config()


# 전역 인스턴스
_strategy_manager_instance = None


def get_strategy_manager() -> StrategyManager:
    """전략 관리자 싱글톤 인스턴스 반환"""
    global _strategy_manager_instance
    if _strategy_manager_instance is None:
        _strategy_manager_instance = StrategyManager()
    return _strategy_manager_instance

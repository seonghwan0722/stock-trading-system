import asyncio
from telegram import Bot
from telegram.error import TelegramError
from backend.config import Config


class TelegramNotifier:
    """텔레그램 알림 봇"""

    def __init__(self):
        self.token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.bot = None
        if self.token and self.chat_id:
            self.bot = Bot(token=self.token)

    async def send_message_async(self, message, parse_mode='Markdown'):
        """비동기 메시지 전송"""
        if not self.bot:
            print("텔레그램 봇이 설정되지 않았습니다.")
            return False

        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            return True
        except TelegramError as e:
            print(f"텔레그램 메시지 전송 실패: {e}")
            return False

    def send_message(self, message, parse_mode='Markdown'):
        """동기 메시지 전송 (내부적으로 비동기 호출)"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 이미 실행 중인 루프가 있으면 새 태스크 생성
                asyncio.create_task(self.send_message_async(message, parse_mode))
                return True
            else:
                # 루프가 없으면 새로 실행
                return loop.run_until_complete(self.send_message_async(message, parse_mode))
        except RuntimeError:
            # 새 이벤트 루프 생성
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.send_message_async(message, parse_mode))
            loop.close()
            return result

    def send_news_summary(self, summary):
        """뉴스 요약 전송"""
        message = f"📰 **경제 뉴스 요약**\n\n{summary}"
        return self.send_message(message)

    def send_trade_notification(self, trade_type, stock_code, stock_name, quantity, price, reason=""):
        """매매 알림 전송

        Args:
            trade_type: "BUY" 또는 "SELL"
            stock_code: 종목 코드
            stock_name: 종목 명
            quantity: 수량
            price: 가격
            reason: 매매 사유
        """
        emoji = "🔵" if trade_type == "BUY" else "🔴"
        action = "매수" if trade_type == "BUY" else "매도"

        message = f"""{emoji} **{action} 체결 알림**

📌 종목: {stock_name} ({stock_code})
💰 가격: {price:,}원
📊 수량: {quantity:,}주
💵 금액: {price * quantity:,}원

📝 사유:
{reason if reason else '자동 매매'}
"""
        return self.send_message(message)

    def send_position_summary(self, positions, total_profit_loss, total_profit_rate):
        """포트폴리오 요약 전송"""
        if not positions:
            message = "📊 **보유 종목 없음**"
            return self.send_message(message)

        position_lines = []
        for pos in positions:
            profit_emoji = "📈" if pos['profit_rate'] > 0 else "📉"
            position_lines.append(
                f"{profit_emoji} {pos['stock_name']}: "
                f"{pos['profit_rate']:.2f}% ({pos['profit_loss']:,}원)"
            )

        positions_text = "\n".join(position_lines)

        overall_emoji = "✅" if total_profit_rate > 0 else "⚠️"

        message = f"""📊 **포트폴리오 요약**

{positions_text}

{overall_emoji} **전체 손익**: {total_profit_rate:.2f}% ({total_profit_loss:,}원)
"""
        return self.send_message(message)

    def send_error_notification(self, error_message):
        """에러 알림 전송"""
        message = f"⚠️ **시스템 에러 발생**\n\n{error_message}"
        return self.send_message(message)

    def send_daily_report(self, summary_data):
        """일일 리포트 전송

        Args:
            summary_data: {
                "total_trades": int,
                "successful_trades": int,
                "total_profit_loss": int,
                "positions_count": int,
                "cash_balance": int
            }
        """
        message = f"""📊 **일일 거래 요약 리포트**

📈 총 거래 횟수: {summary_data.get('total_trades', 0)}회
✅ 성공한 거래: {summary_data.get('successful_trades', 0)}회
💰 총 손익: {summary_data.get('total_profit_loss', 0):,}원
📦 보유 종목 수: {summary_data.get('positions_count', 0)}개
💵 현금 잔고: {summary_data.get('cash_balance', 0):,}원
"""
        return self.send_message(message)

    def send_market_analysis(self, sentiment, score, news_count):
        """시장 분석 결과 전송"""
        sentiment_emoji = {
            "positive": "🟢",
            "neutral": "🟡",
            "negative": "🔴"
        }

        sentiment_text = {
            "positive": "긍정적",
            "neutral": "중립",
            "negative": "부정적"
        }

        emoji = sentiment_emoji.get(sentiment, "🟡")
        text = sentiment_text.get(sentiment, "중립")

        message = f"""📊 **시장 심리 분석**

{emoji} 현재 시장 심리: **{text}**
🎯 신뢰도: {score * 100:.1f}%
📰 분석 뉴스 수: {news_count}건
"""
        return self.send_message(message)

    def send_alert(self, title, content):
        """일반 알림 전송"""
        message = f"🔔 **{title}**\n\n{content}"
        return self.send_message(message)

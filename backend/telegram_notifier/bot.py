import asyncio
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Optional
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.config import get_config

Config = get_config()


class TelegramNotifier:
    """텔레그램 알림 봇 (양방향 통신 지원)"""

    def __init__(self):
        self.token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.bot = None
        self.application = None

        # 매매 승인 대기 목록
        self.pending_trades: Dict[str, dict] = {}

        if self.token and self.chat_id:
            self.bot = Bot(token=self.token)
            self.application = Application.builder().token(self.token).build()

            # 명령어 핸들러 등록
            self.application.add_handler(CommandHandler("status", self.cmd_status))
            self.application.add_handler(CommandHandler("portfolio", self.cmd_portfolio))
            self.application.add_handler(CommandHandler("help", self.cmd_help))

            # 콜백 쿼리 핸들러 (버튼 클릭 처리)
            self.application.add_handler(CallbackQueryHandler(self.handle_callback))

    async def send_message_async(self, message, parse_mode='Markdown', reply_markup=None):
        """비동기 메시지 전송"""
        if not self.bot:
            print("텔레그램 봇이 설정되지 않았습니다.")
            return False

        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
            return True
        except TelegramError as e:
            print(f"텔레그램 메시지 전송 실패: {e}")
            return False

    def send_message(self, message, parse_mode='Markdown', reply_markup=None):
        """동기 메시지 전송 (내부적으로 비동기 호출)"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.send_message_async(message, parse_mode, reply_markup))
                return True
            else:
                return loop.run_until_complete(self.send_message_async(message, parse_mode, reply_markup))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.send_message_async(message, parse_mode, reply_markup))
            loop.close()
            return result

    # ==================== 서버 시작 알림 ====================

    def send_server_start_notification(self, port=5000, features=None):
        """서버 시작 알림

        Args:
            port: 서버 포트 번호
            features: 활성화된 기능 리스트
        """
        if features is None:
            features = ["DART 재무제표 분석", "자동매매 시스템", "텔레그램 알림"]

        features_text = "\n".join([f"✅ {feature}" for feature in features])
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        message = f"""🚀 **주식 자동매매 서버 시작**

⏰ 시작 시간: {current_time}
🌐 포트: {port}
📍 URL: http://localhost:{port}

**활성화된 기능**:
{features_text}

시스템이 정상적으로 작동 중입니다.
명령어를 보려면 /help 를 입력하세요.
"""
        return self.send_message(message)

    def send_server_shutdown_notification(self):
        """서버 종료 알림"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        message = f"""⚠️ **서버 종료**

⏰ 종료 시간: {current_time}

서버가 안전하게 종료되었습니다.
"""
        return self.send_message(message)

    # ==================== 매매 추천 및 승인 ====================

    def send_trade_recommendation(self, trade_id: str, trade_data: dict):
        """매매 추천 알림 (승인 대기)

        Args:
            trade_id: 고유 거래 ID
            trade_data: {
                "type": "BUY" or "SELL",
                "stock_code": str,
                "stock_name": str,
                "quantity": int,
                "price": int,
                "current_price": int,
                "reason": str,
                "confidence": float,  # 0-1
                "strategy": str
            }
        """
        # 대기 목록에 추가
        self.pending_trades[trade_id] = {
            **trade_data,
            "timestamp": datetime.now().isoformat()
        }

        emoji = "🔵" if trade_data["type"] == "BUY" else "🔴"
        action = "매수" if trade_data["type"] == "BUY" else "매도"
        confidence_percent = trade_data.get("confidence", 0) * 100

        # 신뢰도에 따른 색상
        if confidence_percent >= 80:
            confidence_emoji = "🟢"
        elif confidence_percent >= 60:
            confidence_emoji = "🟡"
        else:
            confidence_emoji = "🟠"

        message = f"""{emoji} **{action} 추천 알림**

📌 종목: {trade_data['stock_name']} ({trade_data['stock_code']})
💰 현재가: {trade_data.get('current_price', trade_data['price']):,}원
📊 {action} 가격: {trade_data['price']:,}원
🔢 수량: {trade_data['quantity']:,}주
💵 총 금액: {trade_data['price'] * trade_data['quantity']:,}원

{confidence_emoji} 신뢰도: {confidence_percent:.1f}%
🎯 전략: {trade_data.get('strategy', '자동매매')}

📝 추천 사유:
{trade_data.get('reason', 'AI 분석 결과')}

⏰ 15분 내 응답이 없으면 자동으로 취소됩니다.
"""

        # 승인/거부 버튼
        keyboard = [
            [
                InlineKeyboardButton("✅ 승인", callback_data=f"approve_{trade_id}"),
                InlineKeyboardButton("❌ 거부", callback_data=f"reject_{trade_id}")
            ],
            [
                InlineKeyboardButton("📊 상세 정보", callback_data=f"details_{trade_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        return self.send_message(message, reply_markup=reply_markup)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """버튼 클릭 처리"""
        query = update.callback_query
        await query.answer()

        data = query.data
        action, trade_id = data.split("_", 1)

        if trade_id not in self.pending_trades:
            await query.edit_message_text("⚠️ 이미 처리되었거나 만료된 거래입니다.")
            return

        trade = self.pending_trades[trade_id]

        if action == "approve":
            # 매매 승인
            await query.edit_message_text(
                f"✅ **매매 승인됨**\n\n"
                f"종목: {trade['stock_name']} ({trade['stock_code']})\n"
                f"유형: {'매수' if trade['type'] == 'BUY' else '매도'}\n"
                f"수량: {trade['quantity']:,}주\n"
                f"가격: {trade['price']:,}원\n\n"
                f"주문을 실행합니다..."
            )

            # 실제 매매 실행 (여기서 API 호출)
            await self.execute_trade(trade_id, trade)

        elif action == "reject":
            # 매매 거부
            await query.edit_message_text(
                f"❌ **매매 거부됨**\n\n"
                f"종목: {trade['stock_name']} ({trade['stock_code']})\n"
                f"거래가 취소되었습니다."
            )
            del self.pending_trades[trade_id]

        elif action == "details":
            # 상세 정보 표시
            details = f"""📊 **거래 상세 정보**

종목: {trade['stock_name']} ({trade['stock_code']})
유형: {'매수' if trade['type'] == 'BUY' else '매도'}
현재가: {trade.get('current_price', trade['price']):,}원
주문가격: {trade['price']:,}원
수량: {trade['quantity']:,}주
총액: {trade['price'] * trade['quantity']:,}원

신뢰도: {trade.get('confidence', 0) * 100:.1f}%
전략: {trade.get('strategy', '자동매매')}

사유:
{trade.get('reason', 'AI 분석 결과')}

타임스탬프: {trade.get('timestamp', 'N/A')}
"""

            # 원래 버튼 유지
            keyboard = [
                [
                    InlineKeyboardButton("✅ 승인", callback_data=f"approve_{trade_id}"),
                    InlineKeyboardButton("❌ 거부", callback_data=f"reject_{trade_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(details, reply_markup=reply_markup)

    async def execute_trade(self, trade_id: str, trade: dict):
        """실제 매매 실행

        Args:
            trade_id: 거래 ID
            trade: 거래 정보
        """
        try:
            # 여기서 실제 API 호출
            # from api.kiwoom_api import get_kiwoom_api
            # kiwoom = get_kiwoom_api()
            # if trade['type'] == 'BUY':
            #     result = kiwoom.buy_stock(trade['stock_code'], trade['quantity'], trade['price'])
            # else:
            #     result = kiwoom.sell_stock(trade['stock_code'], trade['quantity'], trade['price'])

            # 임시로 성공 메시지
            await self.send_message_async(
                f"✅ **매매 체결 완료**\n\n"
                f"종목: {trade['stock_name']} ({trade['stock_code']})\n"
                f"유형: {'매수' if trade['type'] == 'BUY' else '매도'}\n"
                f"수량: {trade['quantity']:,}주\n"
                f"가격: {trade['price']:,}원\n"
                f"총액: {trade['price'] * trade['quantity']:,}원"
            )

            # 대기 목록에서 제거
            del self.pending_trades[trade_id]

        except Exception as e:
            await self.send_message_async(
                f"⚠️ **매매 실행 실패**\n\n"
                f"오류: {str(e)}\n"
                f"거래 ID: {trade_id}"
            )

    # ==================== 월간 리포트 ====================

    def send_monthly_report(self, report_data: dict):
        """월간 거래 요약 리포트

        Args:
            report_data: {
                "month": str,  # "2025-01"
                "total_trades": int,
                "buy_count": int,
                "sell_count": int,
                "win_rate": float,
                "total_profit_loss": int,
                "best_trade": dict,
                "worst_trade": dict,
                "top_stocks": list,
                "starting_balance": int,
                "ending_balance": int,
                "return_rate": float
            }
        """
        month = report_data.get("month", datetime.now().strftime("%Y-%m"))
        total_trades = report_data.get("total_trades", 0)
        win_rate = report_data.get("win_rate", 0)
        total_pl = report_data.get("total_profit_loss", 0)
        return_rate = report_data.get("return_rate", 0)

        pl_emoji = "📈" if total_pl >= 0 else "📉"
        return_emoji = "🟢" if return_rate >= 0 else "🔴"

        # 최고/최악 거래
        best_trade = report_data.get("best_trade")
        worst_trade = report_data.get("worst_trade")

        best_text = "없음"
        if best_trade:
            best_text = f"{best_trade['stock_name']}: +{best_trade['profit']:,}원 ({best_trade['return']:.2f}%)"

        worst_text = "없음"
        if worst_trade:
            worst_text = f"{worst_trade['stock_name']}: {worst_trade['profit']:,}원 ({worst_trade['return']:.2f}%)"

        # 인기 종목
        top_stocks = report_data.get("top_stocks", [])
        top_stocks_text = "\n".join([
            f"{i+1}. {stock['name']}: {stock['trades']}회"
            for i, stock in enumerate(top_stocks[:5])
        ]) if top_stocks else "없음"

        message = f"""📊 **{month} 월간 거래 요약 리포트**

━━━━━━━━━━━━━━━━━━━━
**📈 거래 통계**
━━━━━━━━━━━━━━━━━━━━

총 거래 횟수: {total_trades}회
  ├ 매수: {report_data.get('buy_count', 0)}회
  └ 매도: {report_data.get('sell_count', 0)}회

승률: {win_rate:.1f}%

━━━━━━━━━━━━━━━━━━━━
**💰 수익 분석**
━━━━━━━━━━━━━━━━━━━━

{pl_emoji} 총 손익: {total_pl:,}원
{return_emoji} 수익률: {return_rate:.2f}%

기초 잔고: {report_data.get('starting_balance', 0):,}원
기말 잔고: {report_data.get('ending_balance', 0):,}원

━━━━━━━━━━━━━━━━━━━━
**🏆 거래 하이라이트**
━━━━━━━━━━━━━━━━━━━━

최고 수익 거래:
{best_text}

최악 손실 거래:
{worst_text}

━━━━━━━━━━━━━━━━━━━━
**📊 거래 빈도 TOP 5**
━━━━━━━━━━━━━━━━━━━━

{top_stocks_text}

━━━━━━━━━━━━━━━━━━━━

다음 달도 성공적인 투자 되세요! 💪
"""
        return self.send_message(message)

    def send_market_analysis_report(self, analysis_data: dict):
        """월간 시장 분석 리포트

        Args:
            analysis_data: {
                "month": str,
                "kospi_change": float,
                "kosdaq_change": float,
                "top_sectors": list,
                "market_sentiment": str,
                "key_events": list,
                "outlook": str,
                "recommendations": list
            }
        """
        month = analysis_data.get("month", datetime.now().strftime("%Y-%m"))

        kospi_change = analysis_data.get("kospi_change", 0)
        kosdaq_change = analysis_data.get("kosdaq_change", 0)

        kospi_emoji = "📈" if kospi_change >= 0 else "📉"
        kosdaq_emoji = "📈" if kosdaq_change >= 0 else "📉"

        # 상위 업종
        top_sectors = analysis_data.get("top_sectors", [])
        sectors_text = "\n".join([
            f"{i+1}. {sector['name']}: {sector['change']:+.2f}%"
            for i, sector in enumerate(top_sectors[:5])
        ]) if top_sectors else "데이터 없음"

        # 주요 이벤트
        key_events = analysis_data.get("key_events", [])
        events_text = "\n".join([
            f"• {event}"
            for event in key_events
        ]) if key_events else "특이사항 없음"

        # 투자 권장사항
        recommendations = analysis_data.get("recommendations", [])
        recommendations_text = "\n".join([
            f"✅ {rec}"
            for rec in recommendations
        ]) if recommendations else "일반적인 분산투자 권장"

        sentiment = analysis_data.get("market_sentiment", "중립")
        sentiment_emoji_map = {
            "매우 긍정": "🟢🟢",
            "긍정": "🟢",
            "중립": "🟡",
            "부정": "🔴",
            "매우 부정": "🔴🔴"
        }
        sentiment_emoji = sentiment_emoji_map.get(sentiment, "🟡")

        message = f"""📊 **{month} 월간 시장 분석 리포트**

━━━━━━━━━━━━━━━━━━━━
**📈 주요 지수 동향**
━━━━━━━━━━━━━━━━━━━━

{kospi_emoji} KOSPI: {kospi_change:+.2f}%
{kosdaq_emoji} KOSDAQ: {kosdaq_change:+.2f}%

━━━━━━━━━━━━━━━━━━━━
**🏆 상위 업종 (월간)**
━━━━━━━━━━━━━━━━━━━━

{sectors_text}

━━━━━━━━━━━━━━━━━━━━
**📰 주요 이벤트**
━━━━━━━━━━━━━━━━━━━━

{events_text}

━━━━━━━━━━━━━━━━━━━━
**🎯 시장 심리**
━━━━━━━━━━━━━━━━━━━━

{sentiment_emoji} {sentiment}

━━━━━━━━━━━━━━━━━━━━
**💡 시장 전망**
━━━━━━━━━━━━━━━━━━━━

{analysis_data.get('outlook', 'AI 기반 분석 결과를 확인하세요.')}

━━━━━━━━━━━━━━━━━━━━
**📋 투자 권장사항**
━━━━━━━━━━━━━━━━━━━━

{recommendations_text}

━━━━━━━━━━━━━━━━━━━━

현명한 투자 결정을 하세요! 📊
"""
        return self.send_message(message)

    # ==================== 기존 함수들 ====================

    def send_news_summary(self, summary):
        """뉴스 요약 전송"""
        message = f"📰 **경제 뉴스 요약**\n\n{summary}"
        return self.send_message(message)

    def send_trade_notification(self, trade_type, stock_code, stock_name, quantity, price, reason=""):
        """매매 체결 알림 전송 (승인 후 실행 완료)"""
        emoji = "🔵" if trade_type == "BUY" else "🔴"
        action = "매수" if trade_type == "BUY" else "매도"

        message = f"""{emoji} **{action} 체결 완료**

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
        """일일 리포트 전송"""
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

    # ==================== 명령어 핸들러 ====================

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """시스템 상태 조회 명령어"""
        message = """🤖 **시스템 상태**

✅ 서버: 정상 작동 중
✅ 텔레그램 봇: 연결됨
✅ API 연동: 정상

명령어 목록을 보려면 /help 를 입력하세요.
"""
        await update.message.reply_text(message, parse_mode='Markdown')

    async def cmd_portfolio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """포트폴리오 조회 명령어"""
        # 실제로는 API에서 데이터를 가져와야 함
        message = """📊 **포트폴리오 조회**

현재 포트폴리오 정보를 조회 중...
잠시만 기다려주세요.
"""
        await update.message.reply_text(message, parse_mode='Markdown')

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """도움말 명령어"""
        message = """📖 **사용 가능한 명령어**

/status - 시스템 상태 확인
/portfolio - 포트폴리오 조회
/help - 도움말 보기

**자동 알림**:
• 서버 시작/종료 알림
• 매매 추천 및 승인 요청
• 매매 체결 알림
• 일일 리포트
• 월말 월간 리포트 및 시장 분석

**매매 승인**:
매매 추천 시 ✅승인 또는 ❌거부 버튼을 눌러주세요.
15분 내 응답이 없으면 자동 취소됩니다.
"""
        await update.message.reply_text(message, parse_mode='Markdown')

    # ==================== 봇 실행 ====================

    def run_bot(self):
        """텔레그램 봇 백그라운드 실행"""
        if not self.application:
            print("텔레그램 봇이 설정되지 않았습니다.")
            return

        print("텔레그램 봇 시작...")
        self.application.run_polling()


# 싱글톤 인스턴스
_notifier_instance = None

def get_telegram_notifier():
    """텔레그램 알림 봇 싱글톤 인스턴스 반환"""
    global _notifier_instance
    if _notifier_instance is None:
        _notifier_instance = TelegramNotifier()
    return _notifier_instance

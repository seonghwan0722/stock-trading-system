import requests
from bs4 import BeautifulSoup
import anthropic
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.config import get_config

Config = get_config()


class NewsSummarizer:
    """경제 뉴스 크롤링 및 AI 요약"""

    def __init__(self):
        # Anthropic API는 선택사항 - 없으면 요약 기능 비활성화
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY) if hasattr(Config, 'ANTHROPIC_API_KEY') and Config.ANTHROPIC_API_KEY else None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def crawl_naver_finance_news(self, limit=10):
        """네이버 금융 뉴스 크롤링"""
        url = "https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258"
        news_list = []

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # 뉴스 목록 추출
            news_items = soup.select('.newsList .articleSubject a')

            for item in news_items[:limit]:
                title = item.get('title', item.text.strip())
                link = "https://finance.naver.com" + item.get('href', '')

                news_list.append({
                    'title': title,
                    'link': link,
                    'source': '네이버 금융'
                })

        except Exception as e:
            print(f"네이버 금융 뉴스 크롤링 오류: {e}")

        return news_list

    def crawl_hankyung_news(self, limit=10):
        """한국경제 뉴스 크롤링"""
        url = "https://www.hankyung.com/economy"
        news_list = []

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # 뉴스 목록 추출
            news_items = soup.select('.news-list li a')

            for item in news_items[:limit]:
                title = item.get('title', item.text.strip())
                link = item.get('href', '')
                if link and not link.startswith('http'):
                    link = "https://www.hankyung.com" + link

                if title and link:
                    news_list.append({
                        'title': title,
                        'link': link,
                        'source': '한국경제'
                    })

        except Exception as e:
            print(f"한국경제 뉴스 크롤링 오류: {e}")

        return news_list

    def crawl_mk_news(self, limit=10):
        """매일경제 뉴스 크롤링"""
        url = "https://www.mk.co.kr/news/stock/"
        news_list = []

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # 뉴스 목록 추출
            news_items = soup.select('.news_node .news_ttl a')

            for item in news_items[:limit]:
                title = item.text.strip()
                link = item.get('href', '')

                if title and link:
                    news_list.append({
                        'title': title,
                        'link': link,
                        'source': '매일경제'
                    })

        except Exception as e:
            print(f"매일경제 뉴스 크롤링 오류: {e}")

        return news_list

    def gather_all_news(self):
        """모든 소스에서 뉴스 수집"""
        all_news = []

        # 여러 소스에서 뉴스 크롤링
        all_news.extend(self.crawl_naver_finance_news(limit=5))
        all_news.extend(self.crawl_hankyung_news(limit=5))
        all_news.extend(self.crawl_mk_news(limit=5))

        return all_news

    def summarize_news_with_ai(self, news_list):
        """AI를 사용해 뉴스 요약"""
        if not news_list:
            return "수집된 뉴스가 없습니다."

        # 뉴스 제목 목록 생성
        news_titles = "\n".join([
            f"{i+1}. [{news['source']}] {news['title']}"
            for i, news in enumerate(news_list)
        ])

        prompt = f"""다음은 최신 한국 경제/증시 뉴스 헤드라인입니다. 이를 분석하여 핵심 내용을 요약해주세요.

## 뉴스 헤드라인
{news_titles}

## 요청사항
다음 형식으로 요약해주세요:

**📊 주요 시장 동향**
- [핵심 포인트 1]
- [핵심 포인트 2]

**🔥 주목할 이슈**
- [주목할 이슈 1]
- [주목할 이슈 2]

**💡 투자 시사점**
- [시사점 1]
- [시사점 2]

**⚠️ 리스크 요인**
- [리스크 요인]

간결하고 명확하게 핵심만 전달해주세요. 각 섹션당 2-3개의 bullet point로 제한합니다.
"""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            summary = message.content[0].text

            # 날짜 정보 추가
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            full_summary = f"📰 **경제 뉴스 요약** ({current_time})\n\n{summary}"

            return full_summary

        except Exception as e:
            print(f"AI 요약 오류: {e}")
            return f"뉴스 요약 중 오류 발생: {str(e)}"

    def get_market_sentiment(self, news_list):
        """뉴스 기반 시장 심리 분석"""
        if not news_list:
            return {"sentiment": "neutral", "score": 0.5}

        news_titles = "\n".join([news['title'] for news in news_list])

        prompt = f"""다음 뉴스 헤드라인들을 분석하여 현재 한국 주식 시장의 전반적인 심리를 평가해주세요.

뉴스 헤드라인:
{news_titles}

다음 형식으로 답변해주세요:
**시장 심리**: POSITIVE, NEUTRAL, NEGATIVE 중 하나
**신뢰도 점수**: 0.0 ~ 1.0 (1.0이 가장 확실함)
**근거**: 간단한 설명
"""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response = message.content[0].text

            # 간단한 파싱
            sentiment = "neutral"
            if "POSITIVE" in response.upper():
                sentiment = "positive"
            elif "NEGATIVE" in response.upper():
                sentiment = "negative"

            score = 0.5
            if "신뢰도" in response or "점수" in response:
                try:
                    for line in response.split("\n"):
                        if "점수" in line or "신뢰도" in line:
                            score_str = line.split(":")[-1].strip()
                            score = float(score_str.replace("%", "").strip())
                            if score > 1.0:
                                score = score / 100.0
                            break
                except:
                    pass

            return {
                "sentiment": sentiment,
                "score": score,
                "analysis": response
            }

        except Exception as e:
            print(f"시장 심리 분석 오류: {e}")
            return {"sentiment": "neutral", "score": 0.5, "analysis": str(e)}

# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
DART 종목 코드 수집기
DART API에서 전체 상장 종목을 다운로드하여 DB에 저장
"""

import os
import sys
import requests
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict
import logging
from dotenv import load_dotenv

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))  # project_root 추가

# .env 파일 로드
load_dotenv(project_root / '.env')

from backend.database.mongo_db import get_database
from backend.config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DARTCompanyCollector:
    """DART 상장 종목 수집 클래스 - MongoDB 버전"""

    CORP_CODE_URL = "https://opendart.fss.or.kr/api/corpCode.xml"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.db = get_database()
        self.dart_companies = self.db.dart_companies if self.db else None

    def download_corp_codes(self, output_path: str = "data/corpcode.zip") -> str:
        logger.info("Downloading corporate codes from DART...")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        response = requests.get(
            self.CORP_CODE_URL,
            params={'crtfc_key': self.api_key},
            timeout=30
        )
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            f.write(response.content)

        logger.info(f"Downloaded to {output_path}")
        return output_path

    def extract_xml(self, zip_path: str, extract_path: str = "data/CORPCODE.xml") -> str:
        logger.info("Extracting XML from ZIP...")

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(Path(extract_path).parent)

        logger.info(f"Extracted to {extract_path}")
        return extract_path

    def parse_xml(self, xml_path: str) -> List[Dict]:
        logger.info("Parsing XML...")

        tree = ET.parse(xml_path)
        root = tree.getroot()

        companies = []
        for company in root.findall('list'):
            corp_code = company.find('corp_code').text
            corp_name = company.find('corp_name').text
            stock_code = company.find('stock_code').text
            modify_date = company.find('modify_date').text

            if not stock_code or stock_code.strip() == '':
                continue

            # 숫자만 포함된 유효한 stock_code인지 확인
            if not stock_code.isdigit():
                logger.debug(f"Skipping non-numeric stock code: {stock_code} for {corp_name}")
                continue

            stock_code_int = int(stock_code)
            if stock_code_int < 100000:
                market_type = 'KOSPI'
            elif stock_code_int < 400000:
                market_type = 'KOSDAQ'
            else:
                market_type = 'KONEX'

            companies.append({
                'corp_code': corp_code,
                'corp_name': corp_name,
                'stock_code': stock_code,
                'modify_date': modify_date,
                'market_type': market_type
            })

        logger.info(f"Parsed {len(companies)} companies with stock codes")
        return companies

    def save_to_database(self, companies: List[Dict]) -> int:
        """MongoDB에 종목 데이터 저장"""
        if not self.dart_companies:
            logger.error("MongoDB connection not available")
            return 0

        logger.info("Saving to MongoDB...")

        # Clear existing data
        self.dart_companies.delete_many({})

        # Prepare documents
        stocks = []
        for company in companies:
            stocks.append({
                'stock_code': company['stock_code'],
                'corp_code': company['corp_code'],
                'name': company['corp_name'],
                'name_en': None,
                'market_type': company['market_type'],
                'modify_date': company['modify_date']
            })

        # Bulk insert
        if stocks:
            result = self.dart_companies.insert_many(stocks)
            count = len(result.inserted_ids)
            logger.info(f"✅ Saved {count} stocks to MongoDB")
            return count

        return 0

    def run(self) -> int:
        try:
            zip_path = self.download_corp_codes()
            xml_path = self.extract_xml(zip_path)
            companies = self.parse_xml(xml_path)
            count = self.save_to_database(companies)

            logger.info("Cleaning up temporary files...")
            Path(zip_path).unlink(missing_ok=True)
            Path(xml_path).unlink(missing_ok=True)

            logger.info(f"Successfully collected {count} companies")
            return count

        except Exception as e:
            logger.error(f"Collection failed: {e}")
            raise

        finally:
            self.db.close()


def main():
    api_key = os.getenv('DART_API_KEY')

    if not api_key:
        logger.error("DART_API_KEY environment variable not set")
        sys.exit(1)

    collector = DARTCompanyCollector(api_key=api_key)

    try:
        count = collector.run()
        print(f"\nSuccessfully collected {count} companies\n")

    except Exception as e:
        logger.error(f"Failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

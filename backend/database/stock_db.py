"""
Stock Database Manager
국내 상장 종목 정보를 관리하는 데이터베이스 모듈
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import re


class StockDatabase:
    """
    국내 상장 종목 DB 관리 클래스

    Features:
    - SQLite 기반 경량 데이터베이스
    - 종목 코드, 이름, 시장 구분 저장
    - 초성 검색 지원
    - 자동 업데이트 기능
    """

    def __init__(self, db_path: str = "data/stocks.db"):
        """
        Initialize database

        Args:
            db_path: SQLite database file path
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = None
        self.cursor = None
        self._connect()
        self._initialize_tables()

    def _connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def _initialize_tables(self):
        """Create tables if they don't exist"""
        # 종목 정보 테이블
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT UNIQUE NOT NULL,
                corp_code TEXT NOT NULL,
                company_name TEXT NOT NULL,
                company_name_en TEXT,
                market_type TEXT NOT NULL,
                sector TEXT,
                listed_date DATE,
                listed_shares BIGINT,
                modify_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 검색 최적화를 위한 인덱스
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_stock_code
            ON stocks(stock_code)
        ''')

        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_corp_code
            ON stocks(corp_code)
        ''')

        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_company_name
            ON stocks(company_name)
        ''')

        # 메타데이터 테이블 (DB 업데이트 정보)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.commit()

    def bulk_insert_stocks(self, stocks: List[Dict]) -> int:
        """
        Bulk insert stock data

        Args:
            stocks: List of stock dictionaries with keys:
                   stock_code, corp_code, company_name, market_type, etc.

        Returns:
            Number of inserted records
        """
        inserted = 0

        for stock in stocks:
            try:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO stocks
                    (stock_code, corp_code, company_name, company_name_en,
                     market_type, sector, listed_date, modify_date, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    stock.get('stock_code'),
                    stock.get('corp_code'),
                    stock.get('company_name'),
                    stock.get('company_name_en'),
                    stock.get('market_type', '유가증권'),
                    stock.get('sector'),
                    stock.get('listed_date'),
                    stock.get('modify_date')
                ))
                inserted += 1
            except Exception as e:
                print(f"Error inserting stock {stock.get('company_name', 'Unknown')}: {e}")

        self.conn.commit()

        # Update metadata
        self._update_metadata('last_update', datetime.now().isoformat())
        self._update_metadata('total_stocks', str(inserted))

        return inserted

    def search_stocks(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search stocks by name or code

        Args:
            query: Search query (name, code, or chosung)
            limit: Maximum results

        Returns:
            List of matching stocks
        """
        if not query or len(query) < 2:
            return []

        # 종목 코드 검색 (정확히 일치)
        if query.isdigit():
            self.cursor.execute('''
                SELECT * FROM stocks
                WHERE stock_code LIKE ?
                LIMIT ?
            ''', (f'%{query}%', limit))
            results = [dict(row) for row in self.cursor.fetchall()]
            if results:
                return results

        # 회사명 검색 (부분 일치)
        self.cursor.execute('''
            SELECT * FROM stocks
            WHERE company_name LIKE ? OR company_name_en LIKE ?
            ORDER BY
                CASE
                    WHEN company_name = ? THEN 1
                    WHEN company_name LIKE ? THEN 2
                    ELSE 3
                END
            LIMIT ?
        ''', (f'%{query}%', f'%{query}%', query, f'{query}%', limit))

        return [dict(row) for row in self.cursor.fetchall()]

    def get_stock_by_code(self, stock_code: str) -> Optional[Dict]:
        """
        Get stock by stock code

        Args:
            stock_code: 6-digit stock code

        Returns:
            Stock dictionary or None
        """
        self.cursor.execute('''
            SELECT * FROM stocks WHERE stock_code = ?
        ''', (stock_code,))

        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_stock_by_corp_code(self, corp_code: str) -> Optional[Dict]:
        """
        Get stock by DART corporate code

        Args:
            corp_code: 8-digit DART corp_code

        Returns:
            Stock dictionary or None
        """
        self.cursor.execute('''
            SELECT * FROM stocks WHERE corp_code = ?
        ''', (corp_code,))

        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_all_stocks(self, market_type: Optional[str] = None) -> List[Dict]:
        """
        Get all stocks

        Args:
            market_type: Filter by market (KOSPI, KOSDAQ, KONEX)

        Returns:
            List of all stocks
        """
        if market_type:
            self.cursor.execute('''
                SELECT * FROM stocks
                WHERE market_type = ?
                ORDER BY company_name
            ''', (market_type,))
        else:
            self.cursor.execute('''
                SELECT * FROM stocks
                ORDER BY company_name
            ''')

        return [dict(row) for row in self.cursor.fetchall()]

    def get_stock_count(self, market_type: Optional[str] = None) -> int:
        """
        Get total stock count

        Args:
            market_type: Filter by market

        Returns:
            Stock count
        """
        if market_type:
            self.cursor.execute('''
                SELECT COUNT(*) FROM stocks WHERE market_type = ?
            ''', (market_type,))
        else:
            self.cursor.execute('SELECT COUNT(*) FROM stocks')

        return self.cursor.fetchone()[0]

    def get_market_stats(self) -> Dict[str, int]:
        """
        Get statistics by market type

        Returns:
            Dictionary with market stats
        """
        self.cursor.execute('''
            SELECT market_type, COUNT(*) as count
            FROM stocks
            GROUP BY market_type
        ''')

        stats = {}
        for row in self.cursor.fetchall():
            stats[row['market_type']] = row['count']

        return stats

    def _update_metadata(self, key: str, value: str):
        """Update metadata"""
        self.cursor.execute('''
            INSERT OR REPLACE INTO metadata (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, value))
        self.conn.commit()

    def get_metadata(self, key: str) -> Optional[str]:
        """Get metadata value"""
        self.cursor.execute('''
            SELECT value FROM metadata WHERE key = ?
        ''', (key,))

        row = self.cursor.fetchone()
        return row['value'] if row else None

    def get_last_update(self) -> Optional[str]:
        """Get last database update timestamp"""
        return self.get_metadata('last_update')

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Example usage
if __name__ == '__main__':
    db = StockDatabase()

    # Sample data
    sample_stocks = [
        {
            'stock_code': '005930',
            'corp_code': '00126380',
            'company_name': '삼성전자',
            'company_name_en': 'Samsung Electronics',
            'market_type': 'KOSPI',
            'sector': '전기전자'
        },
        {
            'stock_code': '000660',
            'corp_code': '00164779',
            'company_name': 'SK하이닉스',
            'company_name_en': 'SK Hynix',
            'market_type': 'KOSPI',
            'sector': '반도체'
        }
    ]

    # Insert
    count = db.bulk_insert_stocks(sample_stocks)
    print(f"Inserted {count} stocks")

    # Search
    results = db.search_stocks('삼성')
    print(f"\nSearch results for '삼성':")
    for stock in results:
        print(f"  {stock['company_name']} ({stock['stock_code']})")

    # Stats
    stats = db.get_market_stats()
    print(f"\nMarket stats: {stats}")

    db.close()

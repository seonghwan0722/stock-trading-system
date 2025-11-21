# Korean Stock Market Data & Search Implementation Research

## Executive Summary

This document provides a comprehensive research guide for obtaining complete Korean stock market data and implementing search functionality with autocomplete support, including Korean language features.

**Key Findings:**
- DART API (`/api/corpCode.xml`) is the most authoritative source for company registry
- PyKRX library provides practical data collection from KRX
- Hybrid approach (server-side database + client-side fuzzy search) recommended for 3000+ companies
- Sub-100ms response time requires in-memory caching or database indexing
- Korean language support requires initial consonant (초성) search libraries

---

## 1. Data Sources for Korean Stocks

### 1.1 Official Sources (Recommended)

#### DART API (Data Analysis, Retrieval and Transfer System)
**Source:** Korea Financial Supervisory Service (FSS)
- **Website:** https://opendart.fss.or.kr/ (Korean) | https://englishdart.fss.or.kr/ (English)
- **Type:** Official government-backed disclosure system
- **Completeness:** Most complete - includes ALL listed companies + unlisted audited companies
- **Registration Required:** Yes (Free API key available)

**Key Endpoint:**
```
GET /api/corpCode.xml?crtfc_key={API_KEY}
```

**Data Structure (XML):**
```xml
<result>
  <list>
    <corp_code>00126380</corp_code>
    <corp_name>삼성전자</corp_name>
    <stock_code>005930</stock_code>
    <ceo_nm>한종희,이준호</ceo_nm>
    <corp_cls>Y</corp_cls>
    <modify_date>20231215</modify_date>
  </list>
  ...
</result>
```

**Update Frequency:**
- Near real-time for new company registrations
- Suggests updating local cache daily or weekly
- New listings/delistings reflected within 24-48 hours

#### KRX (Korea Exchange / 한국거래소)
**Source:** Official Korea Exchange
- **Website:** https://data.krx.co.kr/
- **Type:** Official exchange-operated data portal
- **Markets Covered:** KOSPI, KOSDAQ, KONEX
- **Data Available:** Real-time trading data, market data, investor information

**Advantages:**
- Real-time market data
- Official exchange source
- Regulated data quality

**Disadvantages:**
- Requires registration and sometimes authentication
- May have usage restrictions for commercial purposes
- Less focused on company registry completeness

### 1.2 Python Library Sources

#### PyKRX (Recommended for Python Projects)
**Library:** https://github.com/sharebook-kr/pykrx
```bash
pip install pykrx
```

**Capabilities:**
- Scrapes KRX and Naver Finance data
- OHLCV (Open, High, Low, Close, Volume) data
- Fundamental data (PER, PBR, EPS, BPS)
- Market-wide aggregates
- Historical data by date range

**Usage:**
```python
from pykrx import stock

# Get all KOSPI tickers for a date
tickers = stock.get_market_ticker_list("20231215", market="KOSPI")

# Get OHLCV data
df = stock.get_market_ohlcv("20231201", "20231215", "005930")

# Get fundamental data
df = stock.get_market_fundamental_by_ticker("20231215")
```

#### FinanceDataReader
**Library:** https://github.com/FinanceData/FinanceDataReader
```bash
pip install FinanceDataReader
```

**Advantages:**
- Supports multiple markets (Korea, USA, etc.)
- High-level API for common operations
- Built-in pandas DataFrame integration

### 1.3 Web Scraping Sources (Not Recommended)

#### Naver Finance
**Considerations:**
- **Legal Status:** Terms of Service prohibit automated scraping
- **Anti-Bot Protection:** Sophisticated IP-based rate limiting, browser fingerprinting
- **Blocked Frequently:** IPs can be blocked after excessive requests
- **Rate Limiting:** No official API, requires careful rate limiting

**If scraping is necessary:**
```python
# Implement exponential backoff
# Add random delays between requests (2-5 seconds minimum)
# Rotate proxies or use residential proxies
# Respect robots.txt
# Add proper User-Agent headers

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Example with rate limiting
import time
import random

for ticker in tickers:
    response = requests.get(url, headers=headers)
    delay = random.uniform(2, 5)  # 2-5 second random delay
    time.sleep(delay)
```

**Recommendation:** Use PyKRX instead, which handles Naver scraping internally with proper rate limiting

---

## 2. DART API Implementation Guide

### 2.1 Getting Started

**Step 1: Register for API Key**
1. Visit https://opendart.fss.or.kr/ or https://englishdart.fss.or.kr/
2. Register account (free)
3. Request API key (immediate approval)

**Step 2: Download Company Code List**

```python
import requests
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime
import time

class DARTClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://opendart.fss.or.kr/api"
        self.corp_code_cache = None
        self.last_update = None

    def get_corp_code_list(self, force_refresh=False):
        """
        Fetch and parse company code list from DART API

        Args:
            force_refresh: Force refresh even if cached

        Returns:
            DataFrame with columns: [corp_code, corp_name, stock_code, ceo_nm, modify_date]
        """
        # Check cache (update daily)
        if self.corp_code_cache is not None and not force_refresh:
            if (datetime.now() - self.last_update).days == 0:
                return self.corp_code_cache

        # Download from DART
        url = f"{self.base_url}/corpCode.xml"
        params = {'crtfc_key': self.api_key}

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            # Parse XML
            root = ET.fromstring(response.content)

            data = []
            for item in root.findall('list'):
                data.append({
                    'corp_code': item.findtext('corp_code'),
                    'corp_name': item.findtext('corp_name'),
                    'stock_code': item.findtext('stock_code'),
                    'ceo_nm': item.findtext('ceo_nm'),
                    'modify_date': item.findtext('modify_date'),
                })

            df = pd.DataFrame(data)

            # Cache result
            self.corp_code_cache = df
            self.last_update = datetime.now()

            return df

        except Exception as e:
            print(f"Error fetching DART company list: {e}")
            if self.corp_code_cache is not None:
                print("Returning cached data")
                return self.corp_code_cache
            raise

# Example usage
dart_client = DARTClient(api_key="YOUR_API_KEY")
corp_df = dart_client.get_corp_code_list()
print(f"Total companies: {len(corp_df)}")
print(corp_df.head())
```

### 2.2 Alternative: Using OpenDartReader Library

```python
# pip install OpenDartReader

from OpenDartReader import OpenDartReader

odr = OpenDartReader("YOUR_API_KEY")

# Get company code list (automatically handled)
# Returns: corp_code, corp_name, stock_code, etc.
corp_list = odr.get_corp_list()
```

### 2.3 Data Update Strategy

```python
import json
from pathlib import Path
from datetime import datetime, timedelta

class StockDataCache:
    def __init__(self, cache_dir="./stock_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.metadata_file = self.cache_dir / "metadata.json"

    def should_update(self, data_type="corp_code", max_age_days=1):
        """Check if cache needs refresh based on age"""
        if not self.metadata_file.exists():
            return True

        with open(self.metadata_file, 'r') as f:
            metadata = json.load(f)

        if data_type not in metadata:
            return True

        last_update = datetime.fromisoformat(metadata[data_type]['last_update'])
        age = datetime.now() - last_update

        return age > timedelta(days=max_age_days)

    def save_corp_code_list(self, df):
        """Save company code list to cache"""
        cache_file = self.cache_dir / "corp_code_list.csv"
        df.to_csv(cache_file, index=False, encoding='utf-8-sig')

        # Update metadata
        metadata = {}
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)

        metadata['corp_code'] = {
            'last_update': datetime.now().isoformat(),
            'count': len(df),
            'file': str(cache_file)
        }

        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

    def load_corp_code_list(self):
        """Load company code list from cache"""
        cache_file = self.cache_dir / "corp_code_list.csv"
        if cache_file.exists():
            return pd.read_csv(cache_file, dtype={'corp_code': str, 'stock_code': str})
        return None

# Usage
cache = StockDataCache()

if cache.should_update('corp_code', max_age_days=1):
    print("Updating company list...")
    dart_client = DARTClient(api_key="YOUR_API_KEY")
    corp_df = dart_client.get_corp_code_list()
    cache.save_corp_code_list(corp_df)
else:
    print("Using cached company list")
    corp_df = cache.load_corp_code_list()
```

---

## 3. Complete Stock Data Collection Implementation

### 3.1 Full Data Collection Pipeline

```python
import pandas as pd
from pykrx import stock
import time
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KoreanStockDataCollector:
    def __init__(self):
        self.data_dir = Path("./stock_data")
        self.data_dir.mkdir(exist_ok=True)

    def collect_market_data(self, end_date="20231215", market="KOSPI"):
        """
        Collect complete market data for a date

        Args:
            end_date: Date in YYYYMMDD format
            market: "KOSPI", "KOSDAQ", or "KONEX"
        """
        logger.info(f"Collecting {market} data for {end_date}")

        # Get ticker list
        tickers = stock.get_market_ticker_list(end_date, market=market)
        logger.info(f"Found {len(tickers)} tickers in {market}")

        all_data = []

        for idx, ticker in enumerate(tickers):
            try:
                # Get company name
                name = stock.get_market_ticker_name(ticker)

                # Get fundamental data
                fund_df = stock.get_market_fundamental_by_ticker(
                    end_date,
                    market=market
                )

                # Find this ticker's data
                if ticker in fund_df.index:
                    row = fund_df.loc[ticker].to_dict()
                    row['ticker'] = ticker
                    row['company_name'] = name
                    row['market'] = market
                    all_data.append(row)

                if (idx + 1) % 50 == 0:
                    logger.info(f"Processed {idx + 1}/{len(tickers)}")

                # Rate limiting (IMPORTANT)
                time.sleep(0.5)

            except Exception as e:
                logger.warning(f"Error processing {ticker}: {e}")
                continue

        # Save to CSV
        result_df = pd.DataFrame(all_data)
        output_file = self.data_dir / f"{market}_{end_date}.csv"
        result_df.to_csv(output_file, index=False, encoding='utf-8-sig')

        logger.info(f"Saved {len(result_df)} records to {output_file}")
        return result_df

    def collect_historical_data(self, tickers, start_date, end_date):
        """
        Collect historical OHLCV data for multiple tickers

        Args:
            tickers: List of ticker symbols
            start_date: Start date in YYYYMMDD format
            end_date: End date in YYYYMMDD format
        """
        all_data = []

        for idx, ticker in enumerate(tickers):
            try:
                df = stock.get_market_ohlcv(start_date, end_date, ticker)
                df['ticker'] = ticker
                all_data.append(df)

                if (idx + 1) % 50 == 0:
                    logger.info(f"Processed {idx + 1}/{len(tickers)}")

                time.sleep(0.5)

            except Exception as e:
                logger.warning(f"Error collecting data for {ticker}: {e}")
                continue

        result_df = pd.concat(all_data)
        output_file = self.data_dir / f"historical_{start_date}_{end_date}.csv"
        result_df.to_csv(output_file, encoding='utf-8-sig')

        logger.info(f"Saved {len(result_df)} historical records")
        return result_df

# Usage
collector = KoreanStockDataCollector()
kospi_data = collector.collect_market_data("20231215", "KOSPI")
```

---

## 4. Search Algorithm Recommendations

### 4.1 Comparison Table: Algorithms for 3000+ Companies

| Algorithm | Data Size | Speed | Setup | Korean Support | Recommendation |
|-----------|-----------|-------|-------|-----------------|-----------------|
| **Database LIKE Query** | 1000-10K | ~50-500ms | Low | Native | Not recommended alone |
| **Indexed Database** | 1000-100K | ~10-50ms | Medium | Native | Good for server-side |
| **Trie (In-Memory)** | 1000-100K | ~5-20ms | Medium | Requires wrapper | Excellent for 3K items |
| **Fuse.js (Client-Side)** | 1000-5K | ~50-200ms | Very Low | Via library | Good for small datasets |
| **Elasticsearch** | 100K+ | ~10-100ms | High | Excellent | Over-engineered for 3K |
| **Hybrid (Server + Client)** | 1000-100K | ~10-100ms | Medium | Excellent | BEST CHOICE |

### 4.2 Recommended: Hybrid Approach

**Architecture:**
```
┌─────────────────┐
│   User Input    │
└────────┬────────┘
         │ (debounce 300ms)
         ↓
┌─────────────────────────────────┐
│   Client-Side Fuzzy Search      │  ← Fuse.js (pre-loaded 3000 items)
│   Response: <50ms               │
└──────────────┬──────────────────┘
               │ (No server request for local data)
               │
               ├─→ Exact match? → Return from cache
               │
               ├─→ Fuzzy match? → Return from cache
               │
               └─→ Not found locally → Query server
                  ↓
         ┌──────────────────────┐
         │   Server Database    │
         │   (Indexed search)   │
         │   Response: <50ms    │
         └──────────────────────┘
```

**Advantages:**
- Sub-50ms response time for 90% of queries (cached locally)
- Works offline with cached data
- Reduces server load
- Supports all search modes (exact, fuzzy, Korean)

---

## 5. Implementation: Hybrid Search System

### 5.1 Backend Setup (Node.js/Express)

```typescript
// backend/src/services/StockSearchService.ts

import { PrismaClient } from '@prisma/client';
import { Stock } from '@prisma/client';

const prisma = new PrismaClient();

export class StockSearchService {
  /**
   * Index-optimized database search
   * Uses left-anchored LIKE for index efficiency
   */
  async searchStocks(
    query: string,
    limit: number = 20
  ): Promise<Stock[]> {
    if (!query || query.length < 2) {
      return [];
    }

    // Escape special characters for LIKE
    const escapedQuery = query.replace(/[_%\\]/g, '\\$&');

    // Use UNION to search multiple fields with proper indexing
    const results = await prisma.$queryRaw`
      (
        SELECT * FROM stocks
        WHERE company_name LIKE ${escapedQuery + '%'}
        LIMIT ${limit}
      )
      UNION
      (
        SELECT * FROM stocks
        WHERE stock_code LIKE ${escapedQuery + '%'}
        LIMIT ${limit}
      )
      UNION
      (
        SELECT * FROM stocks
        WHERE corp_code LIKE ${escapedQuery + '%'}
        LIMIT ${limit}
      )
      LIMIT ${limit}
    `;

    return results;
  }

  /**
   * Get all stocks for initial load (client-side caching)
   */
  async getAllStocks(): Promise<Stock[]> {
    return prisma.stock.findMany({
      select: {
        id: true,
        stock_code: true,
        corp_code: true,
        company_name: true,
        market: true,
      },
      orderBy: { company_name: 'asc' },
    });
  }

  /**
   * Bulk upsert stocks (for data synchronization)
   */
  async syncStocks(stocks: Stock[]): Promise<number> {
    let upsertCount = 0;

    for (const stock of stocks) {
      await prisma.stock.upsert({
        where: { stock_code: stock.stock_code },
        update: stock,
        create: stock,
      });
      upsertCount++;
    }

    return upsertCount;
  }
}
```

**Database Schema (Prisma):**
```prisma
// prisma/schema.prisma

model Stock {
  id          String    @id @default(cuid())
  stock_code  String    @unique @db.VarChar(6)
  corp_code   String    @unique @db.VarChar(8)
  company_name String   @db.VarChar(255)
  market      String    @db.VarChar(20)
  created_at  DateTime  @default(now())
  updated_at  DateTime  @updatedAt

  // Indexes for fast searching
  @@index([company_name])
  @@index([stock_code])
  @@index([corp_code])
  @@index([market])
}
```

**API Endpoint:**
```typescript
// backend/src/routes/stocks.ts

import express from 'express';
import { StockSearchService } from '../services/StockSearchService';

const router = express.Router();
const searchService = new StockSearchService();

// Quick server-side search for substrings
router.get('/api/stocks/search', async (req, res) => {
  try {
    const { q, limit = 20 } = req.query;

    if (!q || typeof q !== 'string' || q.length < 2) {
      return res.json({ data: [] });
    }

    const results = await searchService.searchStocks(
      q,
      Math.min(parseInt(limit as string) || 20, 100)
    );

    res.json({ data: results });
  } catch (error) {
    console.error('Search error:', error);
    res.status(500).json({ error: 'Search failed' });
  }
});

// Get all stocks for initial client load
router.get('/api/stocks/all', async (req, res) => {
  try {
    const stocks = await searchService.getAllStocks();
    res.json({ data: stocks });
  } catch (error) {
    console.error('Fetch error:', error);
    res.status(500).json({ error: 'Failed to fetch stocks' });
  }
});

export default router;
```

### 5.2 Frontend Setup (React/Vue)

**Installation:**
```bash
npm install fuse.js hangul-js
```

**Implementation with Fuzzy Search + Hangul Support:**

```typescript
// frontend/src/hooks/useStockSearch.ts

import { useState, useEffect, useMemo, useCallback } from 'react';
import Fuse from 'fuse.js';
import { hangul } from 'hangul-js';

interface Stock {
  id: string;
  stock_code: string;
  corp_code: string;
  company_name: string;
  market: string;
}

export function useStockSearch() {
  const [allStocks, setAllStocks] = useState<Stock[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize Fuse.js for fuzzy search
  const fuse = useMemo(() => {
    if (!allStocks.length) return null;

    return new Fuse(allStocks, {
      keys: [
        { name: 'company_name', weight: 0.7 },
        { name: 'stock_code', weight: 0.2 },
        { name: 'corp_code', weight: 0.1 },
      ],
      threshold: 0.4, // Allow ~40% character variance
      minMatchCharLength: 2,
      includeScore: true,
    });
  }, [allStocks]);

  // Load all stocks on mount
  useEffect(() => {
    const loadStocks = async () => {
      try {
        const response = await fetch('/api/stocks/all');
        const data = await response.json();
        setAllStocks(data.data || []);
        setIsInitialized(true);
      } catch (error) {
        console.error('Failed to load stocks:', error);
        setIsInitialized(true);
      }
    };

    loadStocks();
  }, []);

  // Extract initial consonants from Hangul
  const getChoseong = useCallback((text: string): string => {
    return hangul
      .disassemble(text)
      .filter((char) => {
        // Keep only initial consonants
        const choseongList = [
          'ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅄ', 'ㅅ',
          'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'
        ];
        return choseongList.includes(char);
      })
      .join('');
  }, []);

  // Main search function
  const search = useCallback(async (query: string) => {
    setSearchQuery(query);

    if (!query || query.length < 2) {
      setResults([]);
      return;
    }

    if (!fuse || !isInitialized) {
      setResults([]);
      return;
    }

    setLoading(true);

    try {
      let searchResults: Stock[] = [];

      // 1. Try exact match first
      const exactMatches = allStocks.filter(
        (stock) =>
          stock.company_name.includes(query) ||
          stock.stock_code.includes(query) ||
          stock.corp_code.includes(query)
      );

      if (exactMatches.length > 0) {
        searchResults = exactMatches;
      } else {
        // 2. Try fuzzy match
        const fuzzyMatches = fuse.search(query).map((result) => result.item);
        searchResults = fuzzyMatches;

        // 3. Try initial consonant (초성) search if query is all Hangul
        if (searchResults.length === 0 && /^[가-힣]+$/.test(query)) {
          const queryChoseong = getChoseong(query);

          searchResults = allStocks.filter((stock) => {
            const nameChoseong = getChoseong(stock.company_name);
            return nameChoseong.includes(queryChoseong);
          });
        }
      }

      setResults(searchResults.slice(0, 20)); // Limit to top 20
    } catch (error) {
      console.error('Search error:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [fuse, isInitialized, allStocks, getChoseong]);

  return {
    query: searchQuery,
    results,
    loading,
    isInitialized,
    search,
    allStocks,
  };
}
```

**React Component:**

```tsx
// frontend/src/components/StockSearchAutocomplete.tsx

import React, { useState, useCallback } from 'react';
import { useStockSearch } from '../hooks/useStockSearch';
import './StockSearchAutocomplete.css';

interface StockSearchAutocompleteProps {
  onSelectStock?: (stock: any) => void;
}

export function StockSearchAutocomplete({
  onSelectStock,
}: StockSearchAutocompleteProps) {
  const { query, results, loading, isInitialized, search, allStocks } =
    useStockSearch();
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [searchTimeout, setSearchTimeout] = useState<NodeJS.Timeout | null>(null);

  // Debounced search (300ms)
  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value;

      if (searchTimeout) {
        clearTimeout(searchTimeout);
      }

      const timeout = setTimeout(() => {
        search(value);
        setShowDropdown(value.length >= 2);
        setSelectedIndex(-1);
      }, 300);

      setSearchTimeout(timeout);
    },
    [search, searchTimeout]
  );

  const handleSelectStock = useCallback(
    (stock: any) => {
      onSelectStock?.(stock);
      setShowDropdown(false);
    },
    [onSelectStock]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (!showDropdown) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex((i) =>
            i < results.length - 1 ? i + 1 : results.length - 1
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex((i) => (i > 0 ? i - 1 : -1));
          break;
        case 'Enter':
          e.preventDefault();
          if (selectedIndex >= 0) {
            handleSelectStock(results[selectedIndex]);
          }
          break;
        case 'Escape':
          setShowDropdown(false);
          break;
      }
    },
    [showDropdown, results, selectedIndex, handleSelectStock]
  );

  if (!isInitialized) {
    return <div>Loading stocks...</div>;
  }

  return (
    <div className="stock-search-container">
      <input
        type="text"
        placeholder="회사명, 종목코드 또는 초성 입력... (e.g., 삼성, 005930, ㅅㅅ)"
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onFocus={() => {
          if (query.length >= 2) {
            setShowDropdown(true);
          }
        }}
        onBlur={() => {
          setTimeout(() => setShowDropdown(false), 200);
        }}
        className="stock-search-input"
      />

      {loading && <div className="stock-search-loading">검색 중...</div>}

      {showDropdown && results.length > 0 && (
        <ul className="stock-search-dropdown">
          {results.map((stock, index) => (
            <li
              key={stock.id}
              className={`stock-search-item ${
                index === selectedIndex ? 'selected' : ''
              }`}
              onClick={() => handleSelectStock(stock)}
              onMouseEnter={() => setSelectedIndex(index)}
            >
              <strong>{stock.company_name}</strong>
              <span className="stock-code">{stock.stock_code}</span>
              <span className="market-badge">{stock.market}</span>
            </li>
          ))}
        </ul>
      )}

      {showDropdown && query.length >= 2 && results.length === 0 && (
        <div className="stock-search-no-results">
          검색 결과가 없습니다.
        </div>
      )}
    </div>
  );
}
```

**Styling:**

```css
/* frontend/src/components/StockSearchAutocomplete.css */

.stock-search-container {
  position: relative;
  width: 100%;
  max-width: 500px;
}

.stock-search-input {
  width: 100%;
  padding: 10px 12px;
  border: 2px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.stock-search-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

.stock-search-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #ddd;
  border-top: none;
  border-radius: 0 0 6px 6px;
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 300px;
  overflow-y: auto;
  z-index: 10;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.stock-search-item {
  padding: 12px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: background-color 0.2s;
}

.stock-search-item:hover,
.stock-search-item.selected {
  background-color: #f5f5f5;
}

.stock-search-item strong {
  flex: 1;
}

.stock-code {
  color: #666;
  font-size: 12px;
  font-weight: 500;
}

.market-badge {
  background-color: #007bff;
  color: white;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 600;
}

.stock-search-loading,
.stock-search-no-results {
  padding: 12px;
  text-align: center;
  color: #666;
  font-size: 14px;
  background: white;
  border: 1px solid #ddd;
  border-top: none;
}
```

---

## 6. Korean Language Search Implementation

### 6.1 Initial Consonant (초성) Search

```typescript
// utils/hangulUtils.ts

import { hangul } from 'hangul-js';

/**
 * Extract initial consonants from Korean text
 * 예: "삼성전자" → "ㅅㅅㅇㅈ"
 */
export function getChoseong(text: string): string {
  const disassembled = hangul.disassemble(text);
  const choseongList = [
    'ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅄ', 'ㅅ',
    'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'
  ];

  return disassembled
    .filter((char) => choseongList.includes(char))
    .join('');
}

/**
 * Check if text matches initial consonant pattern
 */
export function matchesChoseong(text: string, pattern: string): boolean {
  const textChoseong = getChoseong(text);
  return textChoseong.includes(pattern);
}

/**
 * Romanize Hangul characters to English
 * 예: "삼성" → "samsung"
 */
export function romanize(text: string): string {
  const hangulToRoman: Record<string, string> = {
    'ㄱ': 'g', 'ㄲ': 'kk', 'ㄴ': 'n', 'ㄷ': 'd', 'ㄸ': 'dd',
    'ㄹ': 'r', 'ㅁ': 'm', 'ㅂ': 'b', 'ㅃ': 'pp', 'ㅄ': 'bs',
    'ㅅ': 's', 'ㅆ': 'ss', 'ㅇ': '', 'ㅈ': 'j', 'ㅉ': 'jj',
    'ㅊ': 'ch', 'ㅋ': 'k', 'ㅌ': 't', 'ㅍ': 'p', 'ㅎ': 'h',
    'ㅏ': 'a', 'ㅑ': 'ya', 'ㅓ': 'eo', 'ㅕ': 'yeo', 'ㅗ': 'o',
    'ㅛ': 'yo', 'ㅜ': 'u', 'ㅠ': 'yu', 'ㅡ': 'eu', 'ㅣ': 'i',
  };

  const disassembled = hangul.disassemble(text);
  return disassembled.map((char) => hangulToRoman[char] || char).join('');
}

/**
 * Comprehensive fuzzy search with Korean support
 */
export function fuzzySearchKorean(
  items: Array<{ name: string; [key: string]: any }>,
  query: string,
  limit: number = 20
): Array<{ name: string; [key: string]: any }> {
  if (!query) return [];

  const isAllHangul = /^[가-힣]+$/.test(query);
  const isAllChoseong = /^[ㄱ-ㅎ]+$/.test(query);

  return items
    .filter((item) => {
      const name = item.name;

      // Exact match
      if (name.includes(query)) return true;

      // Fuzzy character match
      let queryIndex = 0;
      for (let i = 0; i < name.length && queryIndex < query.length; i++) {
        if (name[i] === query[queryIndex]) {
          queryIndex++;
        }
      }
      if (queryIndex === query.length) return true;

      // Choseong match for Hangul input
      if (isAllHangul || isAllChoseong) {
        return matchesChoseong(name, query);
      }

      // Romanization match
      const nameRoman = romanize(name);
      return nameRoman.includes(query.toLowerCase());
    })
    .slice(0, limit);
}
```

### 6.2 Multi-mode Korean Search

```typescript
// frontend/src/hooks/useKoreanStockSearch.ts

import { useState, useEffect, useCallback } from 'react';
import {
  getChoseong,
  matchesChoseong,
  romanize,
  fuzzySearchKorean,
} from '../utils/hangulUtils';

interface Stock {
  id: string;
  stock_code: string;
  corp_code: string;
  company_name: string;
  market: string;
}

export function useKoreanStockSearch() {
  const [allStocks, setAllStocks] = useState<Stock[]>([]);
  const [results, setResults] = useState<Stock[]>([]);
  const [query, setQuery] = useState('');
  const [searchMode, setSearchMode] = useState<'all' | 'hangul' | 'choseong' | 'english'>('all');

  // Load stocks
  useEffect(() => {
    const loadStocks = async () => {
      try {
        const response = await fetch('/api/stocks/all');
        const data = await response.json();
        setAllStocks(data.data || []);
      } catch (error) {
        console.error('Failed to load stocks:', error);
      }
    };

    loadStocks();
  }, []);

  // Detect input type
  const detectSearchMode = useCallback((text: string) => {
    if (/^[가-힣]+$/.test(text)) {
      return 'hangul';
    } else if (/^[ㄱ-ㅎ]+$/.test(text)) {
      return 'choseong';
    } else if (/^[a-z]+$/i.test(text)) {
      return 'english';
    }
    return 'all';
  }, []);

  // Perform search
  const search = useCallback(
    (searchQuery: string) => {
      setQuery(searchQuery);

      if (!searchQuery || searchQuery.length < 2) {
        setResults([]);
        return;
      }

      const mode = detectSearchMode(searchQuery);
      setSearchMode(mode);

      let searchResults: Stock[] = [];

      if (mode === 'hangul') {
        // Full Hangul search (exact + fuzzy)
        searchResults = allStocks.filter((stock) =>
          stock.company_name.includes(searchQuery) ||
          fuzzySearchKorean([stock], searchQuery).length > 0
        );
      } else if (mode === 'choseong') {
        // Initial consonant search
        searchResults = allStocks.filter((stock) =>
          matchesChoseong(stock.company_name, searchQuery)
        );
      } else if (mode === 'english') {
        // Romanized search
        searchResults = allStocks.filter((stock) => {
          const romanized = romanize(stock.company_name);
          return (
            romanized.includes(searchQuery.toLowerCase()) ||
            stock.stock_code.includes(searchQuery.toUpperCase())
          );
        });
      } else {
        // Mixed mode - try all methods
        searchResults = allStocks.filter((stock) => {
          return (
            stock.company_name.includes(searchQuery) ||
            stock.stock_code.includes(searchQuery) ||
            stock.corp_code.includes(searchQuery) ||
            romanize(stock.company_name).includes(searchQuery.toLowerCase())
          );
        });
      }

      setResults(searchResults.slice(0, 20));
    },
    [allStocks, detectSearchMode]
  );

  return {
    query,
    results,
    searchMode,
    search,
    allStocks,
  };
}
```

---

## 7. Performance Benchmarks & Optimization

### 7.1 Expected Response Times

| Operation | Size | Method | Time |
|-----------|------|--------|------|
| **Initial load** | 3000 items | Client-side cache | 100-500ms |
| **Exact match** | 3000 items | In-memory search | 5-20ms |
| **Fuzzy match** | 3000 items | Fuse.js | 50-100ms |
| **Choseong search** | 3000 items | In-memory filter | 10-30ms |
| **Database LIKE** | 3000 items | Indexed query | 10-50ms |
| **Full table scan** | 3000 items | Unindexed | 100-500ms |

### 7.2 Optimization Techniques

**1. Client-Side Caching:**
```typescript
// Cache stocks in localStorage for offline support
export function cacheStocks(stocks: Stock[]): void {
  const cached = {
    timestamp: Date.now(),
    data: stocks,
  };
  localStorage.setItem('cached_stocks', JSON.stringify(cached));
}

export function getCachedStocks(): Stock[] | null {
  const cached = localStorage.getItem('cached_stocks');
  if (!cached) return null;

  const { timestamp, data } = JSON.parse(cached);
  const age = Date.now() - timestamp;

  // Cache valid for 24 hours
  if (age < 24 * 60 * 60 * 1000) {
    return data;
  }

  return null;
}
```

**2. Debouncing User Input:**
```typescript
export function useDebouncedSearch(
  searchFn: (query: string) => void,
  delay: number = 300
) {
  const [timeout, setTimeout] = useState<NodeJS.Timeout | null>(null);

  return (query: string) => {
    if (timeout) clearTimeout(timeout);

    const newTimeout = setTimeout(() => {
      searchFn(query);
    }, delay);

    setTimeout(newTimeout);
  };
}
```

**3. Database Index Creation:**
```sql
-- Create indexes for fast searching
CREATE INDEX idx_stocks_company_name ON stocks(company_name);
CREATE INDEX idx_stocks_stock_code ON stocks(stock_code);
CREATE INDEX idx_stocks_corp_code ON stocks(corp_code);

-- For prefix-based search (LIKE 'prefix%')
CREATE INDEX idx_stocks_company_name_prefix
ON stocks(company_name VARCHAR(255));
```

**4. Query Optimization:**
```typescript
// Use connection pooling
import { Pool } from 'pg';

const pool = new Pool({
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Use prepared statements
const searchQuery = `
  SELECT id, stock_code, corp_code, company_name, market
  FROM stocks
  WHERE company_name ILIKE $1 || '%'
  LIMIT 20
`;

const result = await pool.query(searchQuery, [escapedQuery]);
```

---

## 8. Legal & Ethical Considerations

### 8.1 Data Sourcing Guidelines

| Source | Legal Status | Recommendation | Notes |
|--------|--------------|-----------------|-------|
| **DART API** | Legal | Use officially | Official government API |
| **KRX Data** | Legal | Use officially | Official exchange data |
| **Naver Finance** | Terms prohibit scraping | Avoid direct scraping | Use PyKRX wrapper instead |
| **Web Scraping** | Gray area in Korea | Risky | Violates ToS; IP blocking |
| **Yahoo Finance** | API deprecated | Not recommended | No official support |

### 8.2 Responsible Usage

```python
# Best practices for data collection

1. REGISTER YOUR API KEY
   - DART API requires free registration
   - Use legitimate API keys only

2. RESPECT RATE LIMITS
   - Add delays between requests (0.5-1 second minimum)
   - Respect server load
   - Don't hammer endpoints

3. CACHE DATA LOCALLY
   - Avoid repeated requests for same data
   - Update daily/weekly, not per-request

4. HANDLE ERRORS GRACEFULLY
   - Implement retry logic with exponential backoff
   - Log errors properly
   - Notify users of failures

5. FOLLOW TERMS OF SERVICE
   - Read and follow platform ToS
   - Don't redistribute proprietary data
   - Use data only for intended purpose

# Example: Responsible data collection

import time
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ResponsibleStockDataCollector:
    def __init__(self, cache_ttl_hours=24):
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.last_update = {}

    def can_update(self, source_key: str) -> bool:
        """Check if enough time has passed since last update"""
        if source_key not in self.last_update:
            return True

        age = datetime.now() - self.last_update[source_key]
        return age > self.cache_ttl

    def fetch_with_backoff(self, fetch_fn, max_retries=3):
        """Fetch with exponential backoff"""
        for attempt in range(max_retries):
            try:
                result = fetch_fn()
                self.last_update[fetch_fn.__name__] = datetime.now()
                return result
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 1s, 2s, 4s
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Max retries exceeded: {e}")
                    raise
```

---

## 9. Summary & Recommendations

### 9.1 Recommended Tech Stack

**Data Collection:**
```
DART API (primary)
  ↓
PyKRX (convenience)
  ↓
Cached in PostgreSQL
```

**Search Implementation:**
```
Frontend:
  - Fuse.js (fuzzy matching)
  - hangul-js (Korean support)
  - React/Vue for UI

Backend:
  - Express/FastAPI
  - PostgreSQL with indexes
  - Node.js caching layer (optional)
```

### 9.2 Implementation Phases

**Phase 1: Data Pipeline (Week 1-2)**
- Register DART API key
- Implement stock data sync
- Setup PostgreSQL database
- Create automated update schedule

**Phase 2: Backend API (Week 2-3)**
- Build search endpoints
- Create indexes
- Implement caching
- Add error handling

**Phase 3: Frontend Search (Week 3-4)**
- Implement Fuse.js integration
- Add Korean language support
- Create autocomplete UI
- Performance optimization

**Phase 4: Testing & Deployment (Week 4)**
- Load testing (3000+ items)
- Performance benchmarking
- Korean language testing
- Deploy to production

### 9.3 Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| Initial load time | < 500ms | Achievable with caching |
| Search response | < 100ms | Achievable with Fuse.js + indexes |
| Autocomplete latency | < 50ms | Achievable with debouncing |
| UI responsiveness | 60 FPS | Standard modern browser |
| Data freshness | Daily | Recommended update frequency |

---

## 10. Resources & References

### Official APIs
- DART API: https://opendart.fss.or.kr/ (Korean) | https://englishdart.fss.or.kr/ (English)
- KRX: https://data.krx.co.kr/
- PyKRX GitHub: https://github.com/sharebook-kr/pykrx

### Libraries
- Fuse.js: https://www.fusejs.io/
- hangul-js: https://github.com/e-/Hangul.js
- es-hangul: https://github.com/toss/es-hangul
- OpenDartReader: https://github.com/FinanceData/OpenDartReader

### Documentation
- Database indexing: https://use-the-index-luke.com/
- Autocomplete UX: https://www.algolia.com/blog/
- Korean language NLP: https://konlpy.org/

---

**Last Updated:** 2025-11-21
**Research Completed By:** Korean Stock Search Research Team

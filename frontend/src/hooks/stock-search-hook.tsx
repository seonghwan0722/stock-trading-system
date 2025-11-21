/**
 * Korean Stock Search Hook with Hangul Support
 *
 * Provides fuzzy search, initial consonant search, and romanization support
 * for Korean stock market data.
 *
 * Features:
 * - Exact match search
 * - Fuzzy matching with Fuse.js
 * - Initial consonant (초성) search
 * - Romanization support
 * - Debounced search input
 * - Client-side caching
 *
 * Usage:
 * ```tsx
 * const { query, results, loading, search } = useKoreanStockSearch();
 *
 * const handleSearch = (input: string) => {
 *   search(input);
 * };
 * ```
 */

import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import Fuse from 'fuse.js';
import Hangul from 'hangul-js';

interface Stock {
  id: string;
  stock_code: string;
  corp_code: string;
  company_name: string;
  market: 'KOSPI' | 'KOSDAQ' | 'KONEX';
}

interface SearchResult {
  stock: Stock;
  score?: number;
  matchType: 'exact' | 'fuzzy' | 'choseong' | 'romanized';
}

interface HangulUtils {
  getChoseong: (text: string) => string;
  matchesChoseong: (text: string, pattern: string) => boolean;
  romanize: (text: string) => string;
  detectInputType: (text: string) => 'hangul' | 'choseong' | 'english' | 'mixed';
}

/**
 * Hangul utility functions for Korean text processing
 */
const createHangulUtils = (): HangulUtils => {
  // Choseong (initial consonant) character list
  const CHOSEONG_LIST = [
    'ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅄ', 'ㅅ',
    'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'
  ];

  // Romanization map
  const HANGUL_TO_ROMAN: Record<string, string> = {
    'ㄱ': 'g', 'ㄲ': 'kk', 'ㄴ': 'n', 'ㄷ': 'd', 'ㄸ': 'dd',
    'ㄹ': 'r', 'ㅁ': 'm', 'ㅂ': 'b', 'ㅃ': 'pp', 'ㅄ': 'bs',
    'ㅅ': 's', 'ㅆ': 'ss', 'ㅇ': '', 'ㅈ': 'j', 'ㅉ': 'jj',
    'ㅊ': 'ch', 'ㅋ': 'k', 'ㅌ': 't', 'ㅍ': 'p', 'ㅎ': 'h',
    'ㅏ': 'a', 'ㅑ': 'ya', 'ㅓ': 'eo', 'ㅕ': 'yeo', 'ㅗ': 'o',
    'ㅛ': 'yo', 'ㅜ': 'u', 'ㅠ': 'yu', 'ㅡ': 'eu', 'ㅣ': 'i',
  };

  /**
   * Extract initial consonants from Korean text
   * Example: "삼성전자" → "ㅅㅅㅇㅈ"
   */
  const getChoseong = (text: string): string => {
    try {
      const disassembled = Hangul.disassemble(text);
      return disassembled
        .filter((char) => CHOSEONG_LIST.includes(char))
        .join('');
    } catch (error) {
      console.error('Error extracting choseong:', error);
      return '';
    }
  };

  /**
   * Check if text matches initial consonant pattern
   */
  const matchesChoseong = (text: string, pattern: string): boolean => {
    const textChoseong = getChoseong(text);
    return textChoseong.includes(pattern);
  };

  /**
   * Romanize Hangul characters to English
   * Example: "삼성" → "samsung"
   */
  const romanize = (text: string): string => {
    try {
      const disassembled = Hangul.disassemble(text);
      return disassembled
        .map((char) => HANGUL_TO_ROMAN[char] || char)
        .join('')
        .toLowerCase();
    } catch (error) {
      console.error('Error romanizing text:', error);
      return text.toLowerCase();
    }
  };

  /**
   * Detect the type of input
   */
  const detectInputType = (text: string): 'hangul' | 'choseong' | 'english' | 'mixed' => {
    if (/^[가-힣]+$/.test(text)) return 'hangul';
    if (/^[ㄱ-ㅎ]+$/.test(text)) return 'choseong';
    if (/^[a-z]+$/i.test(text)) return 'english';
    return 'mixed';
  };

  return {
    getChoseong,
    matchesChoseong,
    romanize,
    detectInputType,
  };
};

/**
 * Main hook for Korean stock search
 */
export function useKoreanStockSearch() {
  const [allStocks, setAllStocks] = useState<Stock[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const hangulUtils = useMemo(() => createHangulUtils(), []);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize Fuse.js for fuzzy search
  const fuse = useMemo(() => {
    if (!allStocks.length) return null;

    return new Fuse(allStocks, {
      keys: [
        { name: 'company_name', weight: 0.7 },
        { name: 'stock_code', weight: 0.2 },
        { name: 'corp_code', weight: 0.1 },
      ],
      threshold: 0.4, // Allow ~40% character variance for typos
      minMatchCharLength: 2,
      includeScore: true,
      shouldSort: true,
    });
  }, [allStocks]);

  // Load stocks from server or cache
  useEffect(() => {
    const loadStocks = async () => {
      try {
        setError(null);

        // Try to load from cache first
        const cached = localStorage.getItem('cached_stocks');
        if (cached) {
          try {
            const { data, timestamp } = JSON.parse(cached);
            const age = Date.now() - timestamp;
            // Cache valid for 24 hours
            if (age < 24 * 60 * 60 * 1000) {
              setAllStocks(data);
              setIsInitialized(true);
              return;
            }
          } catch (e) {
            console.warn('Failed to parse cached stocks:', e);
          }
        }

        // Load from server
        const response = await fetch('/api/stocks/all');
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        const stocks = data.data || [];

        setAllStocks(stocks);

        // Cache stocks
        try {
          localStorage.setItem(
            'cached_stocks',
            JSON.stringify({
              data: stocks,
              timestamp: Date.now(),
            })
          );
        } catch (e) {
          console.warn('Failed to cache stocks:', e);
        }

        setIsInitialized(true);
      } catch (err) {
        console.error('Failed to load stocks:', err);
        setError(err instanceof Error ? err.message : 'Failed to load stocks');
        setIsInitialized(true);
      }
    };

    loadStocks();
  }, []);

  // Perform local search
  const performLocalSearch = useCallback(
    (query: string): SearchResult[] => {
      if (!query || query.length < 2) return [];

      const inputType = hangulUtils.detectInputType(query);
      const results: SearchResult[] = [];
      const resultMap = new Map<string, SearchResult>();

      // 1. Exact match (highest priority)
      allStocks.forEach((stock) => {
        let isMatch = false;

        if (stock.company_name.includes(query)) {
          isMatch = true;
        } else if (stock.stock_code.includes(query)) {
          isMatch = true;
        } else if (stock.corp_code.includes(query)) {
          isMatch = true;
        }

        if (isMatch && !resultMap.has(stock.id)) {
          resultMap.set(stock.id, {
            stock,
            score: 1.0,
            matchType: 'exact',
          });
        }
      });

      // 2. Fuzzy match (if not too many exact matches)
      if (resultMap.size < 20 && fuse) {
        fuse.search(query).forEach((result) => {
          if (!resultMap.has(result.item.id)) {
            resultMap.set(result.item.id, {
              stock: result.item,
              score: 1 - (result.score ?? 0),
              matchType: 'fuzzy',
            });
          }
        });
      }

      // 3. Initial consonant (초성) search
      if ((inputType === 'hangul' || inputType === 'choseong') &&
          resultMap.size < 20) {
        const queryChoseong = hangulUtils.getChoseong(query);

        allStocks.forEach((stock) => {
          if (!resultMap.has(stock.id) &&
              hangulUtils.matchesChoseong(stock.company_name, queryChoseong)) {
            resultMap.set(stock.id, {
              stock,
              matchType: 'choseong',
            });
          }
        });
      }

      // 4. Romanization match
      if ((inputType === 'english' || inputType === 'mixed') &&
          resultMap.size < 20) {
        const queryLower = query.toLowerCase();

        allStocks.forEach((stock) => {
          if (!resultMap.has(stock.id)) {
            const nameRoman = hangulUtils.romanize(stock.company_name);

            if (nameRoman.includes(queryLower) ||
                stock.stock_code.toLowerCase().includes(queryLower)) {
              resultMap.set(stock.id, {
                stock,
                matchType: 'romanized',
              });
            }
          }
        });
      }

      // Convert to array and limit results
      return Array.from(resultMap.values()).slice(0, 20);
    },
    [allStocks, fuse, hangulUtils]
  );

  // Main search function with debouncing
  const search = useCallback(
    (query: string) => {
      setSearchQuery(query);
      setError(null);

      // Clear previous timeout
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }

      if (!query || query.length < 2) {
        setResults([]);
        return;
      }

      if (!isInitialized) {
        setResults([]);
        return;
      }

      setLoading(true);

      // Debounce search by 300ms
      searchTimeoutRef.current = setTimeout(() => {
        try {
          const searchResults = performLocalSearch(query);
          setResults(searchResults);
        } catch (err) {
          console.error('Search error:', err);
          setError(err instanceof Error ? err.message : 'Search failed');
          setResults([]);
        } finally {
          setLoading(false);
        }
      }, 300);
    },
    [isInitialized, performLocalSearch]
  );

  // Server-side search as fallback
  const serverSearch = useCallback(
    async (query: string): Promise<SearchResult[]> => {
      if (!query || query.length < 2) return [];

      try {
        const response = await fetch(`/api/stocks/search?q=${encodeURIComponent(query)}`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        const stocks = (data.data || []) as Stock[];

        return stocks.map((stock) => ({
          stock,
          matchType: 'exact' as const,
        }));
      } catch (err) {
        console.error('Server search error:', err);
        return [];
      }
    },
    []
  );

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, []);

  return {
    // Input state
    query: searchQuery,
    setQuery: setSearchQuery,

    // Results
    results,
    loading,

    // State
    isInitialized,
    error,
    stockCount: allStocks.length,

    // Methods
    search,
    serverSearch,
    clearResults: () => setResults([]),

    // Raw data access
    allStocks,
  };
}

/**
 * Hook for batch stock search with caching
 */
export function useStockBatchSearch() {
  const [batchResults, setBatchResults] = useState<Map<string, Stock>>(new Map());
  const [loading, setLoading] = useState(false);

  const searchBatch = useCallback(
    async (queries: string[]): Promise<Stock[]> => {
      setLoading(true);

      try {
        const results: Stock[] = [];

        for (const query of queries) {
          const response = await fetch(`/api/stocks/search?q=${encodeURIComponent(query)}`);

          if (response.ok) {
            const data = await response.json();
            if (data.data && data.data.length > 0) {
              results.push(data.data[0]);
            }
          }

          // Add delay to avoid overwhelming server
          await new Promise((resolve) => setTimeout(resolve, 100));
        }

        // Cache results
        const resultMap = new Map(batchResults);
        results.forEach((stock) => {
          resultMap.set(stock.stock_code, stock);
        });
        setBatchResults(resultMap);

        return results;
      } catch (err) {
        console.error('Batch search error:', err);
        return [];
      } finally {
        setLoading(false);
      }
    },
    [batchResults]
  );

  return {
    batchResults,
    loading,
    searchBatch,
  };
}

export type { Stock, SearchResult, HangulUtils };

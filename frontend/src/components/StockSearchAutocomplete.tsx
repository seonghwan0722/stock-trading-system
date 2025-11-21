/**
 * Korean Stock Search Autocomplete Component
 *
 * A fully-featured autocomplete component for searching Korean stocks with:
 * - Fuzzy matching
 * - Initial consonant (초성) search
 * - Keyboard navigation
 * - Loading states
 * - Error handling
 * - Market badges
 * - Debounced input
 *
 * Usage:
 * ```tsx
 * <StockSearchAutocomplete
 *   onSelectStock={(stock) => console.log(stock)}
 *   placeholder="회사명 또는 종목코드"
 *   limit={20}
 * />
 * ```
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useKoreanStockSearch, type Stock, type SearchResult } from '../hooks/useKoreanStockSearch';
import styles from './StockSearchAutocomplete.module.css';

interface StockSearchAutocompleteProps {
  onSelectStock?: (stock: Stock) => void;
  placeholder?: string;
  limit?: number;
  disabled?: boolean;
  className?: string;
  showMarketBadge?: boolean;
  showStockCode?: boolean;
  clearOnSelect?: boolean;
}

export function StockSearchAutocomplete({
  onSelectStock,
  placeholder = '회사명, 종목코드 또는 초성 입력... (예: 삼성, 005930, ㅅㅅ)',
  limit = 20,
  disabled = false,
  className,
  showMarketBadge = true,
  showStockCode = true,
  clearOnSelect = true,
}: StockSearchAutocompleteProps) {
  const { query, results, loading, isInitialized, error, search, clearResults } =
    useKoreanStockSearch();

  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [highlightedResult, setHighlightedResult] = useState<SearchResult | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const selectedItemRef = useRef<HTMLLIElement>(null);

  // Handle input change
  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.currentTarget.value;
      search(value);
      setShowDropdown(value.length >= 2);
      setSelectedIndex(-1);
    },
    [search]
  );

  // Handle stock selection
  const handleSelectStock = useCallback(
    (stock: Stock) => {
      onSelectStock?.(stock);

      if (clearOnSelect) {
        if (inputRef.current) {
          inputRef.current.value = '';
        }
        search('');
        setShowDropdown(false);
      }

      clearResults();
    },
    [onSelectStock, clearOnSelect, search, clearResults]
  );

  // Handle keyboard navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (!showDropdown || results.length === 0) {
        if (e.key === 'Escape') {
          setShowDropdown(false);
        }
        return;
      }

      switch (e.key) {
        case 'ArrowDown': {
          e.preventDefault();
          const nextIndex = Math.min(selectedIndex + 1, results.length - 1);
          setSelectedIndex(nextIndex);
          setHighlightedResult(results[nextIndex]);
          break;
        }

        case 'ArrowUp': {
          e.preventDefault();
          if (selectedIndex <= 0) {
            setSelectedIndex(-1);
            setHighlightedResult(null);
          } else {
            const prevIndex = selectedIndex - 1;
            setSelectedIndex(prevIndex);
            setHighlightedResult(results[prevIndex]);
          }
          break;
        }

        case 'Enter': {
          e.preventDefault();
          if (selectedIndex >= 0 && results[selectedIndex]) {
            handleSelectStock(results[selectedIndex].stock);
          }
          break;
        }

        case 'Escape': {
          setShowDropdown(false);
          setSelectedIndex(-1);
          setHighlightedResult(null);
          break;
        }

        case 'Tab': {
          if (selectedIndex >= 0 && results[selectedIndex]) {
            handleSelectStock(results[selectedIndex].stock);
          }
          break;
        }

        default:
          break;
      }
    },
    [showDropdown, results, selectedIndex, handleSelectStock]
  );

  // Handle focus
  const handleFocus = useCallback(() => {
    if (query.length >= 2 && results.length > 0) {
      setShowDropdown(true);
    }
  }, [query, results]);

  // Handle blur
  const handleBlur = useCallback(() => {
    // Delay to allow click events to register
    setTimeout(() => {
      setShowDropdown(false);
    }, 200);
  }, []);

  // Scroll selected item into view
  useEffect(() => {
    if (selectedItemRef.current && dropdownRef.current) {
      selectedItemRef.current.scrollIntoView({
        block: 'nearest',
        behavior: 'smooth',
      });
    }
  }, [selectedIndex]);

  // Handle outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Get market badge color
  const getMarketColor = (market: Stock['market']): string => {
    switch (market) {
      case 'KOSPI':
        return '#007bff'; // Blue
      case 'KOSDAQ':
        return '#28a745'; // Green
      case 'KONEX':
        return '#ffc107'; // Yellow
      default:
        return '#6c757d'; // Gray
    }
  };

  // Render match type indicator
  const renderMatchTypeIndicator = (matchType: SearchResult['matchType']): string => {
    switch (matchType) {
      case 'exact':
        return '완벽';
      case 'fuzzy':
        return '유사';
      case 'choseong':
        return '초성';
      case 'romanized':
        return '로마자';
      default:
        return '';
    }
  };

  if (!isInitialized) {
    return (
      <div className={`${styles.container} ${className || ''}`}>
        <input
          type="text"
          disabled
          placeholder="주식 정보 로딩 중..."
          className={styles.input}
        />
      </div>
    );
  }

  return (
    <div className={`${styles.container} ${className || ''}`}>
      <div className={styles.inputWrapper}>
        <input
          ref={inputRef}
          type="text"
          placeholder={placeholder}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={handleFocus}
          onBlur={handleBlur}
          disabled={disabled}
          className={`${styles.input} ${disabled ? styles.disabled : ''}`}
          autoComplete="off"
          aria-label="주식 검색"
          aria-autocomplete="list"
          aria-expanded={showDropdown && results.length > 0}
          aria-controls="stock-dropdown"
        />

        {loading && <div className={styles.loadingSpinner} />}

        {error && <div className={styles.errorIcon} title={error}>!</div>}
      </div>

      {showDropdown && (
        <div
          ref={dropdownRef}
          id="stock-dropdown"
          className={`${styles.dropdown} ${results.length === 0 ? styles.empty : ''}`}
          role="listbox"
        >
          {results.length > 0 ? (
            <ul className={styles.resultList}>
              {results.map((result, index) => (
                <li
                  key={result.stock.id}
                  ref={index === selectedIndex ? selectedItemRef : null}
                  className={`${styles.resultItem} ${
                    index === selectedIndex ? styles.selected : ''
                  }`}
                  onClick={() => handleSelectStock(result.stock)}
                  onMouseEnter={() => {
                    setSelectedIndex(index);
                    setHighlightedResult(result);
                  }}
                  role="option"
                  aria-selected={index === selectedIndex}
                >
                  <div className={styles.itemContent}>
                    <div className={styles.itemLeft}>
                      <span className={styles.companyName}>
                        {result.stock.company_name}
                      </span>

                      {showStockCode && (
                        <span className={styles.stockCode}>
                          {result.stock.stock_code}
                        </span>
                      )}
                    </div>

                    <div className={styles.itemRight}>
                      <span
                        className={styles.matchTypeBadge}
                        style={{
                          backgroundColor: getMarketColor(result.stock.market),
                        }}
                        title={`Match type: ${result.matchType}`}
                      >
                        {renderMatchTypeIndicator(result.matchType)}
                      </span>

                      {showMarketBadge && (
                        <span
                          className={styles.marketBadge}
                          style={{
                            backgroundColor: getMarketColor(result.stock.market),
                          }}
                        >
                          {result.stock.market}
                        </span>
                      )}
                    </div>
                  </div>

                  {result.score && (
                    <div className={styles.scoreBar}>
                      <div
                        className={styles.scoreBarFill}
                        style={{ width: `${(result.score ?? 0) * 100}%` }}
                      />
                    </div>
                  )}
                </li>
              ))}
            </ul>
          ) : query.length >= 2 ? (
            <div className={styles.noResults}>
              <p>검색 결과가 없습니다.</p>
              <p className={styles.noResultsHint}>
                다른 회사명이나 종목코드를 시도해보세요.
              </p>
            </div>
          ) : (
            <div className={styles.noResults}>
              <p>최소 2자 이상 입력하세요.</p>
            </div>
          )}
        </div>
      )}

      {error && (
        <div className={styles.errorMessage} role="alert">
          <span className={styles.errorIcon}>⚠</span> {error}
        </div>
      )}

      {isInitialized && !error && (
        <div className={styles.helpText}>
          💡 회사명, 종목코드(예: 005930), 또는 초성(예: ㅅㅅ)으로 검색 가능합니다.
        </div>
      )}
    </div>
  );
}

/**
 * Minimal version of the autocomplete component
 */
export function StockSearchAutocompleteMinimal({
  onSelectStock,
}: {
  onSelectStock?: (stock: Stock) => void;
}) {
  return (
    <StockSearchAutocomplete
      onSelectStock={onSelectStock}
      showMarketBadge={false}
      showStockCode={false}
    />
  );
}

export default StockSearchAutocomplete;

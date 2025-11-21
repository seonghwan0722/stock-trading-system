# Open DART Financial Analysis - UI/UX Design System

## 1. Design Overview

### 1.1 Design Philosophy
- **User-Centered**: Financial professionals need quick access to accurate data
- **Information Hierarchy**: Progressive disclosure - overview first, details on demand
- **Data Density**: Balance between comprehensive data and readability
- **Trust & Accuracy**: Clear sourcing, timestamps, and data validation indicators

### 1.2 Integration Strategy
The DART Financial Analysis feature integrates as a primary navigation item in the stock trading dashboard:

```
Navigation Structure:
- Dashboard (Home)
- 시장 현황 (Market Overview)
- 내 포트폴리오 (My Portfolio)
+ 재무 분석 (Financial Analysis) ← NEW FEATURE
- 뉴스 & 리서치 (News & Research)
- 설정 (Settings)
```

---

## 2. Color Scheme for Financial Data

### 2.1 Primary Colors
```css
--primary-blue: #2563EB;        /* Main brand color, CTAs */
--primary-dark: #1E40AF;        /* Hover states */
--primary-light: #DBEAFE;       /* Backgrounds, highlights */
```

### 2.2 Financial Data Colors
```css
/* Performance Indicators */
--positive-green: #10B981;      /* Positive growth, profits */
--positive-light: #D1FAE5;      /* Positive backgrounds */
--negative-red: #EF4444;        /* Negative growth, losses */
--negative-light: #FEE2E2;      /* Negative backgrounds */
--neutral-gray: #6B7280;        /* No change, neutral data */

/* Warning & Status */
--warning-amber: #F59E0B;       /* Caution, needs attention */
--warning-light: #FEF3C7;       /* Warning backgrounds */
--info-blue: #3B82F6;           /* Information, tooltips */
--success-green: #059669;       /* Confirmed, validated */

/* Data Visualization */
--chart-primary: #2563EB;
--chart-secondary: #8B5CF6;
--chart-tertiary: #EC4899;
--chart-quaternary: #F59E0B;
--chart-quinary: #10B981;
```

### 2.3 Neutral Palette
```css
--gray-50: #F9FAFB;            /* Page background */
--gray-100: #F3F4F6;           /* Card backgrounds */
--gray-200: #E5E7EB;           /* Borders, dividers */
--gray-300: #D1D5DB;           /* Disabled states */
--gray-600: #4B5563;           /* Secondary text */
--gray-900: #111827;           /* Primary text */
```

---

## 3. Typography Guidelines

### 3.1 Font Stack
```css
/* Primary Font (Korean + Latin) */
font-family: 'Pretendard', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

/* Numeric Font (Tabular figures for financial data) */
font-family-numeric: 'Inter', 'SF Mono', 'Consolas', monospace;
font-variant-numeric: tabular-nums;
```

### 3.2 Type Scale
```css
/* Headers */
--text-h1: 32px / 40px, font-weight: 700;  /* Page title */
--text-h2: 24px / 32px, font-weight: 600;  /* Section headers */
--text-h3: 20px / 28px, font-weight: 600;  /* Card headers */
--text-h4: 16px / 24px, font-weight: 600;  /* Sub-headers */

/* Body Text */
--text-body-lg: 16px / 24px, font-weight: 400;  /* Primary content */
--text-body: 14px / 20px, font-weight: 400;     /* Default text */
--text-body-sm: 12px / 16px, font-weight: 400;  /* Captions, labels */

/* Financial Data */
--text-data-lg: 24px / 32px, font-weight: 600;  /* Key metrics */
--text-data: 16px / 24px, font-weight: 500;     /* Table data */
--text-data-sm: 14px / 20px, font-weight: 500;  /* Small numbers */
```

---

## 4. Component Specifications

### 4.1 Search Bar Component

#### Visual Design
```
┌─────────────────────────────────────────────────────────────────┐
│ 🔍  삼성전자, Samsung, 005930...           [x]  [최근 검색 ▼]  │
└─────────────────────────────────────────────────────────────────┘
     ↓ (Autocomplete dropdown appears after 2+ characters)
┌─────────────────────────────────────────────────────────────────┐
│ 검색 결과 (5)                                                    │
├─────────────────────────────────────────────────────────────────┤
│ 📊 삼성전자                                       005930 | 유가증권│
│    Samsung Electronics Co., Ltd.                               │
├─────────────────────────────────────────────────────────────────┤
│ 📊 삼성전자우                                     005935 | 유가증권│
│    Samsung Electronics Preferred                               │
├─────────────────────────────────────────────────────────────────┤
│ 최근 검색                                                         │
├─────────────────────────────────────────────────────────────────┤
│ ⏱ 현대자동차 (005380)                              2시간 전      │
│ ⏱ NAVER (035420)                                  1일 전        │
└─────────────────────────────────────────────────────────────────┘
```

#### Component Specs
```typescript
interface SearchBarProps {
  placeholder: string;
  onSearch: (query: string) => void;
  onSelect: (company: CompanyInfo) => void;
  recentSearches: CompanyInfo[];
  popularStocks: CompanyInfo[];
}

interface CompanyInfo {
  code: string;           // "005930"
  name: string;           // "삼성전자"
  nameEn: string;         // "Samsung Electronics"
  marketType: string;     // "유가증권" | "코스닥"
  corpCode: string;       // DART corp_code
}
```

#### Behavior
- **Min Characters**: 2 (trigger autocomplete)
- **Debounce**: 300ms
- **Max Results**: 10 companies
- **Fuzzy Match**: Korean (초성), English, numeric codes
- **Keyboard Navigation**: Arrow keys, Enter to select, Esc to close
- **Recent Searches**: Max 10, stored in localStorage
- **Sticky Position**: Fixed on scroll

#### States
1. **Default**: Gray border, placeholder text
2. **Focus**: Blue border (--primary-blue), dropdown appears
3. **Loading**: Spinner icon, "검색 중..."
4. **Results**: Dropdown with results
5. **No Results**: "검색 결과가 없습니다"
6. **Error**: Red border, error message below

---

### 4.2 Company Header Component

#### Visual Design
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  [Logo]  삼성전자 (005930)                          ⭐ 즐겨찾기  📤 내보내기 │
│          Samsung Electronics Co., Ltd.                                       │
│          유가증권 | 반도체 제조업                                              │
│                                                                              │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐             │
│  │ 시가총액       │ 상장주식수     │ 최근 분기     │ 데이터 기준일  │             │
│  │ 456.7조원     │ 5.97억주      │ 2024 Q3      │ 2024.09.30   │             │
│  └──────────────┴──────────────┴──────────────┴──────────────┘             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Component Specs
```typescript
interface CompanyHeaderProps {
  company: CompanyInfo;
  marketCap: string;
  listedShares: string;
  latestQuarter: string;
  dataDate: string;
  isFavorite: boolean;
  onToggleFavorite: () => void;
  onExport: () => void;
}
```

#### Behavior
- **Sticky Header**: Remains visible on scroll
- **Logo Fallback**: Display first character if no logo
- **Favorite Toggle**: Star icon with animation
- **Export Menu**: Dropdown (Excel, CSV, PDF, Print)

---

### 4.3 Navigation Tabs Component

#### Visual Design
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  [개요] [재무상태표] [손익계산서] [현금흐름표] [재무비율] [비교분석]          │
│   ▔▔▔                                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Tab Definitions
1. **개요 (Overview)**: Dashboard with key metrics
2. **재무상태표 (Balance Sheet)**: Assets, liabilities, equity
3. **손익계산서 (Income Statement)**: Revenue, expenses, profit
4. **현금흐름표 (Cash Flow)**: Operating, investing, financing
5. **재무비율 (Financial Ratios)**: Profitability, efficiency, liquidity
6. **비교분석 (Comparison)**: Multi-company comparison

#### Component Specs
```typescript
interface TabNavigationProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  tabs: Tab[];
}

type TabType = 'overview' | 'balance' | 'income' | 'cashflow' | 'ratios' | 'comparison';

interface Tab {
  id: TabType;
  label: string;
  icon?: React.ReactNode;
  badge?: number;  // Notification count
}
```

#### Behavior
- **Active State**: Bottom border, bold text
- **Hover State**: Background color change
- **Mobile**: Horizontal scroll, swipe gesture
- **URL Sync**: Tab state in URL query params

---

### 4.4 Date Range Selector

#### Visual Design
```
┌────────────────────────────────────────────────────────────┐
│  기간 선택:  [1년 ▼]  [2024 Q3 ▼]  [2023 Q3 ▼]  [비교 +]  │
└────────────────────────────────────────────────────────────┘
```

#### Presets
- 1년 (1 Year) - 4 quarters
- 3년 (3 Years) - 12 quarters
- 5년 (5 Years) - 20 quarters
- 전체 (All) - All available data
- 사용자 지정 (Custom) - Date picker

#### Component Specs
```typescript
interface DateRangeSelectorProps {
  startDate: Date;
  endDate: Date;
  preset: 'year' | '3years' | '5years' | 'all' | 'custom';
  onRangeChange: (start: Date, end: Date) => void;
  availablePeriods: Period[];
}

interface Period {
  year: number;
  quarter: 1 | 2 | 3 | 4;
  reportDate: Date;
}
```

---

### 4.5 Metric Card Component

#### Visual Design
```
┌─────────────────────────────────────────────┐
│ 총 자산 (Total Assets)               [i]   │
│                                             │
│ 456,789억원                         ↑ 8.3% │
│                                             │
│ ▂▃▅▆█ (Sparkline chart)                    │
│                                             │
│ 전분기: 422,156억원 | 전년 동기: 398,234억원  │
└─────────────────────────────────────────────┘
```

#### Component Specs
```typescript
interface MetricCardProps {
  title: string;
  titleEn?: string;
  value: number;
  unit: string;
  changePercent?: number;
  trend?: number[];           // Sparkline data
  previousPeriod?: number;
  previousYear?: number;
  info?: string;              // Tooltip text
  category: MetricCategory;
  priority: 'high' | 'medium' | 'low';
}

type MetricCategory = 'asset' | 'liability' | 'equity' | 'revenue' | 'expense' | 'cashflow' | 'ratio';
```

#### Behavior
- **Hover**: Elevation shadow, tooltip appears
- **Click**: Expand to detail view with chart
- **Color Coding**:
  - Green for positive growth
  - Red for negative growth
  - Contextual (e.g., debt decrease = good)

---

### 4.6 Data Table Component

#### Visual Design
```
┌───────────────────────────────────────────────────────────────────────────────┐
│ 재무상태표 (Balance Sheet)                              단위: 억원             │
├───────────────────────┬──────────┬──────────┬──────────┬──────────┬─────────┤
│ 계정과목               │ 2024 Q3  │ 2024 Q2  │ 2024 Q1  │ 2023 Q4  │ YoY %   │
├───────────────────────┼──────────┼──────────┼──────────┼──────────┼─────────┤
│ [자산]                │          │          │          │          │         │
│   유동자산            │ 234,567  │ 228,901  │ 223,456  │ 218,234  │ ↑ 7.5% │
│     현금 및 현금성자산│  45,678  │  43,210  │  41,234  │  39,876  │ ↑ 14.5%│
│     단기금융상품      │  89,123  │  87,456  │  85,789  │  84,123  │ ↑ 5.9% │
│   비유동자산          │ 222,222  │ 218,765  │ 215,432  │ 212,098  │ ↑ 4.8% │
├───────────────────────┼──────────┼──────────┼──────────┼──────────┼─────────┤
│ 자산총계              │ 456,789  │ 447,666  │ 438,888  │ 430,332  │ ↑ 6.1% │
└───────────────────────┴──────────┴──────────┴──────────┴──────────┴─────────┘
```

#### Component Specs
```typescript
interface DataTableProps {
  title: string;
  unit: string;
  columns: TableColumn[];
  rows: TableRow[];
  expandable?: boolean;
  sortable?: boolean;
  exportable?: boolean;
}

interface TableColumn {
  id: string;
  label: string;
  period?: Period;
  align: 'left' | 'right' | 'center';
  format?: (value: number) => string;
}

interface TableRow {
  id: string;
  label: string;
  labelEn?: string;
  indent: number;              // 0, 1, 2 for hierarchy
  values: (number | null)[];
  isHeader?: boolean;
  isBold?: boolean;
  isExpandable?: boolean;
  children?: TableRow[];
}
```

#### Behavior
- **Sorting**: Click column header to sort
- **Expansion**: Click row to expand/collapse children
- **Hover**: Highlight entire row
- **Sticky Header**: Column headers fixed on scroll
- **Sticky Column**: First column (labels) fixed on horizontal scroll
- **Number Format**:
  - Comma separators: 123,456
  - Negative in red with parentheses: (123,456)
  - Decimal places: 2 for ratios, 0 for amounts

---

### 4.7 Chart Components

#### 4.7.1 Trend Line Chart
```
┌─────────────────────────────────────────────────────────────┐
│ 총 자산 추이                                    [1년] [3년] │
│                                                             │
│ 500조 ┤                                            ╱───     │
│       │                                    ╱───────         │
│ 450조 ┤                            ╱───────                 │
│       │                    ╱───────                         │
│ 400조 ┤            ╱───────                                 │
│       │    ╱───────                                         │
│ 350조 ┼────┴────┴────┴────┴────┴────┴────┴────┴────        │
│        Q1   Q2   Q3   Q4   Q1   Q2   Q3   Q4   Q1          │
│        2022         2023         2024                       │
└─────────────────────────────────────────────────────────────┘
```

#### 4.7.2 Comparison Bar Chart
```
┌─────────────────────────────────────────────────────────────┐
│ 매출액 vs 영업이익                                           │
│                                                             │
│ 2024 Q3 ██████████████████████████ 75조 (매출)            │
│         ███████ 15조 (영업이익)                            │
│                                                             │
│ 2024 Q2 ████████████████████████ 73조                     │
│         ██████ 13조                                        │
│                                                             │
│ 2024 Q1 ███████████████████████ 70조                      │
│         ██████ 12조                                        │
└─────────────────────────────────────────────────────────────┘
```

#### 4.7.3 Composition Pie Chart
```
┌─────────────────────────────────────────────────────────────┐
│ 자산 구성 (2024 Q3)                                         │
│                                                             │
│            ╱───────╲                                        │
│        ╱───         ───╲       ■ 유동자산 51.4%           │
│      ╱                   ╲     ■ 유형자산 28.3%           │
│     │         51%         │    ■ 무형자산 12.7%           │
│     │                     │    ■ 기타 7.6%                │
│      ╲        29%        ╱                                 │
│        ╲───         ───╱                                   │
│            ╲───────╱                                        │
└─────────────────────────────────────────────────────────────┘
```

#### Chart Library Recommendation
- **Recharts**: React-friendly, responsive, customizable
- **Alternative**: Chart.js, D3.js for advanced visualizations

---

## 5. Page Layouts & Wireframes

### 5.1 Overview Dashboard (개요)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [HEADER: Company Info + Actions]                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ [TABS: Overview | Balance Sheet | Income | Cash Flow | Ratios | Compare]   │
├─────────────────────────────────────────────────────────────────────────────┤
│ [DATE RANGE SELECTOR]                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  핵심 재무 지표 (Key Financial Metrics)                                      │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐             │
│  │ 총 자산       │ 총 부채       │ 자본총계      │ 부채비율      │             │
│  │ 456.7조원    │ 178.3조원    │ 278.4조원    │ 64.0%        │             │
│  │ ↑ 8.3%       │ ↑ 3.2%       │ ↑ 12.1%      │ ↓ 2.8%       │             │
│  │ [sparkline]  │ [sparkline]  │ [sparkline]  │ [sparkline]  │             │
│  └──────────────┴──────────────┴──────────────┴──────────────┘             │
│                                                                              │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐             │
│  │ 매출액        │ 영업이익      │ 당기순이익    │ 영업이익률    │             │
│  │ 75.2조원     │ 15.8조원     │ 12.3조원     │ 21.0%        │             │
│  │ ↑ 5.6%       │ ↑ 18.3%      │ ↑ 22.5%      │ ↑ 12.0%      │             │
│  │ [sparkline]  │ [sparkline]  │ [sparkline]  │ [sparkline]  │             │
│  └──────────────┴──────────────┴──────────────┴──────────────┘             │
│                                                                              │
│  재무 성과 추이 (Financial Performance Trends)                               │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │                                                              │           │
│  │  [LINE CHART: Revenue, Operating Income, Net Income]        │           │
│  │                                                              │           │
│  │                                                              │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                              │
│  ┌───────────────────────────────┬─────────────────────────────┐           │
│  │ 자산 구성                      │ 수익성 지표                  │           │
│  │                               │                             │           │
│  │ [PIE CHART]                   │ [BAR CHART]                 │           │
│  │                               │                             │           │
│  └───────────────────────────────┴─────────────────────────────┘           │
│                                                                              │
│  주요 재무비율 요약 (Key Financial Ratios)                                   │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐             │
│  │ ROE          │ ROA          │ 유동비율      │ 당좌비율      │             │
│  │ 12.5%        │ 8.3%         │ 178.3%       │ 142.7%       │             │
│  └──────────────┴──────────────┴──────────────┴──────────────┘             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Layout Grid
- **Container**: Max-width 1440px, centered
- **Grid**: 12 columns, 24px gutter
- **Metric Cards**: 3 or 4 per row (responsive)
- **Charts**: Full width or 2-column layout

---

### 5.2 Balance Sheet View (재무상태표)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [HEADER + TABS + DATE SELECTOR]                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  재무상태표 (Balance Sheet)                                                  │
│                                                                              │
│  ┌─────────────┬─────────────┐  [전체 보기] [표 형식] [차트 형식] [📥 다운로드]│
│  │ 요약 보기    │ 상세 보기   │                                             │
│  │  (선택됨)   │             │                                             │
│  └─────────────┴─────────────┘                                             │
│                                                                              │
│  [DATA TABLE - as specified in 4.6]                                         │
│                                                                              │
│  자산 추이 그래프                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │ [STACKED AREA CHART: Current Assets, Non-current Assets]    │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                              │
│  ┌───────────────────────────────┬─────────────────────────────┐           │
│  │ 자산 구성 비율                 │ 부채/자본 구조               │           │
│  │ [PIE CHART]                   │ [STACKED BAR CHART]         │           │
│  └───────────────────────────────┴─────────────────────────────┘           │
│                                                                              │
│  ℹ️ 데이터 출처: 금융감독원 전자공시시스템 (DART)                            │
│  ℹ️ 기준 회계기준: K-IFRS 연결재무제표                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 15-20 Balance Sheet Metrics
**자산 (Assets)**
1. 유동자산 (Current Assets)
2. 현금 및 현금성자산 (Cash and Cash Equivalents)
3. 단기금융상품 (Short-term Financial Instruments)
4. 매출채권 (Trade Receivables)
5. 재고자산 (Inventories)
6. 비유동자산 (Non-current Assets)
7. 유형자산 (Property, Plant & Equipment)
8. 무형자산 (Intangible Assets)
9. 투자자산 (Investment Assets)
10. 자산총계 (Total Assets)

**부채 (Liabilities)**
11. 유동부채 (Current Liabilities)
12. 단기차입금 (Short-term Borrowings)
13. 매입채무 (Trade Payables)
14. 비유동부채 (Non-current Liabilities)
15. 장기차입금 (Long-term Borrowings)
16. 부채총계 (Total Liabilities)

**자본 (Equity)**
17. 자본금 (Capital Stock)
18. 이익잉여금 (Retained Earnings)
19. 자본총계 (Total Equity)
20. 부채비율 (Debt-to-Equity Ratio)

---

### 5.3 Income Statement View (손익계산서)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [HEADER + TABS + DATE SELECTOR]                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  손익계산서 (Income Statement)                                               │
│                                                                              │
│  핵심 지표                                                                    │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐             │
│  │ 매출액        │ 영업이익      │ 당기순이익    │ EPS          │             │
│  │ 75.2조원     │ 15.8조원     │ 12.3조원     │ 65,432원     │             │
│  │ ↑ 5.6%       │ ↑ 18.3%      │ ↑ 22.5%      │ ↑ 19.8%      │             │
│  └──────────────┴──────────────┴──────────────┴──────────────┘             │
│                                                                              │
│  [DATA TABLE]                                                                │
│                                                                              │
│  수익성 분석                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │ [WATERFALL CHART: Revenue → COGS → Operating Exp → Net]    │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                              │
│  ┌───────────────────────────────┬─────────────────────────────┐           │
│  │ 수익 추이                      │ 이익률 추이                  │           │
│  │ [MULTI-LINE CHART]            │ [LINE CHART]                │           │
│  └───────────────────────────────┴─────────────────────────────┘           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 15-20 Income Statement Metrics
**수익 (Revenue)**
1. 매출액 (Revenue / Sales)
2. 제품 매출 (Product Sales)
3. 용역 매출 (Service Revenue)

**비용 (Expenses)**
4. 매출원가 (Cost of Goods Sold)
5. 매출총이익 (Gross Profit)
6. 판매비와관리비 (Selling & Administrative Expenses)
7. 연구개발비 (R&D Expenses)
8. 영업이익 (Operating Income)
9. 금융수익 (Finance Income)
10. 금융비용 (Finance Costs)
11. 기타수익 (Other Income)
12. 기타비용 (Other Expenses)

**순이익 (Net Income)**
13. 법인세비용차감전순이익 (Income Before Tax)
14. 법인세비용 (Income Tax Expense)
15. 당기순이익 (Net Income)
16. 지배기업 소유주지분 (Profit Attributable to Owners)

**수익성 지표 (Profitability Metrics)**
17. 매출총이익률 (Gross Profit Margin)
18. 영업이익률 (Operating Profit Margin)
19. 순이익률 (Net Profit Margin)
20. 주당순이익 (EPS - Earnings Per Share)

---

### 5.4 Cash Flow View (현금흐름표)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [HEADER + TABS + DATE SELECTOR]                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  현금흐름표 (Cash Flow Statement)                                            │
│                                                                              │
│  핵심 현금흐름                                                                │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐             │
│  │ 영업활동      │ 투자활동      │ 재무활동      │ 현금증감      │             │
│  │ +18.3조원    │ -12.5조원    │ -3.2조원     │ +2.6조원     │             │
│  │ ↑ 12.3%      │ ↓ 8.7%       │ ↓ 15.2%      │ ↑ 45.8%      │             │
│  └──────────────┴──────────────┴──────────────┴──────────────┘             │
│                                                                              │
│  [DATA TABLE]                                                                │
│                                                                              │
│  현금흐름 시각화                                                              │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │ [SANKEY DIAGRAM: Cash flow between activities]              │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                              │
│  ┌───────────────────────────────┬─────────────────────────────┐           │
│  │ 분기별 현금흐름                │ 누적 잉여현금흐름            │           │
│  │ [STACKED BAR CHART]           │ [AREA CHART]                │           │
│  └───────────────────────────────┴─────────────────────────────┘           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 10-15 Cash Flow Metrics
**영업활동 현금흐름 (Operating Activities)**
1. 영업활동 현금흐름 (Cash Flow from Operating Activities)
2. 당기순이익 (Net Income)
3. 현금유출이 없는 비용 (Non-cash Expenses - Depreciation, Amortization)
4. 운전자본 변동 (Changes in Working Capital)

**투자활동 현금흐름 (Investing Activities)**
5. 투자활동 현금흐름 (Cash Flow from Investing Activities)
6. 유형자산 취득 (Purchase of PP&E)
7. 무형자산 취득 (Purchase of Intangible Assets)
8. 투자자산 취득/처분 (Investment Activities)

**재무활동 현금흐름 (Financing Activities)**
9. 재무활동 현금흐름 (Cash Flow from Financing Activities)
10. 차입금 증감 (Net Change in Borrowings)
11. 배당금 지급 (Dividends Paid)

**현금 변동 (Cash Changes)**
12. 현금의 증가(감소) (Net Increase/Decrease in Cash)
13. 기초 현금 (Cash at Beginning)
14. 기말 현금 (Cash at End)
15. 잉여현금흐름 (Free Cash Flow)

---

### 5.5 Financial Ratios View (재무비율)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [HEADER + TABS + DATE SELECTOR]                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  재무비율 분석 (Financial Ratio Analysis)                                    │
│                                                                              │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐                │
│  │ 수익성       │ 안정성       │ 활동성       │ 성장성       │                │
│  │ (선택됨)    │             │             │             │                │
│  └─────────────┴─────────────┴─────────────┴─────────────┘                │
│                                                                              │
│  수익성 지표 (Profitability Ratios)                                          │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │ ROE (자기자본이익률)                                    [i]  │           │
│  │ 12.5%                                              ↑ 2.3%p  │           │
│  │ ━━━━━━━━━━━━━━━━━░░░░░░░░ 우수                             │           │
│  │ 업종 평균: 9.8% | 상위 25%: 15.2%                            │           │
│  │ [LINE CHART: 5-year trend]                                  │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │ ROA (총자산이익률)                                     [i]  │           │
│  │ 8.3%                                               ↑ 1.5%p  │           │
│  │ ━━━━━━━━━━━━━░░░░░░░░░░░░░░ 양호                           │           │
│  │ 업종 평균: 6.5% | 상위 25%: 10.1%                            │           │
│  │ [LINE CHART]                                                │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                              │
│  비율 비교                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │ [RADAR CHART: Compare all ratios with industry average]     │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 5-10 Financial Ratios per Category

**수익성 지표 (Profitability)**
1. ROE - 자기자본이익률 (Return on Equity)
2. ROA - 총자산이익률 (Return on Assets)
3. ROIC - 투하자본이익률 (Return on Invested Capital)
4. 매출총이익률 (Gross Profit Margin)
5. 영업이익률 (Operating Profit Margin)
6. 순이익률 (Net Profit Margin)

**안정성 지표 (Stability/Solvency)**
7. 부채비율 (Debt-to-Equity Ratio)
8. 유동비율 (Current Ratio)
9. 당좌비율 (Quick Ratio)
10. 이자보상배율 (Interest Coverage Ratio)
11. 자기자본비율 (Equity Ratio)

**활동성 지표 (Activity/Efficiency)**
12. 총자산회전율 (Total Asset Turnover)
13. 재고자산회전율 (Inventory Turnover)
14. 매출채권회전율 (Receivables Turnover)
15. 매입채무회전율 (Payables Turnover)

**성장성 지표 (Growth)**
16. 매출액증가율 (Revenue Growth Rate)
17. 영업이익증가율 (Operating Income Growth Rate)
18. 순이익증가율 (Net Income Growth Rate)
19. 자산증가율 (Asset Growth Rate)
20. EPS 증가율 (EPS Growth Rate)

---

### 5.6 Comparison View (비교분석)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [HEADER + TABS]                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  기업 비교 분석 (Company Comparison)                                          │
│                                                                              │
│  선택된 기업:                                                                 │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐             │
│  │ [삼성전자]   │ [SK하이닉스] │ [+ 기업 추가]│              │             │
│  │ 005930 [x]   │ 000660 [x]   │              │              │             │
│  └──────────────┴──────────────┴──────────────┴──────────────┘             │
│                                                                              │
│  비교 기간: [2024 Q3 ▼]                                                      │
│                                                                              │
│  [전체] [재무상태표] [손익계산서] [현금흐름] [재무비율]                        │
│                                                                              │
│  핵심 지표 비교                                                               │
│  ┌──────────────────────────────────────────────────────────┐              │
│  │ 지표          삼성전자      SK하이닉스    업종평균        │              │
│  ├──────────────────────────────────────────────────────────┤              │
│  │ 총자산       456.7조       98.3조       127.5조          │              │
│  │ 매출액        75.2조       18.4조        23.6조          │              │
│  │ 영업이익      15.8조        4.2조         5.1조          │              │
│  │ ROE          12.5% ●       8.3% ●       9.8% ●          │              │
│  │ 부채비율      64.0% ●      78.5% ●      72.3% ●          │              │
│  └──────────────────────────────────────────────────────────┘              │
│                                                                              │
│  시각적 비교                                                                  │
│  ┌───────────────────────────────┬─────────────────────────────┐           │
│  │ 규모 비교 (Bar Chart)         │ 수익성 비교 (Radar Chart)    │           │
│  │ [GROUPED BAR CHART]           │ [RADAR CHART]               │           │
│  └───────────────────────────────┴─────────────────────────────┘           │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │ 성장 추이 비교 (Multi-line Chart)                            │           │
│  │ [MULTI-LINE CHART: 3 companies over time]                   │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Interaction Patterns

### 6.1 Loading States

#### Skeleton Screens
```
┌─────────────────────────────────────────────────────────────┐
│ ░░░░░░░░░░░░░░░░░░░ (Company name loading)                  │
│                                                             │
│ ┌──────────────┬──────────────┬──────────────┐             │
│ │ ░░░░░░░░░░  │ ░░░░░░░░░░  │ ░░░░░░░░░░  │             │
│ │ ░░░░░░      │ ░░░░░░      │ ░░░░░░      │             │
│ │ ░░░░░░░░    │ ░░░░░░░░    │ ░░░░░░░░    │             │
│ └──────────────┴──────────────┴──────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

#### Loading Spinner
- Position: Center of loading container
- Size: 40px diameter
- Animation: Smooth rotation, 1s duration
- Color: --primary-blue with opacity

#### Progressive Loading
1. **Phase 1**: Company header and basic info (fast)
2. **Phase 2**: Key metrics (medium)
3. **Phase 3**: Charts and detailed tables (slower)

### 6.2 Error States

#### Error Message Pattern
```
┌─────────────────────────────────────────────────────────────┐
│  ⚠️ 데이터를 불러올 수 없습니다                              │
│                                                             │
│  일시적인 오류가 발생했습니다.                               │
│  잠시 후 다시 시도해주세요.                                  │
│                                                             │
│  [다시 시도]  [고객센터 문의]                                │
│                                                             │
│  오류 코드: DART_API_TIMEOUT_500                            │
└─────────────────────────────────────────────────────────────┘
```

#### Error Types
1. **Network Error**: Connection failed, retry button
2. **API Error**: DART API unavailable, show status
3. **No Data**: Company has no financial reports filed
4. **Invalid Search**: No matching companies found
5. **Permission Error**: Subscription required message

### 6.3 Empty States

#### No Data Available
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                  📊                                         │
│                                                             │
│  재무 데이터가 없습니다                                      │
│                                                             │
│  이 기업은 아직 재무제표를 공시하지 않았습니다.              │
│  상장 예정 기업이거나 공시가 지연되었을 수 있습니다.         │
│                                                             │
│  [다른 기업 검색]                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.4 Tooltips

#### Metric Explanation Tooltip
```
┌─────────────────────────────────────────┐
│ ROE (자기자본이익률)                     │
├─────────────────────────────────────────┤
│ 기업이 자기자본을 활용하여 얼마나       │
│ 효율적으로 이익을 창출했는지 나타내는   │
│ 지표입니다.                             │
│                                         │
│ 계산식: 당기순이익 / 자기자본 × 100     │
│                                         │
│ 높을수록 좋음 | 업종별 차이 있음        │
└─────────────────────────────────────────┘
```

#### Tooltip Behavior
- **Trigger**: Hover on [i] icon or metric label
- **Position**: Above element, adjust if near edge
- **Delay**: 500ms hover delay
- **Animation**: Fade in 200ms
- **Close**: Mouse leave, click outside

### 6.5 Responsive Behavior

#### Breakpoints
```css
--breakpoint-mobile: 640px;      /* Mobile phones */
--breakpoint-tablet: 768px;      /* Tablets */
--breakpoint-desktop: 1024px;    /* Desktop */
--breakpoint-wide: 1440px;       /* Wide screens */
```

#### Mobile Adaptations (< 768px)
1. **Search Bar**: Full width, simplified dropdown
2. **Metric Cards**: 1 per row, vertical stacking
3. **Tables**: Horizontal scroll, sticky first column
4. **Charts**: Simplified, reduced data points
5. **Tabs**: Horizontal scroll, swipe gesture
6. **Navigation**: Bottom sheet or hamburger menu

#### Tablet (768px - 1024px)
1. **Metric Cards**: 2 per row
2. **Charts**: Side-by-side reduced to single column
3. **Tables**: Better readability, larger touch targets

---

## 7. Accessibility Guidelines

### 7.1 WCAG 2.1 AA Compliance

#### Color Contrast
- **Text**: Minimum 4.5:1 ratio (normal), 3:1 (large text)
- **Interactive**: 3:1 for UI components
- **Success**: Pass AAA where possible

#### Contrast Examples
```
✓ Black text on white: 21:1
✓ --gray-900 on white: 16.2:1
✓ --primary-blue on white: 8.6:1
✓ --positive-green on white: 4.8:1
✗ --gray-300 on white: 2.8:1 (Use for decorative only)
```

### 7.2 Keyboard Navigation

#### Tab Order
1. Skip to main content link
2. Search bar
3. Company selector
4. Tab navigation
5. Date range selector
6. Interactive cards/tables
7. Action buttons (export, favorite)

#### Keyboard Shortcuts
```
Ctrl/Cmd + K     : Focus search bar
Ctrl/Cmd + E     : Export data
Tab              : Navigate forward
Shift + Tab      : Navigate backward
Enter            : Activate/select
Escape           : Close modals/dropdowns
Arrow Keys       : Navigate tabs, table cells
Space            : Toggle checkboxes, expand rows
```

#### Focus Indicators
```css
:focus-visible {
  outline: 2px solid var(--primary-blue);
  outline-offset: 2px;
  border-radius: 4px;
}
```

### 7.3 Screen Reader Support

#### ARIA Labels
```html
<!-- Search bar -->
<input
  aria-label="기업 검색"
  aria-describedby="search-help"
  aria-autocomplete="list"
  aria-controls="search-results"
/>

<!-- Metric card -->
<div role="article" aria-labelledby="metric-title">
  <h3 id="metric-title">총 자산</h3>
  <p aria-label="456조 7890억원, 전분기 대비 8.3% 증가">
    456.7조원 <span aria-hidden="true">↑ 8.3%</span>
  </p>
</div>

<!-- Data table -->
<table role="table" aria-label="재무상태표">
  <thead>
    <tr>
      <th scope="col">계정과목</th>
      <th scope="col">2024 3분기</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">유동자산</th>
      <td>234,567억원</td>
    </tr>
  </tbody>
</table>

<!-- Chart -->
<div role="img" aria-label="총 자산 추이 그래프. 2023년 1분기 398조원에서 2024년 3분기 456조원으로 증가">
  <canvas><!-- Chart rendered here --></canvas>
</div>
```

#### Live Regions
```html
<!-- Search results -->
<div role="status" aria-live="polite" aria-atomic="true">
  5개 검색 결과
</div>

<!-- Data loading -->
<div role="alert" aria-live="assertive">
  데이터를 불러오는 중입니다...
</div>

<!-- Error messages -->
<div role="alert" aria-live="assertive">
  데이터를 불러올 수 없습니다.
</div>
```

### 7.4 Text Alternatives

#### Icons
- All icons must have text labels or aria-labels
- Decorative icons: `aria-hidden="true"`
- Functional icons: `aria-label="설명"`

#### Charts & Visualizations
- Provide data table alternative
- Screen reader description of trends
- Download option for raw data

#### Images
- Company logos: `alt="[회사명] 로고"`
- Decorative images: `alt=""` or `aria-hidden="true"`

---

## 8. Animation & Motion

### 8.1 Animation Principles
- **Purpose**: Provide feedback, guide attention, smooth transitions
- **Duration**: 200-400ms for UI, 400-600ms for page transitions
- **Easing**: Use CSS easing functions

```css
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
```

### 8.2 Common Animations

#### Fade In
```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.fade-in {
  animation: fadeIn 300ms ease-out;
}
```

#### Slide Up
```css
@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.slide-up {
  animation: slideUp 400ms ease-out;
}
```

#### Skeleton Loading
```css
@keyframes shimmer {
  0% { background-position: -1000px 0; }
  100% { background-position: 1000px 0; }
}

.skeleton {
  background: linear-gradient(
    90deg,
    var(--gray-100) 25%,
    var(--gray-200) 50%,
    var(--gray-100) 75%
  );
  background-size: 2000px 100%;
  animation: shimmer 2s infinite linear;
}
```

### 8.3 Reduced Motion
```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 9. Export & Print Functionality

### 9.1 Export Options

#### Export Menu
```
┌─────────────────────┐
│ 📤 내보내기         │
├─────────────────────┤
│ 📊 Excel (.xlsx)    │
│ 📄 CSV              │
│ 📑 PDF              │
│ 🖨️ 인쇄             │
│ 🔗 링크 복사        │
└─────────────────────┘
```

#### Export Settings Modal
```
┌─────────────────────────────────────────────────────────┐
│ 데이터 내보내기                                    [x]  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 형식: [Excel ▼]                                         │
│                                                         │
│ 포함 항목:                                              │
│ ☑ 기업 정보                                            │
│ ☑ 재무상태표                                           │
│ ☑ 손익계산서                                           │
│ ☑ 현금흐름표                                           │
│ ☑ 재무비율                                             │
│ ☐ 차트 (이미지)                                        │
│                                                         │
│ 기간: [2024 Q3 ▼] ~ [2023 Q1 ▼]                       │
│                                                         │
│                        [취소]  [내보내기]               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 9.2 Print Styles

```css
@media print {
  /* Hide navigation and controls */
  nav,
  .search-bar,
  .action-buttons,
  .tab-navigation {
    display: none !important;
  }

  /* Optimize for print */
  body {
    background: white;
    color: black;
    font-size: 12pt;
  }

  /* Page breaks */
  .section {
    page-break-inside: avoid;
  }

  h2, h3 {
    page-break-after: avoid;
  }

  /* Charts - convert to images or tables */
  .chart {
    max-height: 300px;
  }

  /* Tables */
  table {
    width: 100%;
    border-collapse: collapse;
  }

  th, td {
    border: 1px solid #000;
    padding: 4pt;
  }

  /* Add headers and footers */
  @page {
    margin: 1in;

    @top-right {
      content: "페이지 " counter(page) " / " counter(pages);
    }

    @bottom-left {
      content: "출처: 금융감독원 DART";
    }

    @bottom-right {
      content: "생성일: " string(print-date);
    }
  }
}
```

---

## 10. Performance Optimization

### 10.1 Data Loading Strategy

#### Lazy Loading
- Load overview first (priority)
- Defer detailed tables until tab selected
- Load charts only when visible (Intersection Observer)
- Paginate large datasets (50 rows per page)

#### Caching Strategy
```typescript
interface CacheStrategy {
  company: {
    ttl: 1 * 60 * 60 * 1000;      // 1 hour
    storage: 'memory';
  };
  financials: {
    ttl: 24 * 60 * 60 * 1000;     // 24 hours
    storage: 'localStorage';
  };
  charts: {
    ttl: 24 * 60 * 60 * 1000;     // 24 hours
    storage: 'memory';
  };
}
```

### 10.2 Rendering Optimization

#### Virtual Scrolling
- Use for tables with 100+ rows
- Render only visible rows + buffer
- Libraries: react-window, react-virtualized

#### Memoization
```typescript
// Memoize expensive calculations
const processedData = useMemo(() => {
  return calculateFinancialRatios(rawData);
}, [rawData]);

// Memoize components
const MetricCard = React.memo(({ metric, value }) => {
  // Component implementation
});
```

### 10.3 Image Optimization

#### Company Logos
- Format: WebP with PNG fallback
- Sizes: 40px, 80px, 160px (responsive)
- Lazy load: Below the fold images
- CDN: Serve from CDN if available

---

## 11. Mobile Experience

### 11.1 Mobile Navigation

#### Bottom Navigation
```
┌─────────────────────────────────────────────────────────┐
│ [Content Area]                                          │
│                                                         │
│                                                         │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  [🏠]    [📊]    [🔍]    [⭐]    [☰]                   │
│  홈      분석    검색    즐겨찾기  더보기                │
└─────────────────────────────────────────────────────────┘
```

### 11.2 Mobile-Specific Components

#### Compact Metric Cards
```
┌─────────────────────────────┐
│ 총 자산            ↑ 8.3%  │
│ 456.7조원                   │
│ ▂▃▅▆█                       │
└─────────────────────────────┘
```

#### Swipeable Tabs
- Swipe left/right to change tabs
- Visual indicator showing swipe possibility
- Smooth animation on transition

#### Collapsible Tables
```
┌─────────────────────────────────────┐
│ ▼ 유동자산         234,567억원 [>] │
├─────────────────────────────────────┤
│ ▶ 비유동자산       222,222억원 [>] │
└─────────────────────────────────────┘

(Expanded state)
┌─────────────────────────────────────┐
│ ▼ 유동자산         234,567억원      │
│   현금             45,678억원       │
│   단기금융상품     89,123억원       │
│   매출채권         34,567억원       │
│   재고자산         45,678억원       │
│   기타             19,521억원       │
└─────────────────────────────────────┘
```

### 11.3 Touch Interactions

#### Touch Targets
- Minimum size: 44x44px (iOS), 48x48px (Android)
- Spacing: 8px minimum between targets
- Visual feedback: 100ms delay, ripple effect

#### Gestures
- **Swipe**: Navigate tabs, dismiss notifications
- **Pinch**: Zoom charts (if applicable)
- **Long press**: Show context menu, copy data
- **Pull to refresh**: Reload latest data

---

## 12. Implementation Notes

### 12.1 Recommended Tech Stack

#### Frontend Framework
```
React 18+ with TypeScript
- Component reusability
- Type safety for financial data
- Large ecosystem for charts/tables
```

#### UI Component Library
```
Option 1: Ant Design
- Comprehensive table components
- Good internationalization (Korean)
- Built-in date pickers, selectors

Option 2: Material-UI (MUI)
- Modern design system
- Excellent theming support
- Good accessibility

Option 3: Custom + Headless UI
- Full design control
- Smaller bundle size
- More development effort
```

#### Chart Library
```
Recharts (Recommended)
- React-native, composable
- Good documentation
- SVG-based, responsive

Alternative: Chart.js
- More chart types
- Better performance for large datasets
- Canvas-based
```

#### Data Fetching
```
React Query (TanStack Query)
- Automatic caching
- Background refetching
- Loading/error states
- Optimistic updates
```

#### State Management
```
Zustand or Jotai (Lightweight)
- Simple API
- Good TypeScript support
- No boilerplate

Alternative: Redux Toolkit
- More structure
- DevTools
- Larger app needs
```

### 12.2 File Structure

```
src/
├── features/
│   └── dart-analysis/
│       ├── components/
│       │   ├── CompanyHeader.tsx
│       │   ├── SearchBar.tsx
│       │   ├── TabNavigation.tsx
│       │   ├── DateRangeSelector.tsx
│       │   ├── MetricCard.tsx
│       │   ├── DataTable.tsx
│       │   ├── charts/
│       │   │   ├── TrendChart.tsx
│       │   │   ├── ComparisonChart.tsx
│       │   │   └── PieChart.tsx
│       │   └── index.ts
│       ├── views/
│       │   ├── OverviewView.tsx
│       │   ├── BalanceSheetView.tsx
│       │   ├── IncomeStatementView.tsx
│       │   ├── CashFlowView.tsx
│       │   ├── RatiosView.tsx
│       │   └── ComparisonView.tsx
│       ├── hooks/
│       │   ├── useCompanySearch.ts
│       │   ├── useFinancialData.ts
│       │   ├── useFavorites.ts
│       │   └── useExport.ts
│       ├── services/
│       │   ├── dartApi.ts
│       │   ├── dataProcessing.ts
│       │   └── export.ts
│       ├── types/
│       │   ├── company.ts
│       │   ├── financial.ts
│       │   └── chart.ts
│       ├── utils/
│       │   ├── formatters.ts
│       │   ├── calculations.ts
│       │   └── validators.ts
│       ├── constants/
│       │   ├── metrics.ts
│       │   └── colors.ts
│       └── DartAnalysisPage.tsx
├── shared/
│   ├── components/
│   ├── hooks/
│   └── utils/
└── styles/
    ├── variables.css
    ├── global.css
    └── dart-analysis.css
```

### 12.3 API Integration

#### DART API Wrapper
```typescript
// src/features/dart-analysis/services/dartApi.ts

interface DartApiConfig {
  baseUrl: string;
  apiKey: string;
  timeout: number;
}

class DartApiService {
  private config: DartApiConfig;

  constructor(config: DartApiConfig) {
    this.config = config;
  }

  // Search companies
  async searchCompanies(query: string): Promise<CompanyInfo[]> {
    // Implementation
  }

  // Get financial statements
  async getFinancialStatements(
    corpCode: string,
    year: number,
    quarter: number,
    reportType: 'BS' | 'IS' | 'CF'
  ): Promise<FinancialData> {
    // Implementation
  }

  // Get company info
  async getCompanyInfo(corpCode: string): Promise<CompanyDetails> {
    // Implementation
  }
}

export default DartApiService;
```

### 12.4 Data Processing

#### Financial Calculations
```typescript
// src/features/dart-analysis/utils/calculations.ts

export const calculateFinancialRatios = (
  balanceSheet: BalanceSheetData,
  incomeStatement: IncomeStatementData
) => {
  return {
    roe: (incomeStatement.netIncome / balanceSheet.equity) * 100,
    roa: (incomeStatement.netIncome / balanceSheet.totalAssets) * 100,
    debtToEquity: (balanceSheet.totalLiabilities / balanceSheet.equity) * 100,
    currentRatio: (balanceSheet.currentAssets / balanceSheet.currentLiabilities) * 100,
    // ... more ratios
  };
};

export const calculateGrowthRate = (
  current: number,
  previous: number
): number => {
  if (previous === 0) return 0;
  return ((current - previous) / previous) * 100;
};

export const calculateYoY = (
  current: number,
  yearAgo: number
): number => {
  return calculateGrowthRate(current, yearAgo);
};
```

#### Number Formatting
```typescript
// src/features/dart-analysis/utils/formatters.ts

export const formatCurrency = (
  value: number,
  unit: 'won' | 'billion' | 'trillion' = 'billion'
): string => {
  const units = {
    won: { divisor: 1, suffix: '원' },
    billion: { divisor: 100000000, suffix: '억원' },
    trillion: { divisor: 1000000000000, suffix: '조원' },
  };

  const { divisor, suffix } = units[unit];
  const formatted = (value / divisor).toLocaleString('ko-KR', {
    maximumFractionDigits: 1,
  });

  return `${formatted}${suffix}`;
};

export const formatPercent = (
  value: number,
  decimals: number = 1
): string => {
  return `${value.toFixed(decimals)}%`;
};

export const formatChangeIndicator = (value: number): string => {
  if (value > 0) return `↑ ${formatPercent(value)}`;
  if (value < 0) return `↓ ${formatPercent(Math.abs(value))}`;
  return '─ 0%';
};
```

---

## 13. Testing Strategy

### 13.1 Unit Tests
- Test utility functions (formatters, calculations)
- Test hooks (search, data fetching)
- Test data processing logic

### 13.2 Component Tests
- Test rendering with mock data
- Test user interactions (click, type, select)
- Test accessibility (keyboard navigation, screen readers)

### 13.3 Integration Tests
- Test complete user flows
- Test API integration
- Test error handling

### 13.4 Visual Regression Tests
- Screenshot comparisons
- Responsive design verification
- Dark mode (if implemented)

---

## 14. Launch Checklist

### 14.1 Pre-Launch
- [ ] All 50+ metrics mapped from DART API
- [ ] Search functionality working (fuzzy, autocomplete)
- [ ] All 6 views implemented
- [ ] Charts rendering correctly
- [ ] Export to Excel/CSV/PDF working
- [ ] Mobile responsive (test on real devices)
- [ ] Accessibility audit (WAVE, Lighthouse)
- [ ] Performance audit (< 3s load time)
- [ ] Browser testing (Chrome, Firefox, Safari, Edge)
- [ ] Error handling implemented
- [ ] Loading states polished
- [ ] Empty states designed

### 14.2 Documentation
- [ ] User guide created
- [ ] API documentation
- [ ] Component storybook
- [ ] Metric definitions glossary
- [ ] FAQ section

### 14.3 Analytics Setup
- [ ] Page view tracking
- [ ] Search query tracking
- [ ] Export usage tracking
- [ ] Error tracking
- [ ] Performance monitoring

---

## 15. Future Enhancements

### Phase 2 Features
1. **Alerts & Notifications**
   - Set alerts for financial metric changes
   - Quarterly report release notifications

2. **Custom Reports**
   - Build custom metric combinations
   - Save and share report templates

3. **AI Insights**
   - Automated financial analysis
   - Risk indicators
   - Peer comparison recommendations

4. **Historical Analysis**
   - 10+ year trend analysis
   - Seasonality detection
   - Forecast modeling

5. **Collaboration**
   - Share analysis with team
   - Collaborative annotations
   - Discussion threads

6. **Advanced Visualizations**
   - Heat maps
   - Sankey diagrams for cash flow
   - Treemaps for portfolio composition

---

## Appendix A: Complete Metric List (50+)

### Balance Sheet Metrics (20)
1. 유동자산 (Current Assets)
2. 현금 및 현금성자산 (Cash and Cash Equivalents)
3. 단기금융상품 (Short-term Financial Instruments)
4. 매출채권 및 기타채권 (Trade and Other Receivables)
5. 재고자산 (Inventories)
6. 기타유동자산 (Other Current Assets)
7. 비유동자산 (Non-current Assets)
8. 장기금융상품 (Long-term Financial Instruments)
9. 유형자산 (Property, Plant and Equipment)
10. 무형자산 (Intangible Assets)
11. 투자부동산 (Investment Property)
12. 자산총계 (Total Assets)
13. 유동부채 (Current Liabilities)
14. 단기차입금 (Short-term Borrowings)
15. 매입채무 및 기타채무 (Trade and Other Payables)
16. 비유동부채 (Non-current Liabilities)
17. 장기차입금 (Long-term Borrowings)
18. 부채총계 (Total Liabilities)
19. 자본금 (Capital Stock)
20. 자본잉여금 (Capital Surplus)
21. 이익잉여금 (Retained Earnings)
22. 자본총계 (Total Equity)

### Income Statement Metrics (20)
23. 매출액 (Revenue)
24. 제품매출 (Product Sales)
25. 상품매출 (Merchandise Sales)
26. 용역매출 (Service Revenue)
27. 매출원가 (Cost of Sales)
28. 매출총이익 (Gross Profit)
29. 판매비와관리비 (Selling and Administrative Expenses)
30. 급여 (Salaries)
31. 연구개발비 (Research and Development)
32. 광고선전비 (Advertising)
33. 영업이익 (Operating Income)
34. 영업외수익 (Non-operating Income)
35. 이자수익 (Interest Income)
36. 영업외비용 (Non-operating Expenses)
37. 이자비용 (Interest Expense)
38. 법인세비용차감전순이익 (Income Before Tax)
39. 법인세비용 (Income Tax Expense)
40. 당기순이익 (Net Income)
41. 지배기업소유주지분 순이익 (Profit Attributable to Owners)
42. 주당순이익 (EPS)

### Cash Flow Metrics (12)
43. 영업활동 현금흐름 (Cash Flow from Operating Activities)
44. 당기순이익 (Net Income for CF)
45. 감가상각비 (Depreciation)
46. 무형자산상각비 (Amortization)
47. 운전자본 증감 (Changes in Working Capital)
48. 투자활동 현금흐름 (Cash Flow from Investing Activities)
49. 유형자산 취득 (Purchase of PP&E)
50. 투자자산 취득/처분 (Investment Activities)
51. 재무활동 현금흐름 (Cash Flow from Financing Activities)
52. 차입금 증감 (Net Borrowings)
53. 배당금 지급 (Dividends Paid)
54. 현금의 증가(감소) (Net Increase/Decrease in Cash)

### Financial Ratios (20)
55. ROE - 자기자본이익률 (Return on Equity)
56. ROA - 총자산이익률 (Return on Assets)
57. ROIC - 투하자본이익률 (Return on Invested Capital)
58. 매출총이익률 (Gross Profit Margin)
59. 영업이익률 (Operating Profit Margin)
60. 순이익률 (Net Profit Margin)
61. EBITDA 마진 (EBITDA Margin)
62. 부채비율 (Debt-to-Equity Ratio)
63. 유동비율 (Current Ratio)
64. 당좌비율 (Quick Ratio)
65. 이자보상배율 (Interest Coverage Ratio)
66. 자기자본비율 (Equity Ratio)
67. 총자산회전율 (Total Asset Turnover)
68. 재고자산회전율 (Inventory Turnover)
69. 매출채권회전율 (Receivables Turnover)
70. 매입채무회전율 (Payables Turnover)
71. 매출액증가율 (Revenue Growth Rate)
72. 영업이익증가율 (Operating Income Growth Rate)
73. 순이익증가율 (Net Income Growth Rate)
74. EPS 증가율 (EPS Growth Rate)

---

## Appendix B: Color Usage Examples

### Positive/Negative Indicators
```
Positive (Green):
- Profit increase
- Revenue growth
- Asset increase
- Debt ratio decrease
- Efficiency improvement

Negative (Red):
- Profit decrease
- Revenue decline
- Loss
- Debt increase
- Efficiency decline

Neutral (Gray):
- No change
- Non-financial data
- Informational text
```

### Chart Color Assignments
```
Primary Metrics:
- Revenue: #2563EB (Primary Blue)
- Operating Income: #10B981 (Green)
- Net Income: #8B5CF6 (Purple)

Assets/Liabilities:
- Current Assets: #3B82F6 (Blue)
- Non-current Assets: #60A5FA (Light Blue)
- Current Liabilities: #F59E0B (Amber)
- Non-current Liabilities: #FB923C (Orange)

Cash Flow:
- Operating: #10B981 (Green)
- Investing: #3B82F6 (Blue)
- Financing: #F59E0B (Amber)
```

---

## Conclusion

This comprehensive UI/UX design system provides a complete blueprint for implementing the Open DART financial analysis feature. The design prioritizes:

1. **User Efficiency**: Quick access to critical financial data
2. **Data Accuracy**: Clear sourcing and validation
3. **Visual Clarity**: Intuitive charts and tables
4. **Accessibility**: WCAG 2.1 AA compliant
5. **Responsiveness**: Mobile-first approach
6. **Performance**: Optimized loading and rendering

The modular component structure allows for iterative development and easy maintenance. Each component is designed with reusability and customization in mind.

**Next Steps**:
1. Review and approve design system
2. Create high-fidelity mockups in Figma/Sketch
3. Build component library
4. Implement feature incrementally (Overview → Details)
5. User testing and iteration
6. Launch and monitor analytics

**Questions or Clarifications**: Please reach out for any specific component details or implementation guidance.

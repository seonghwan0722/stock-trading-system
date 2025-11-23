/**
 * DART Financial Analysis - Component Specifications
 * TypeScript interfaces and component props for implementation
 */

// ============================================================================
// CORE DATA TYPES
// ============================================================================

/**
 * Company Information
 */
export interface CompanyInfo {
  code: string;              // Stock code: "005930"
  name: string;              // Korean name: "삼성전자"
  nameEn: string;            // English name: "Samsung Electronics"
  corpCode: string;          // DART corp_code: "00126380"
  marketType: MarketType;    // Market classification
  sector?: string;           // Industry sector
  logoUrl?: string;          // Company logo URL
}

export type MarketType = '유가증권' | '코스닥' | 'KONEX';

/**
 * Financial Period
 */
export interface Period {
  year: number;              // 2024
  quarter: 1 | 2 | 3 | 4;    // Quarter number
  reportDate: Date;          // Report publication date
  fiscalPeriodEnd: Date;     // Period end date
}

/**
 * Financial Data Types
 */
export type ReportType = 'BS' | 'IS' | 'CF' | 'RATIO';
export type AccountCategory = 'asset' | 'liability' | 'equity' | 'revenue' | 'expense' | 'cashflow' | 'ratio';

/**
 * Account Line Item
 */
export interface AccountItem {
  id: string;
  label: string;             // "유동자산"
  labelEn?: string;          // "Current Assets"
  accountCode: string;       // DART account code
  category: AccountCategory;
  value: number;             // Amount in base unit (won)
  indent: number;            // Hierarchy level: 0, 1, 2
  isHeader: boolean;         // True for section headers
  isBold: boolean;           // Display in bold
  children?: AccountItem[];  // Sub-items
}

/**
 * Balance Sheet Data
 */
export interface BalanceSheetData {
  period: Period;
  // Assets
  currentAssets: number;
  cash: number;
  shortTermInvestments: number;
  receivables: number;
  inventory: number;
  otherCurrentAssets: number;
  nonCurrentAssets: number;
  ppe: number;                      // Property, Plant & Equipment
  intangibleAssets: number;
  investments: number;
  totalAssets: number;

  // Liabilities
  currentLiabilities: number;
  shortTermDebt: number;
  payables: number;
  otherCurrentLiabilities: number;
  nonCurrentLiabilities: number;
  longTermDebt: number;
  totalLiabilities: number;

  // Equity
  capitalStock: number;
  capitalSurplus: number;
  retainedEarnings: number;
  totalEquity: number;

  // Additional items
  items: AccountItem[];
}

/**
 * Income Statement Data
 */
export interface IncomeStatementData {
  period: Period;
  // Revenue
  revenue: number;
  productSales: number;
  serviceSales: number;

  // Costs & Expenses
  costOfSales: number;
  grossProfit: number;
  sellingAdminExpenses: number;
  rdExpenses: number;
  operatingIncome: number;

  // Non-operating
  nonOperatingIncome: number;
  nonOperatingExpenses: number;
  interestIncome: number;
  interestExpense: number;

  // Net Income
  incomeBeforeTax: number;
  incomeTaxExpense: number;
  netIncome: number;
  eps: number;                      // Earnings Per Share

  // Additional items
  items: AccountItem[];
}

/**
 * Cash Flow Statement Data
 */
export interface CashFlowData {
  period: Period;
  // Operating Activities
  operatingCashFlow: number;
  netIncome: number;
  depreciation: number;
  amortization: number;
  workingCapitalChange: number;

  // Investing Activities
  investingCashFlow: number;
  capex: number;                    // Capital Expenditures
  investmentPurchase: number;
  investmentSales: number;

  // Financing Activities
  financingCashFlow: number;
  debtIssuance: number;
  debtRepayment: number;
  dividendsPaid: number;

  // Net Change
  netCashChange: number;
  beginningCash: number;
  endingCash: number;
  freeCashFlow: number;             // Operating CF - Capex

  // Additional items
  items: AccountItem[];
}

/**
 * Financial Ratios
 */
export interface FinancialRatios {
  period: Period;

  // Profitability
  roe: number;                      // Return on Equity (%)
  roa: number;                      // Return on Assets (%)
  roic: number;                     // Return on Invested Capital (%)
  grossProfitMargin: number;        // %
  operatingProfitMargin: number;    // %
  netProfitMargin: number;          // %
  ebitdaMargin: number;             // %

  // Stability/Solvency
  debtToEquity: number;             // %
  currentRatio: number;             // %
  quickRatio: number;               // %
  interestCoverage: number;         // Times
  equityRatio: number;              // %

  // Activity/Efficiency
  assetTurnover: number;            // Times
  inventoryTurnover: number;        // Times
  receivablesTurnover: number;      // Times
  payablesTurnover: number;         // Times

  // Growth
  revenueGrowth: number;            // YoY %
  operatingIncomeGrowth: number;    // YoY %
  netIncomeGrowth: number;          // YoY %
  assetGrowth: number;              // YoY %
  epsGrowth: number;                // YoY %
}

/**
 * Complete Financial Data
 */
export interface FinancialData {
  company: CompanyInfo;
  balanceSheet: BalanceSheetData[];
  incomeStatement: IncomeStatementData[];
  cashFlow: CashFlowData[];
  ratios: FinancialRatios[];
  lastUpdated: Date;
}

// ============================================================================
// UI COMPONENT PROPS
// ============================================================================

/**
 * Search Bar Component
 */
export interface SearchBarProps {
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  onSearch: (query: string) => void;
  onSelect: (company: CompanyInfo) => void;
  recentSearches?: CompanyInfo[];
  popularStocks?: CompanyInfo[];
  isLoading?: boolean;
  autoFocus?: boolean;
  className?: string;
}

export interface SearchResultItem {
  company: CompanyInfo;
  matchType: 'name' | 'code' | 'nameEn' | 'chosung';
  matchText: string;
}

/**
 * Company Header Component
 */
export interface CompanyHeaderProps {
  company: CompanyInfo;
  marketCap?: string;
  listedShares?: string;
  latestQuarter?: string;
  dataDate?: Date;
  isFavorite: boolean;
  onToggleFavorite: () => void;
  onExport: () => void;
  className?: string;
}

/**
 * Tab Navigation Component
 */
export type TabType = 'overview' | 'balance' | 'income' | 'cashflow' | 'ratios' | 'comparison';

export interface Tab {
  id: TabType;
  label: string;
  icon?: React.ReactNode;
  badge?: number;
  disabled?: boolean;
}

export interface TabNavigationProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  tabs: Tab[];
  className?: string;
}

/**
 * Date Range Selector Component
 */
export type DatePreset = 'year' | '3years' | '5years' | 'all' | 'custom';

export interface DateRangeSelectorProps {
  startDate: Date;
  endDate: Date;
  preset: DatePreset;
  onRangeChange: (start: Date, end: Date, preset: DatePreset) => void;
  availablePeriods: Period[];
  showComparison?: boolean;
  comparisonPeriod?: Period;
  onComparisonChange?: (period: Period) => void;
  className?: string;
}

/**
 * Metric Card Component
 */
export interface MetricCardProps {
  title: string;
  titleEn?: string;
  value: number;
  unit: string;
  changePercent?: number;
  changePeriod?: 'QoQ' | 'YoY';
  trend?: number[];                 // Sparkline data
  previousPeriod?: number;
  previousYear?: number;
  info?: string;                    // Tooltip text
  category: AccountCategory;
  priority?: 'high' | 'medium' | 'low';
  isLoading?: boolean;
  onClick?: () => void;
  className?: string;
}

/**
 * Data Table Component
 */
export interface TableColumn {
  id: string;
  label: string;
  period?: Period;
  align: 'left' | 'right' | 'center';
  width?: string | number;
  format?: (value: number) => string;
  sortable?: boolean;
}

export interface TableRow {
  id: string;
  label: string;
  labelEn?: string;
  indent: number;
  values: (number | null)[];
  isHeader?: boolean;
  isBold?: boolean;
  isExpandable?: boolean;
  isExpanded?: boolean;
  children?: TableRow[];
  category?: AccountCategory;
}

export interface DataTableProps {
  title: string;
  unit: string;
  columns: TableColumn[];
  rows: TableRow[];
  expandable?: boolean;
  sortable?: boolean;
  stickyHeader?: boolean;
  stickyColumn?: boolean;
  showGrowth?: boolean;
  isLoading?: boolean;
  onRowClick?: (row: TableRow) => void;
  onSort?: (columnId: string, direction: 'asc' | 'desc') => void;
  className?: string;
}

/**
 * Chart Components
 */
export interface ChartDataPoint {
  label: string;
  value: number;
  period?: Period;
  color?: string;
}

export interface ChartSeries {
  name: string;
  data: ChartDataPoint[];
  color?: string;
  type?: 'line' | 'bar' | 'area';
}

export interface TrendChartProps {
  title: string;
  series: ChartSeries[];
  unit: string;
  height?: number;
  showLegend?: boolean;
  showGrid?: boolean;
  showTooltip?: boolean;
  timeRange?: DatePreset;
  onTimeRangeChange?: (range: DatePreset) => void;
  className?: string;
}

export interface ComparisonChartProps {
  title: string;
  categories: string[];
  series: ChartSeries[];
  unit: string;
  orientation?: 'horizontal' | 'vertical';
  stacked?: boolean;
  height?: number;
  className?: string;
}

export interface PieChartProps {
  title: string;
  data: ChartDataPoint[];
  unit?: string;
  showPercentage?: boolean;
  showLegend?: boolean;
  innerRadius?: number;           // For donut chart
  height?: number;
  className?: string;
}

/**
 * Loading States
 */
export interface SkeletonProps {
  variant?: 'text' | 'rect' | 'circle';
  width?: string | number;
  height?: string | number;
  count?: number;
  className?: string;
}

export interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  color?: string;
  text?: string;
  className?: string;
}

/**
 * Error State
 */
export interface ErrorMessageProps {
  title: string;
  message: string;
  errorCode?: string;
  actionLabel?: string;
  onAction?: () => void;
  secondaryActionLabel?: string;
  onSecondaryAction?: () => void;
  className?: string;
}

/**
 * Empty State
 */
export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

/**
 * Tooltip Component
 */
export interface TooltipProps {
  content: string | React.ReactNode;
  title?: string;
  placement?: 'top' | 'right' | 'bottom' | 'left';
  trigger?: 'hover' | 'click' | 'focus';
  delay?: number;
  className?: string;
  children: React.ReactNode;
}

/**
 * Export Menu Component
 */
export type ExportFormat = 'excel' | 'csv' | 'pdf' | 'print' | 'link';

export interface ExportOptions {
  format: ExportFormat;
  includeCharts: boolean;
  includeBalanceSheet: boolean;
  includeIncomeStatement: boolean;
  includeCashFlow: boolean;
  includeRatios: boolean;
  dateRange: {
    start: Date;
    end: Date;
  };
}

export interface ExportMenuProps {
  onExport: (options: ExportOptions) => void;
  isExporting?: boolean;
  availableFormats?: ExportFormat[];
  className?: string;
}

/**
 * Comparison View Component
 */
export interface ComparisonViewProps {
  companies: CompanyInfo[];
  period: Period;
  metrics: string[];                // Metric IDs to compare
  onAddCompany: () => void;
  onRemoveCompany: (code: string) => void;
  onMetricChange: (metrics: string[]) => void;
  className?: string;
}

// ============================================================================
// VIEW COMPONENTS
// ============================================================================

/**
 * Overview View
 */
export interface OverviewViewProps {
  company: CompanyInfo;
  financialData: FinancialData;
  selectedPeriod: Period;
  dateRange: { start: Date; end: Date };
  onPeriodChange: (period: Period) => void;
  onDateRangeChange: (start: Date, end: Date) => void;
}

/**
 * Balance Sheet View
 */
export interface BalanceSheetViewProps {
  company: CompanyInfo;
  data: BalanceSheetData[];
  selectedPeriods: Period[];
  viewMode: 'table' | 'chart';
  onViewModeChange: (mode: 'table' | 'chart') => void;
  onPeriodChange: (periods: Period[]) => void;
}

/**
 * Income Statement View
 */
export interface IncomeStatementViewProps {
  company: CompanyInfo;
  data: IncomeStatementData[];
  selectedPeriods: Period[];
  viewMode: 'table' | 'chart';
  onViewModeChange: (mode: 'table' | 'chart') => void;
  onPeriodChange: (periods: Period[]) => void;
}

/**
 * Cash Flow View
 */
export interface CashFlowViewProps {
  company: CompanyInfo;
  data: CashFlowData[];
  selectedPeriods: Period[];
  viewMode: 'table' | 'chart' | 'sankey';
  onViewModeChange: (mode: 'table' | 'chart' | 'sankey') => void;
  onPeriodChange: (periods: Period[]) => void;
}

/**
 * Ratios View
 */
export interface RatiosViewProps {
  company: CompanyInfo;
  ratios: FinancialRatios[];
  selectedCategory: 'profitability' | 'stability' | 'activity' | 'growth';
  industryAverage?: FinancialRatios;
  onCategoryChange: (category: string) => void;
}

// ============================================================================
// HOOKS
// ============================================================================

/**
 * Company Search Hook
 */
export interface UseCompanySearchOptions {
  minCharacters?: number;
  debounceMs?: number;
  maxResults?: number;
}

export interface UseCompanySearchResult {
  query: string;
  results: SearchResultItem[];
  isLoading: boolean;
  error: Error | null;
  search: (query: string) => void;
  clear: () => void;
}

/**
 * Financial Data Hook
 */
export interface UseFinancialDataOptions {
  corpCode: string;
  startDate: Date;
  endDate: Date;
  reportTypes?: ReportType[];
}

export interface UseFinancialDataResult {
  data: FinancialData | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

/**
 * Favorites Hook
 */
export interface UseFavoritesResult {
  favorites: CompanyInfo[];
  isFavorite: (code: string) => boolean;
  addFavorite: (company: CompanyInfo) => void;
  removeFavorite: (code: string) => void;
  toggleFavorite: (company: CompanyInfo) => void;
}

/**
 * Export Hook
 */
export interface UseExportResult {
  exportData: (options: ExportOptions) => Promise<void>;
  isExporting: boolean;
  error: Error | null;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Number Formatting
 */
export type CurrencyUnit = 'won' | 'thousand' | 'million' | 'billion' | 'trillion';

export interface FormatCurrencyOptions {
  unit?: CurrencyUnit;
  decimals?: number;
  showUnit?: boolean;
  compact?: boolean;
}

export interface FormatPercentOptions {
  decimals?: number;
  showSign?: boolean;
  showSymbol?: boolean;
}

/**
 * Date Formatting
 */
export type DateFormat = 'short' | 'long' | 'quarter' | 'fiscal';

/**
 * Color Utilities
 */
export interface ColorScale {
  positive: string;
  positiveLight: string;
  negative: string;
  negativeLight: string;
  neutral: string;
}

/**
 * Chart Colors
 */
export type ChartColorScheme = 'default' | 'financial' | 'comparison' | 'categorical';

// ============================================================================
// CONSTANTS
// ============================================================================

/**
 * Metric Definitions
 */
export interface MetricDefinition {
  id: string;
  label: string;
  labelEn: string;
  category: AccountCategory;
  unit: CurrencyUnit;
  format: 'currency' | 'percent' | 'number' | 'ratio';
  description: string;
  formula?: string;
  interpretationPositive: boolean;  // True if higher is better
  displayPriority: 'high' | 'medium' | 'low';
}

/**
 * Account Mapping
 */
export interface AccountMapping {
  dartAccountCode: string;
  dartAccountName: string;
  standardName: string;
  category: AccountCategory;
  reportType: ReportType;
}

// ============================================================================
// API TYPES
// ============================================================================

/**
 * DART API Request
 */
export interface DartApiRequest {
  crtfc_key: string;            // API key
  corp_code?: string;           // Company code
  bsns_year?: string;           // Business year
  reprt_code?: string;          // Report code (11011, 11012, etc.)
}

/**
 * DART API Response
 */
export interface DartApiResponse<T> {
  status: string;
  message: string;
  data: T;
}

/**
 * DART Company List Response
 */
export interface DartCompanyListItem {
  corp_code: string;
  corp_name: string;
  stock_code: string;
  modify_date: string;
}

/**
 * DART Financial Statement Response
 */
export interface DartFinancialStatementItem {
  rcept_no: string;             // Receipt number
  reprt_code: string;           // Report code
  bsns_year: string;            // Business year
  corp_code: string;            // Company code
  sj_div: string;               // Statement division
  sj_nm: string;                // Statement name
  account_id: string;           // Account ID
  account_nm: string;           // Account name
  account_detail: string;       // Account detail
  thstrm_nm: string;            // This term name
  thstrm_amount: string;        // This term amount
  frmtrm_nm: string;            // Former term name
  frmtrm_amount: string;        // Former term amount
  bfefrmtrm_nm: string;         // Before former term name
  bfefrmtrm_amount: string;     // Before former term amount
  ord: string;                  // Order
  currency: string;             // Currency
}

/**
 * Example Usage:
 *
 * import { CompanyInfo, FinancialData, SearchBarProps } from './types/financial';
 *
 * const MySearchBar: React.FC<SearchBarProps> = ({ onSearch, onSelect }) => {
 *   // Implementation
 * };
 *
 * const handleSearch = (query: string) => {
 *   // Search logic
 * };
 *
 * const handleSelect = (company: CompanyInfo) => {
 *   // Selection logic
 * };
 */

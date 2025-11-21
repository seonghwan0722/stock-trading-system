# 50 Key Financial Metrics from Open DART API

This document provides a comprehensive reference for the 50 most important financial metrics available from the Korean Financial Supervisory Service's Open DART API, organized by financial statement category.

## Quick Reference Table

### All 50 Metrics at a Glance

| # | Metric | Korean Name | Type | Account Code | Category |
|---|--------|------------|------|--------------|----------|
| 1 | Total Assets | 자산총계 | BS | 1000000 | Balance Sheet |
| 2 | Current Assets | 유동자산 | BS | 1100000 | Balance Sheet |
| 3 | Non-Current Assets | 비유동자산 | BS | 1200000 | Balance Sheet |
| 4 | Cash and Equivalents | 현금및현금성자산 | BS | 1110000 | Balance Sheet |
| 5 | Short-term Investments | 단기금융상품 | BS | 1120000 | Balance Sheet |
| 6 | Accounts Receivable | 매출채권 | BS | 1130000 | Balance Sheet |
| 7 | Inventories | 재고자산 | BS | 1150000 | Balance Sheet |
| 8 | Property, Plant & Equipment | 유형자산 | BS | 1210000 | Balance Sheet |
| 9 | Intangible Assets | 무형자산 | BS | 1220000 | Balance Sheet |
| 10 | Long-term Investments | 장기금융상품 | BS | 1250000 | Balance Sheet |
| 11 | Total Liabilities | 부채총계 | BS | 2000000 | Balance Sheet |
| 12 | Current Liabilities | 유동부채 | BS | 2100000 | Balance Sheet |
| 13 | Non-Current Liabilities | 비유동부채 | BS | 2200000 | Balance Sheet |
| 14 | Short-term Debt | 단기차입금 | BS | 2110000 | Balance Sheet |
| 15 | Long-term Debt | 장기차입금 | BS | 2210000 | Balance Sheet |
| 16 | Total Equity | 자본총계 | BS | 3000000 | Balance Sheet |
| 17 | Capital Stock | 자본금 | BS | 3110000 | Balance Sheet |
| 18 | Retained Earnings | 이익잉여금 | BS | 3200000 | Balance Sheet |
| 19 | Accounts Payable | 외상매입금 | BS | 2140000 | Balance Sheet |
| 20 | Deferred Income Tax (Asset) | 이연세금자산 | BS | 1280000 | Balance Sheet |
| 21 | Deferred Income Tax (Liability) | 이연세금부채 | BS | 2240000 | Balance Sheet |
| 22 | Other Comprehensive Income (OCI) | 기타포괄손익누적액 | BS | 3300000 | Balance Sheet |
| 23 | Provisions | 충당금 | BS | 2150000 | Balance Sheet |
| 24 | Non-controlling Interests | 비지배주주지분 | BS | 3400000 | Balance Sheet |
| 25 | Lease Liabilities | 리스부채 | BS | 2160000 | Balance Sheet |
| 26 | Total Revenue | 매출액 | IS | 4100000 | Income Statement |
| 27 | Cost of Goods Sold | 매출원가 | IS | 5100000 | Income Statement |
| 28 | Gross Profit | 매출총이익 | IS | Calculated | Income Statement |
| 29 | Operating Expenses | 판매비와관리비 | IS | 5200000 | Income Statement |
| 30 | Operating Income | 영업이익 | IS | Calculated | Income Statement |
| 31 | Finance Costs | 금융비용 | IS | 5500000 | Income Statement |
| 32 | Finance Income | 금융수익 | IS | 4300000 | Income Statement |
| 33 | Other Gains/Losses | 기타이익(손실) | IS | 4400000 | Income Statement |
| 34 | Profit Before Tax | 세전이익 | IS | Calculated | Income Statement |
| 35 | Income Tax Expense | 법인세비용 | IS | 5600000 | Income Statement |
| 36 | Net Income | 당기순이익 | IS | Calculated | Income Statement |
| 37 | Other Comprehensive Income | 기타포괄손익 | IS | 4500000 | Income Statement |
| 38 | Total Comprehensive Income | 총포괄손익 | IS | Calculated | Income Statement |
| 39 | Discontinued Operations | 중단영업이익 | IS | 4200000 | Income Statement |
| 40 | Earnings Per Share (Basic) | 주당순이익 | IS | Calculated | Income Statement |
| 41 | Operating Cash Flow | 영업활동현금흐름 | CF | 6100000 | Cash Flow |
| 42 | Investing Cash Flow | 투자활동현금흐름 | CF | 6200000 | Cash Flow |
| 43 | Financing Cash Flow | 재무활동현금흐름 | CF | 6300000 | Cash Flow |
| 44 | Net Change in Cash | 현금순증감 | CF | Calculated | Cash Flow |
| 45 | Cash at Beginning | 기초현금 | CF | Calculated | Cash Flow |
| 46 | Cash at Ending | 기말현금 | CF | Calculated | Cash Flow |
| 47 | Depreciation & Amortization | 감가상각 | CF | 5320000 | Cash Flow |
| 48 | Stock-based Compensation | 주식기반보상 | CF | 5300000 | Cash Flow |
| 49 | Impairment Losses | 손상차손 | CF | 5400000 | Cash Flow |
| 50 | Other Non-Cash Items | 기타비현금항목 | CF | 6000000 | Cash Flow |

Legend: BS = Balance Sheet, IS = Income Statement, CF = Cash Flow

---

## Metric Definitions

### Balance Sheet Metrics (Metrics 1-25)

**Key Asset Metrics:**

1. **Total Assets** - Sum of all economic resources owned by company
2. **Current Assets** - Resources convertible to cash within 12 months
3. **Non-Current Assets** - Long-term resources with life > 12 months
4. **Cash and Equivalents** - Most liquid assets; immediate payment capability
5. **Short-term Investments** - Marketable securities maturing < 12 months
6. **Accounts Receivable** - Expected cash collections from customers
7. **Inventories** - Goods held for sale or production materials
8. **Property, Plant & Equipment** - Tangible long-lived assets
9. **Intangible Assets** - Patents, trademarks, goodwill, brand value
10. **Long-term Investments** - Securities/investments held > 12 months

**Key Liability Metrics:**

11. **Total Liabilities** - Sum of all obligations to creditors
12. **Current Liabilities** - Obligations due within 12 months
13. **Non-Current Liabilities** - Long-term obligations
14. **Short-term Debt** - Borrowings due within 12 months
15. **Long-term Debt** - Borrowings due after 12 months
19. **Accounts Payable** - Amounts owed to suppliers
23. **Provisions** - Estimated liabilities for future obligations
25. **Lease Liabilities** - Obligations under operating/finance leases

**Key Equity Metrics:**

16. **Total Equity** - Shareholders' ownership interest (Assets - Liabilities)
17. **Capital Stock** - Par value of issued shares
18. **Retained Earnings** - Accumulated profits reinvested in business
20. **Deferred Income Tax (Asset)** - Tax benefits from temporary differences
21. **Deferred Income Tax (Liability)** - Tax obligations from temporary differences
22. **Other Comprehensive Income** - Unrealized gains/losses not in net income
24. **Non-controlling Interests** - Minority shareholders' stake in subsidiaries

---

### Income Statement Metrics (Metrics 26-40)

**Revenue and Cost:**

26. **Total Revenue** - Total income from primary operations
27. **Cost of Goods Sold** - Direct costs to produce goods sold
28. **Gross Profit** - Revenue minus COGS (indicates pricing power)
29. **Operating Expenses** - Indirect costs to run business (sales, admin, R&D)
30. **Operating Income** - Profit from core business (before financing/taxes)

**Non-Operating Items:**

31. **Finance Costs** - Interest and other financing expenses
32. **Finance Income** - Investment income and other financial gains
33. **Other Gains/Losses** - Miscellaneous non-operating items
34. **Profit Before Tax** - Operating income adjusted for non-operating items

**Taxes and Net Income:**

35. **Income Tax Expense** - Corporate income tax liability
36. **Net Income** - Bottom-line profit (most important metric)
37. **Other Comprehensive Income** - Unrealized gains/losses not in net income
38. **Total Comprehensive Income** - Complete measure including OCI
39. **Discontinued Operations** - Profit from divested business units
40. **Earnings Per Share** - Net income per common share

---

### Cash Flow Metrics (Metrics 41-50)

**Main Cash Flow Categories:**

41. **Operating Cash Flow** - Cash from core business operations
42. **Investing Cash Flow** - Cash used for investments/acquisitions
43. **Financing Cash Flow** - Cash from/to debt and equity financing
44. **Net Change in Cash** - Sum of all three cash flow categories

**Supporting Metrics:**

45. **Cash at Beginning** - Opening cash balance for period
46. **Cash at Ending** - Closing cash balance for period
47. **Depreciation & Amortization** - Non-cash expense added back to earnings
48. **Stock-based Compensation** - Non-cash employee compensation
49. **Impairment Losses** - Write-downs of asset values
50. **Other Non-Cash Items** - Various reconciling adjustments

---

## Common Financial Ratios Using These Metrics

### Profitability Ratios

```
Gross Margin = Gross Profit / Revenue = (26-27) / 26
Operating Margin = Operating Income / Revenue = 30 / 26
Net Margin = Net Income / Revenue = 36 / 26
Return on Assets (ROA) = Net Income / Total Assets = 36 / 1
Return on Equity (ROE) = Net Income / Total Equity = 36 / 16
```

### Liquidity Ratios

```
Current Ratio = Current Assets / Current Liabilities = 2 / 12
Quick Ratio = (Current Assets - Inventory) / Current Liabilities = (2-7) / 12
Cash Ratio = Cash / Current Liabilities = 4 / 12
```

### Leverage Ratios

```
Debt Ratio = Total Liabilities / Total Assets = 11 / 1
Debt-to-Equity = Total Liabilities / Total Equity = 11 / 16
Equity Ratio = Total Equity / Total Assets = 16 / 1
Interest Coverage = Operating Income / Finance Costs = 30 / 31
```

### Efficiency Ratios

```
Asset Turnover = Revenue / Total Assets = 26 / 1
Inventory Turnover = COGS / Average Inventory = 27 / 7
Receivables Turnover = Revenue / Average Receivables = 26 / 6
```

---

## Data Quality Guidelines

### Best Practices

1. **Use Consolidated Data** - fs_div=1001 recommended (includes subsidiaries)
2. **Verify Period Consistency** - Compare same quarters year-over-year
3. **Check Filing Date** - Ensure not looking at restated data from corrections
4. **Review Accounting Changes** - Note any changes in accounting policies
5. **Exclude Non-recurring Items** - Focus on recurring operations (metric 39)

### Account Code Structure

Codes follow hierarchical pattern:
- **1xxxxx0**: Level 1-2 accounts (summary)
- **1xxxxx**: Level 3+ accounts (detail)
- **Organized by statement type**: 1000s (BS), 4000s/5000s (IS), 6000s (CF)

### Data Availability

| Report Type | Available Statements | Filing Deadline |
|------------|---------------------|-----------------|
| Annual (11011) | Full | 60 days after year-end |
| Half-year (11012) | Full | 45 days after June 30 |
| Q3 (11013) | Full | 45 days after Sept 30 |
| Q1 (11014) | Limited | 45 days after March 31 |

---

## Implementation Example

```python
# Extract all 50 metrics efficiently
def extract_all_metrics(client, corp_code, bsns_year):
    """Get all 50 key metrics from API"""

    # Fetch financial data
    data = client.get_financial_statements(
        corp_code=corp_code,
        bsns_year=bsns_year,
        reprt_code="11011",  # Annual
        fs_div="1001"  # Consolidated
    )

    # Build account lookup
    accounts = {item['account_id']: item for item in data['list']}

    # Extract all metrics
    metrics = {}
    METRIC_ACCOUNTS = {
        'total_assets': '1000000',
        'current_assets': '1100000',
        'noncurrent_assets': '1200000',
        'cash': '1110000',
        # ... (all 50 metrics)
    }

    for metric_name, account_code in METRIC_ACCOUNTS.items():
        if account_code in accounts:
            amount = int(accounts[account_code]['thstrm_amount'])
            metrics[metric_name] = amount

    return metrics
```

This reference provides complete documentation for analyzing financial data from Open DART API.

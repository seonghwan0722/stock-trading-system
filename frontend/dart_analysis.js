// DART 재무제표 분석 JavaScript

const API_BASE = '/api/dart';
let selectedStock = null;
let searchTimeout = null;

// DOM 요소
const searchInput = document.getElementById('stockSearch');
const autocompleteDropdown = document.getElementById('autocompleteDropdown');
const companySection = document.getElementById('companySection');
const loadingSection = document.getElementById('loadingSection');
const errorSection = document.getElementById('errorSection');
const emptyState = document.getElementById('emptyState');

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    setupSearchInput();
});

// 검색 입력 설정
function setupSearchInput() {
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();

        clearTimeout(searchTimeout);

        if (query.length < 2) {
            hideAutocomplete();
            return;
        }

        // 300ms 디바운스
        searchTimeout = setTimeout(() => {
            searchStocks(query);
        }, 300);
    });

    // 외부 클릭 시 자동완성 닫기
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !autocompleteDropdown.contains(e.target)) {
            hideAutocomplete();
        }
    });
}

// 종목 검색
async function searchStocks(query) {
    try {
        const response = await fetch(`${API_BASE}/stocks/search?q=${encodeURIComponent(query)}&limit=20`);
        const data = await response.json();

        if (data.success && data.data.length > 0) {
            displayAutocomplete(data.data);
        } else {
            hideAutocomplete();
        }
    } catch (error) {
        console.error('Search error:', error);
        hideAutocomplete();
    }
}

// 자동완성 결과 표시
function displayAutocomplete(stocks) {
    autocompleteDropdown.innerHTML = stocks.map(stock => `
        <div class="autocomplete-item" onclick='selectStock(${JSON.stringify(stock)})'>
            <strong>${stock.company_name}</strong>
            <span class="stock-code">${stock.stock_code}</span>
            <span class="market-badge market-${stock.market_type.toLowerCase()}">${stock.market_type}</span>
        </div>
    `).join('');

    autocompleteDropdown.classList.add('show');
}

// 자동완성 숨기기
function hideAutocomplete() {
    autocompleteDropdown.classList.remove('show');
}

// 종목 선택
async function selectStock(stock) {
    selectedStock = stock;
    hideAutocomplete();
    searchInput.value = `${stock.company_name} (${stock.stock_code})`;

    // 재무제표 로드
    await loadFinancialData(stock.corp_code);
}

// 재무제표 데이터 로드
async function loadFinancialData(corpCode) {
    showLoading();
    hideError();
    emptyState.style.display = 'none';

    try {
        // 회사 정보 및 재무제표 조회
        const year = new Date().getFullYear() - 1; // 전년도 데이터
        const response = await fetch(
            `${API_BASE}/financials/${corpCode}?year=${year}&report_type=11011&fs_div=1001`,
            {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            }
        );

        const data = await response.json();

        if (data.success) {
            displayCompanyInfo(data.company, data.year);
            displayMetrics(data.metrics);
            displayRatios(data.ratios);
            displayFinancialStatements(data.financials);

            companySection.style.display = 'block';
        } else {
            showError(data.message || '재무제표를 불러올 수 없습니다.');
        }
    } catch (error) {
        console.error('Load financial data error:', error);
        showError('데이터를 불러오는 중 오류가 발생했습니다.');
    } finally {
        hideLoading();
    }
}

// 회사 정보 표시
function displayCompanyInfo(company, year) {
    document.getElementById('companyName').textContent = company.corp_name;
    document.getElementById('stockCode').textContent = selectedStock.stock_code;
    document.getElementById('marketType').textContent = selectedStock.market_type;
    document.getElementById('lastUpdate').textContent = `${year}년 사업보고서`;
}

// 주요 지표 표시
function displayMetrics(metrics) {
    const metricsGrid = document.getElementById('metricsGrid');

    const keyMetrics = [
        { key: 'total_assets', label: '총자산', unit: '억원' },
        { key: 'total_liabilities', label: '총부채', unit: '억원' },
        { key: 'total_equity', label: '총자본', unit: '억원' },
        { key: 'revenue', label: '매출액', unit: '억원' },
        { key: 'operating_income', label: '영업이익', unit: '억원' },
        { key: 'net_income', label: '당기순이익', unit: '억원' }
    ];

    metricsGrid.innerHTML = keyMetrics.map(metric => {
        const value = metrics[metric.key] || 0;
        const formatted = formatCurrency(value);

        return `
            <div class="metric-card">
                <div class="metric-label">${metric.label}</div>
                <div class="metric-value">
                    ${formatted}
                    <span class="metric-unit">${metric.unit}</span>
                </div>
            </div>
        `;
    }).join('');
}

// 재무비율 표시
function displayRatios(ratios) {
    const ratiosGrid = document.getElementById('ratiosGrid');

    const ratioItems = [
        { key: 'gross_margin', label: '매출총이익률', unit: '%' },
        { key: 'operating_margin', label: '영업이익률', unit: '%' },
        { key: 'net_margin', label: '순이익률', unit: '%' },
        { key: 'debt_ratio', label: '부채비율', unit: '%' },
        { key: 'equity_ratio', label: '자기자본비율', unit: '%' },
        { key: 'current_ratio', label: '유동비율', unit: '%' },
        { key: 'debt_to_equity', label: '부채자본비율', unit: '' }
    ];

    ratiosGrid.innerHTML = ratioItems.map(ratio => {
        const value = ratios[ratio.key] || 0;
        const formatted = value.toFixed(2);

        return `
            <div class="metric-card">
                <div class="metric-label">${ratio.label}</div>
                <div class="metric-value">
                    ${formatted}
                    <span class="metric-unit">${ratio.unit}</span>
                </div>
            </div>
        `;
    }).join('');
}

// 재무제표 표시
function displayFinancialStatements(financials) {
    // 간단히 표시 (실제로는 더 상세하게 구현 필요)
    const balanceTable = document.getElementById('balanceTable');
    const incomeTable = document.getElementById('incomeTable');
    const cashflowTable = document.getElementById('cashflowTable');

    balanceTable.innerHTML = '<p>재무상태표 데이터 표시 (구현 중)</p>';
    incomeTable.innerHTML = '<p>손익계산서 데이터 표시 (구현 중)</p>';
    cashflowTable.innerHTML = '<p>현금흐름표 데이터 표시 (구현 중)</p>';
}

// 탭 전환
function showTab(tabName) {
    // 모든 탭 비활성화
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });

    // 선택된 탭 활성화
    event.target.classList.add('active');
    document.getElementById(`${tabName}Tab`).classList.add('active');
}

// 유틸리티 함수
function formatCurrency(value) {
    // 억원 단위로 변환
    const billion = value / 100000000;
    return billion.toLocaleString('ko-KR', {
        maximumFractionDigits: 0
    });
}

function showLoading() {
    loadingSection.style.display = 'block';
    companySection.style.display = 'none';
}

function hideLoading() {
    loadingSection.style.display = 'none';
}

function showError(message) {
    errorSection.innerHTML = `
        <div class="error-message">
            <strong>⚠️ 오류</strong><br>
            ${message}
        </div>
    `;
    errorSection.style.display = 'block';
}

function hideError() {
    errorSection.style.display = 'none';
}

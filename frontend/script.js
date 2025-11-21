// API 기본 URL
const API_BASE = window.location.origin;

// 토큰 관리
let authToken = localStorage.getItem('authToken');

// API 요청 헬퍼
async function apiRequest(endpoint, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        }
    };

    if (authToken) {
        options.headers['Authorization'] = `Bearer ${authToken}`;
    }

    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        const result = await response.json();

        if (response.status === 401) {
            // 인증 실패
            logout();
            return null;
        }

        return result;
    } catch (error) {
        console.error('API 요청 오류:', error);
        alert('서버와 통신 중 오류가 발생했습니다.');
        return null;
    }
}

// 로그인
async function login() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    if (!username || !password) {
        document.getElementById('loginError').textContent = '아이디와 비밀번호를 입력해주세요.';
        return;
    }

    const result = await apiRequest('/api/auth/login', 'POST', { username, password });

    if (result && result.success) {
        authToken = result.token;
        localStorage.setItem('authToken', authToken);

        // 메인 페이지로 이동
        document.getElementById('loginPage').classList.remove('active');
        document.getElementById('mainPage').classList.add('active');

        // 대시보드 로드
        loadDashboard();
    } else {
        document.getElementById('loginError').textContent = result?.message || '로그인 실패';
    }
}

// 로그아웃
function logout() {
    authToken = null;
    localStorage.removeItem('authToken');

    document.getElementById('mainPage').classList.remove('active');
    document.getElementById('loginPage').classList.add('active');
}

// 탭 전환
function showTab(tabName) {
    // 모든 탭 숨기기
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });

    // 선택된 탭 표시
    document.getElementById(`${tabName}Tab`).classList.add('active');

    // 탭별 초기 로드
    if (tabName === 'dashboard') {
        loadDashboard();
    } else if (tabName === 'trading') {
        loadPositionsForSelect();
    } else if (tabName === 'recommendations') {
        // 추천 탭은 수동으로 버튼 클릭 필요
    } else if (tabName === 'strategy') {
        loadStrategySettings();
    } else if (tabName === 'news') {
        loadNews();
    }
}

// 대시보드 로드
async function loadDashboard() {
    await loadAccountSummary();
    await loadPositions();
}

// 계좌 요약 정보 로드
async function loadAccountSummary() {
    const result = await apiRequest('/api/account/balance');

    if (result && result.success) {
        document.getElementById('totalValue').textContent =
            `${result.total_eval_amount.toLocaleString()}원`;
        document.getElementById('cashBalance').textContent =
            `${result.cash_balance.toLocaleString()}원`;

        const profitLoss = result.total_profit_loss;
        const profitLossElement = document.getElementById('totalProfitLoss');
        profitLossElement.textContent = `${profitLoss.toLocaleString()}원`;
        profitLossElement.style.color = profitLoss >= 0 ? '#27ae60' : '#e74c3c';
    }
}

// 보유 종목 로드
async function loadPositions() {
    const result = await apiRequest('/api/account/positions');

    const positionsList = document.getElementById('positionsList');

    if (result && result.success && result.positions.length > 0) {
        positionsList.innerHTML = result.positions.map(pos => {
            const profitClass = pos.profit_rate >= 0 ? 'profit positive' : 'loss negative';
            return `
                <div class="position-item ${profitClass}">
                    <div class="position-header">
                        <span class="position-name">${pos.stock_name} (${pos.stock_code})</span>
                        <span class="position-profit ${profitClass}">
                            ${pos.profit_rate.toFixed(2)}% (${pos.profit_loss.toLocaleString()}원)
                        </span>
                    </div>
                    <div class="position-details">
                        <div>보유수량: ${pos.quantity.toLocaleString()}주</div>
                        <div>평균단가: ${pos.avg_price.toLocaleString()}원</div>
                        <div>현재가: ${pos.current_price.toLocaleString()}원</div>
                        <div>평가금액: ${pos.eval_amount.toLocaleString()}원</div>
                    </div>
                    <div class="position-actions">
                        <button onclick="showStockDetail('${pos.stock_code}', '${pos.stock_name}')" class="detail-btn">📊 상세정보</button>
                    </div>
                </div>
            `;
        }).join('');
    } else {
        positionsList.innerHTML = '<p class="loading">보유 종목이 없습니다.</p>';
    }
}

// 매도용 종목 선택 로드
async function loadPositionsForSelect() {
    const result = await apiRequest('/api/account/positions');
    const select = document.getElementById('sellPositionSelect');

    if (result && result.success && result.positions.length > 0) {
        select.innerHTML = '<option value="">종목 선택</option>' +
            result.positions.map(pos =>
                `<option value='${JSON.stringify(pos)}'>${pos.stock_name} (${pos.stock_code})</option>`
            ).join('');
    }
}

// 매수 분석
async function analyzeBuy() {
    const stockCode = document.getElementById('buyStockCode').value;
    const stockName = document.getElementById('buyStockName').value;

    if (!stockCode || !stockName) {
        alert('종목 코드와 이름을 입력해주세요.');
        return;
    }

    const resultDiv = document.getElementById('buyAnalysisResult');
    resultDiv.innerHTML = '<p class="loading">AI 분석 중...</p>';

    const result = await apiRequest('/api/trading/analyze-buy', 'POST', {
        stock_code: stockCode,
        stock_name: stockName
    });

    if (result && result.success) {
        const analysis = result.analysis;
        resultDiv.innerHTML = `
            <h4>📊 AI 매수 분석 결과</h4>
            <p><strong>매수 추천:</strong> ${analysis.should_buy ? '✅ YES' : '❌ NO'}</p>
            <p><strong>신뢰도:</strong> ${(analysis.confidence * 100).toFixed(1)}%</p>
            <p><strong>추천 수량:</strong> ${analysis.recommended_quantity}주</p>
            <p><strong>목표가:</strong> ${analysis.target_price.toLocaleString()}원</p>
            <hr>
            <p><strong>판단 근거:</strong></p>
            <pre>${analysis.reason}</pre>
        `;

        // 매수 실행 섹션 표시
        if (analysis.should_buy) {
            document.getElementById('buyExecuteSection').style.display = 'block';
            document.getElementById('buyQuantity').value = analysis.recommended_quantity;
            document.getElementById('buyPrice').value = 0;
        }
    } else {
        resultDiv.innerHTML = '<p class="error-message">분석 실패</p>';
    }
}

// 매수 실행
async function executeBuy() {
    const stockCode = document.getElementById('buyStockCode').value;
    const stockName = document.getElementById('buyStockName').value;
    const quantity = parseInt(document.getElementById('buyQuantity').value);
    const price = parseInt(document.getElementById('buyPrice').value) || 0;

    if (!confirm(`${stockName} ${quantity}주를 매수하시겠습니까?`)) {
        return;
    }

    const result = await apiRequest('/api/trading/buy', 'POST', {
        stock_code: stockCode,
        stock_name: stockName,
        quantity: quantity,
        price: price
    });

    if (result && result.success) {
        alert('매수 주문이 접수되었습니다.');
        document.getElementById('buyExecuteSection').style.display = 'none';
        loadDashboard();
    } else {
        alert('매수 실패: ' + (result?.message || '알 수 없는 오류'));
    }
}

// 매도 포지션 선택
let selectedPosition = null;

function loadPositionForSell() {
    const select = document.getElementById('sellPositionSelect');
    const value = select.value;

    if (value) {
        selectedPosition = JSON.parse(value);
    } else {
        selectedPosition = null;
    }
}

// 매도 분석
async function analyzeSell() {
    if (!selectedPosition) {
        alert('매도할 종목을 선택해주세요.');
        return;
    }

    const resultDiv = document.getElementById('sellAnalysisResult');
    resultDiv.innerHTML = '<p class="loading">AI 분석 중...</p>';

    const result = await apiRequest('/api/trading/analyze-sell', 'POST', {
        position: selectedPosition
    });

    if (result && result.success) {
        const analysis = result.analysis;
        resultDiv.innerHTML = `
            <h4>📊 AI 매도 분석 결과</h4>
            <p><strong>매도 추천:</strong> ${analysis.should_sell ? '✅ YES' : '❌ NO'}</p>
            <p><strong>신뢰도:</strong> ${(analysis.confidence * 100).toFixed(1)}%</p>
            <p><strong>추천 수량:</strong> ${analysis.recommended_quantity}주</p>
            <p><strong>긴급도:</strong> ${analysis.urgency.toUpperCase()}</p>
            <hr>
            <p><strong>판단 근거:</strong></p>
            <pre>${analysis.reason}</pre>
        `;

        // 매도 실행 섹션 표시
        if (analysis.should_sell) {
            document.getElementById('sellExecuteSection').style.display = 'block';
            document.getElementById('sellQuantity').value = analysis.recommended_quantity;
            document.getElementById('sellPrice').value = 0;
        }
    } else {
        resultDiv.innerHTML = '<p class="error-message">분석 실패</p>';
    }
}

// 매도 실행
async function executeSell() {
    if (!selectedPosition) {
        alert('매도할 종목을 선택해주세요.');
        return;
    }

    const quantity = parseInt(document.getElementById('sellQuantity').value);
    const price = parseInt(document.getElementById('sellPrice').value) || 0;

    if (!confirm(`${selectedPosition.stock_name} ${quantity}주를 매도하시겠습니까?`)) {
        return;
    }

    const result = await apiRequest('/api/trading/sell', 'POST', {
        stock_code: selectedPosition.stock_code,
        stock_name: selectedPosition.stock_name,
        quantity: quantity,
        price: price
    });

    if (result && result.success) {
        alert('매도 주문이 접수되었습니다.');
        document.getElementById('sellExecuteSection').style.display = 'none';
        loadDashboard();
    } else {
        alert('매도 실패: ' + (result?.message || '알 수 없는 오류'));
    }
}

// 추천 종목 로드
async function loadRecommendations() {
    const container = document.getElementById('recommendationsContainer');
    container.innerHTML = '<p class="loading">AI가 추천 종목을 분석하고 있습니다... 잠시만 기다려주세요.</p>';

    const result = await apiRequest('/api/recommendations/stocks');

    if (result && result.success) {
        const recommendations = result.recommendations;

        if (recommendations.length === 0) {
            container.innerHTML = '<p class="loading">현재 추천할 종목이 없습니다.</p>';
            return;
        }

        container.innerHTML = recommendations.map((stock, index) => {
            const confidenceClass = stock.confidence >= 80 ? 'high-confidence' :
                                   stock.confidence >= 60 ? 'medium-confidence' : 'low-confidence';

            return `
                <div class="recommendation-card ${confidenceClass}">
                    <div class="recommendation-header">
                        <div class="recommendation-title">
                            <h3>${index + 1}. ${stock.stock_name} (${stock.stock_code})</h3>
                            <span class="confidence-badge">신뢰도 ${stock.confidence}%</span>
                        </div>
                        <div class="recommendation-price">
                            <span class="current-price">${stock.current_price?.toLocaleString() || '-'}원</span>
                            ${stock.expected_return ? `<span class="expected-return">기대수익률 +${stock.expected_return}%</span>` : ''}
                        </div>
                    </div>

                    <div class="recommendation-body">
                        <h4>📝 추천 이유</h4>
                        <p class="recommendation-reason">${stock.reason}</p>

                        ${stock.pros ? `
                        <div class="recommendation-section">
                            <h4>✅ 장점</h4>
                            <ul class="pros-list">
                                ${stock.pros.map(pro => `<li>${pro}</li>`).join('')}
                            </ul>
                        </div>
                        ` : ''}

                        ${stock.risks ? `
                        <div class="recommendation-section">
                            <h4>⚠️ 리스크</h4>
                            <ul class="risks-list">
                                ${stock.risks.map(risk => `<li>${risk}</li>`).join('')}
                            </ul>
                        </div>
                        ` : ''}

                        ${stock.target_price ? `
                        <div class="recommendation-footer">
                            <span>목표가: <strong>${stock.target_price.toLocaleString()}원</strong></span>
                            ${stock.investment_period ? `<span>투자기간: <strong>${stock.investment_period}</strong></span>` : ''}
                        </div>
                        ` : ''}
                    </div>

                    <div class="recommendation-actions">
                        <button onclick="goToTrading('${stock.stock_code}', '${stock.stock_name}')" class="analyze-btn">
                            상세 분석하기
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    } else {
        container.innerHTML = '<p class="error-message">추천 종목을 불러오는데 실패했습니다.</p>';
    }
}

// 매매 탭으로 이동하며 종목 정보 입력
function goToTrading(stockCode, stockName) {
    showTab('trading');
    document.getElementById('buyStockCode').value = stockCode;
    document.getElementById('buyStockName').value = stockName;

    // 스크롤을 매수 분석 섹션으로 이동
    setTimeout(() => {
        document.getElementById('buyStockCode').scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 100);
}

// 뉴스 카테고리 전환
function showNewsCategory(category) {
    // 모든 버튼 비활성화
    document.querySelectorAll('.news-tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // 모든 카테고리 콘텐츠 숨기기
    document.querySelectorAll('.news-category-content').forEach(content => {
        content.classList.remove('active');
    });

    // 선택된 버튼 활성화
    event.target.classList.add('active');

    // 선택된 콘텐츠 표시
    document.getElementById(`${category}NewsContent`).classList.add('active');

    // 해당 카테고리 뉴스 로드 (아직 로드되지 않았다면)
    loadNewsByCategory(category);
}

// 모든 뉴스 로드
async function loadAllNews() {
    await loadNewsByCategory('popular');
    await loadNewsByCategory('economy');
    await loadNewsByCategory('stock');
    await loadNewsByCategory('tech');
    await loadNewsByCategory('international');
    await loadNewsByCategory('industry');
    await loadMarketSentiment();
}

// 카테고리별 뉴스 로드
async function loadNewsByCategory(category) {
    const listDiv = document.getElementById(`${category}NewsList`);
    listDiv.innerHTML = '<p class="loading">뉴스 로딩 중...</p>';

    const result = await apiRequest(`/api/news/category/${category}`);

    if (result && result.success && result.news && result.news.length > 0) {
        listDiv.innerHTML = result.news.map((article, index) => {
            const timeAgo = getTimeAgo(article.published_at);
            const summary = article.summary || article.description || article.content || '요약 정보가 없습니다.';
            const truncatedSummary = summary.length > 200 ? summary.substring(0, 200) + '...' : summary;

            return `
                <div class="news-item" onclick="toggleNewsContent(this)">
                    <div class="news-header">
                        <span class="news-index">${index + 1}</span>
                        <div class="news-title-wrapper">
                            <h4 class="news-title">${article.title || '제목 없음'}</h4>
                        </div>
                    </div>
                    <div class="news-meta">
                        <span class="news-source">${article.source || '뉴스 제공처'}</span>
                        <span class="news-time">${timeAgo}</span>
                    </div>
                    <div class="news-content-wrapper collapsed">
                        <p class="news-summary">${truncatedSummary}</p>
                        ${article.content && article.content !== summary ? `<p class="news-full-content">${article.content}</p>` : ''}
                    </div>
                    <div class="news-footer">
                        ${article.url ? `<a href="${article.url}" target="_blank" class="news-link" onclick="event.stopPropagation()">📰 원문 보기 →</a>` : ''}
                        <span class="news-expand-hint">클릭하여 ${article.content ? '전체 내용' : '더보기'} ▼</span>
                    </div>
                </div>
            `;
        }).join('');
    } else {
        listDiv.innerHTML = '<p class="error-message">뉴스를 불러올 수 없습니다.</p>';
    }
}

// 시장 심리 분석 로드
async function loadMarketSentiment() {
    const sentimentDiv = document.getElementById('marketSentiment');
    sentimentDiv.innerHTML = '<p class="loading">시장 심리 분석 중...</p>';

    const sentimentResult = await apiRequest('/api/news/sentiment');
    if (sentimentResult && sentimentResult.success) {
        const sentiment = sentimentResult.sentiment;
        const sentimentClass = `sentiment-${sentiment.sentiment}`;
        const sentimentText = {
            'positive': '긍정적 🟢',
            'neutral': '중립 🟡',
            'negative': '부정적 🔴'
        }[sentiment.sentiment] || '중립';

        sentimentDiv.innerHTML = `
            <h3 class="${sentimentClass}">현재 시장 심리: ${sentimentText}</h3>
            <p><strong>신뢰도:</strong> ${(sentiment.score * 100).toFixed(1)}%</p>
            <hr>
            <pre>${sentiment.analysis}</pre>
        `;
    } else {
        sentimentDiv.innerHTML = '<p class="error-message">시장 심리 분석 실패</p>';
    }
}

// 시간 경과 표시 헬퍼 함수
function getTimeAgo(dateString) {
    if (!dateString) return '';

    const now = new Date();
    const past = new Date(dateString);
    const diffMs = now - past;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return '방금 전';
    if (diffMins < 60) return `${diffMins}분 전`;
    if (diffHours < 24) return `${diffHours}시간 전`;
    if (diffDays < 7) return `${diffDays}일 전`;

    return past.toLocaleDateString('ko-KR');
}

// 뉴스 콘텐츠 토글
function toggleNewsContent(element) {
    const contentWrapper = element.querySelector('.news-content-wrapper');
    const expandHint = element.querySelector('.news-expand-hint');

    if (contentWrapper.classList.contains('collapsed')) {
        contentWrapper.classList.remove('collapsed');
        contentWrapper.classList.add('expanded');
        if (expandHint) {
            expandHint.textContent = '접기 ▲';
        }
    } else {
        contentWrapper.classList.remove('expanded');
        contentWrapper.classList.add('collapsed');
        if (expandHint) {
            const hasFullContent = element.querySelector('.news-full-content');
            expandHint.textContent = `클릭하여 ${hasFullContent ? '전체 내용' : '더보기'} ▼`;
        }
    }
}

// 뉴스 로드 (레거시 호환)
async function loadNews() {
    await loadAllNews();
}

// 전략 설정 관리
const DEFAULT_STRATEGY_SETTINGS = {
    maxPositions: 5,
    maxPositionSize: 5000000,
    buyConfidenceThreshold: 70,
    maxBuyAmount: 3000000,
    stopLossRate: -7,
    takeProfitRate: 15,
    sellConfidenceThreshold: 60,
    aiModel: 'claude-sonnet-4-5-20250929',
    maxTokens: 2000
};

// 전략 설정 불러오기
function loadStrategySettings() {
    // 로컬 스토리지에서 불러오기
    const savedSettings = localStorage.getItem('strategySettings');
    const settings = savedSettings ? JSON.parse(savedSettings) : DEFAULT_STRATEGY_SETTINGS;

    // UI에 값 적용
    document.getElementById('maxPositions').value = settings.maxPositions;
    document.getElementById('maxPositionSize').value = settings.maxPositionSize;
    document.getElementById('buyConfidenceThreshold').value = settings.buyConfidenceThreshold;
    document.getElementById('maxBuyAmount').value = settings.maxBuyAmount;
    document.getElementById('stopLossRate').value = settings.stopLossRate;
    document.getElementById('takeProfitRate').value = settings.takeProfitRate;
    document.getElementById('sellConfidenceThreshold').value = settings.sellConfidenceThreshold;
    document.getElementById('aiModel').value = settings.aiModel;
    document.getElementById('maxTokens').value = settings.maxTokens;

    showSettingsMessage('설정을 불러왔습니다.', 'success');
}

// 전략 설정 저장
async function saveStrategySettings() {
    const settings = {
        maxPositions: parseInt(document.getElementById('maxPositions').value),
        maxPositionSize: parseInt(document.getElementById('maxPositionSize').value),
        buyConfidenceThreshold: parseInt(document.getElementById('buyConfidenceThreshold').value),
        maxBuyAmount: parseInt(document.getElementById('maxBuyAmount').value),
        stopLossRate: parseFloat(document.getElementById('stopLossRate').value),
        takeProfitRate: parseFloat(document.getElementById('takeProfitRate').value),
        sellConfidenceThreshold: parseInt(document.getElementById('sellConfidenceThreshold').value),
        aiModel: document.getElementById('aiModel').value,
        maxTokens: parseInt(document.getElementById('maxTokens').value)
    };

    // 유효성 검사
    if (settings.maxPositions < 1 || settings.maxPositions > 20) {
        showSettingsMessage('최대 보유 종목 수는 1~20 사이여야 합니다.', 'error');
        return;
    }

    if (settings.stopLossRate > 0) {
        showSettingsMessage('손절 비율은 0 이하여야 합니다. (예: -7)', 'error');
        return;
    }

    if (settings.takeProfitRate < 0) {
        showSettingsMessage('익절 비율은 0 이상이어야 합니다.', 'error');
        return;
    }

    // 로컬 스토리지에 저장
    localStorage.setItem('strategySettings', JSON.stringify(settings));

    // 백엔드에 저장 (선택사항 - API 엔드포인트가 있다면)
    try {
        const result = await apiRequest('/api/settings/strategy', 'POST', settings);
        if (result && result.success) {
            showSettingsMessage('설정이 저장되었습니다! ✅', 'success');
        } else {
            showSettingsMessage('로컬에는 저장되었으나, 서버 동기화에 실패했습니다.', 'warning');
        }
    } catch (error) {
        // 백엔드 엔드포인트가 없어도 로컬 저장은 완료
        showSettingsMessage('설정이 로컬에 저장되었습니다.', 'success');
    }
}

// 전략 설정 초기화
function resetStrategySettings() {
    if (!confirm('모든 설정을 기본값으로 초기화하시겠습니까?')) {
        return;
    }

    localStorage.setItem('strategySettings', JSON.stringify(DEFAULT_STRATEGY_SETTINGS));
    loadStrategySettings();
    showSettingsMessage('설정이 기본값으로 초기화되었습니다.', 'success');
}

// 설정 메시지 표시
function showSettingsMessage(message, type = 'info') {
    const messageDiv = document.getElementById('settingsMessage');
    messageDiv.textContent = message;
    messageDiv.className = `settings-message ${type}`;
    messageDiv.style.display = 'block';

    // 3초 후 메시지 숨기기
    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 3000);
}

// 현재 설정 가져오기 (다른 함수에서 사용 가능)
function getCurrentSettings() {
    const savedSettings = localStorage.getItem('strategySettings');
    return savedSettings ? JSON.parse(savedSettings) : DEFAULT_STRATEGY_SETTINGS;
}

// ========== 전략 서브 탭 관리 ==========

// 전략 서브 탭 전환
function showStrategySubTab(tabType) {
    // 모든 서브 탭 버튼 비활성화
    document.querySelectorAll('.strategy-tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // 모든 서브 탭 콘텐츠 숨기기
    document.querySelectorAll('.strategy-content').forEach(content => {
        content.classList.remove('active');
    });

    // 선택된 버튼 활성화
    event.target.classList.add('active');

    // 선택된 콘텐츠 표시
    const contentId = `${tabType}StrategyTab`;
    document.getElementById(contentId).classList.add('active');
}

// 모든 전략 설정의 기본값
const DEFAULT_ALL_STRATEGY_SETTINGS = {
    // 단기 전략
    daytrading: {
        target: 2,
        stoploss: -1,
        volume: 200,
        maxtime: 240
    },
    scalping: {
        target: 0.5,
        stoploss: -0.3,
        maxtime: 180,
        spread: 100
    },
    swing: {
        target: 10,
        stoploss: -5,
        maxdays: 14,
        rsi_high: 70,
        rsi_low: 30
    },
    // 중기 전략
    trend: {
        target: 20,
        stoploss: -10,
        maxweeks: 12,
        ma_short: 60,
        ma_long: 120
    },
    momentum: {
        target: 30,
        stoploss: -12,
        period: 30,
        threshold: 15
    },
    // 장기 전략
    value: {
        target: 100,
        stoploss: -30,
        per_max: 15,
        pbr_max: 1.5,
        roe_min: 10,
        dividend_min: 2
    },
    growth: {
        target: 200,
        stoploss: -40,
        revenue_min: 20,
        profit_min: 30,
        min_holding: 12
    },
    dividend: {
        yield_min: 4,
        payout_min: 30,
        payout_max: 70,
        years_min: 5
    }
};

// 모든 전략 설정 불러오기
function loadAllStrategySettings() {
    const savedSettings = localStorage.getItem('allStrategySettings');
    const settings = savedSettings ? JSON.parse(savedSettings) : DEFAULT_ALL_STRATEGY_SETTINGS;

    // 단기 전략
    document.getElementById('daytrading_target').value = settings.daytrading.target;
    document.getElementById('daytrading_stoploss').value = settings.daytrading.stoploss;
    document.getElementById('daytrading_volume').value = settings.daytrading.volume;
    document.getElementById('daytrading_maxtime').value = settings.daytrading.maxtime;

    document.getElementById('scalping_target').value = settings.scalping.target;
    document.getElementById('scalping_stoploss').value = settings.scalping.stoploss;
    document.getElementById('scalping_maxtime').value = settings.scalping.maxtime;
    document.getElementById('scalping_spread').value = settings.scalping.spread;

    document.getElementById('swing_target').value = settings.swing.target;
    document.getElementById('swing_stoploss').value = settings.swing.stoploss;
    document.getElementById('swing_maxdays').value = settings.swing.maxdays;
    document.getElementById('swing_rsi_high').value = settings.swing.rsi_high;
    document.getElementById('swing_rsi_low').value = settings.swing.rsi_low;

    // 중기 전략
    document.getElementById('trend_target').value = settings.trend.target;
    document.getElementById('trend_stoploss').value = settings.trend.stoploss;
    document.getElementById('trend_maxweeks').value = settings.trend.maxweeks;
    document.getElementById('trend_ma_short').value = settings.trend.ma_short;
    document.getElementById('trend_ma_long').value = settings.trend.ma_long;

    document.getElementById('momentum_target').value = settings.momentum.target;
    document.getElementById('momentum_stoploss').value = settings.momentum.stoploss;
    document.getElementById('momentum_period').value = settings.momentum.period;
    document.getElementById('momentum_threshold').value = settings.momentum.threshold;

    // 장기 전략
    document.getElementById('value_target').value = settings.value.target;
    document.getElementById('value_stoploss').value = settings.value.stoploss;
    document.getElementById('value_per_max').value = settings.value.per_max;
    document.getElementById('value_pbr_max').value = settings.value.pbr_max;
    document.getElementById('value_roe_min').value = settings.value.roe_min;
    document.getElementById('value_dividend_min').value = settings.value.dividend_min;

    document.getElementById('growth_target').value = settings.growth.target;
    document.getElementById('growth_stoploss').value = settings.growth.stoploss;
    document.getElementById('growth_revenue_min').value = settings.growth.revenue_min;
    document.getElementById('growth_profit_min').value = settings.growth.profit_min;
    document.getElementById('growth_min_holding').value = settings.growth.min_holding;

    document.getElementById('dividend_yield_min').value = settings.dividend.yield_min;
    document.getElementById('dividend_payout_min').value = settings.dividend.payout_min;
    document.getElementById('dividend_payout_max').value = settings.dividend.payout_max;
    document.getElementById('dividend_years_min').value = settings.dividend.years_min;

    showStrategySettingsMessage('전략 설정을 불러왔습니다.', 'success');
}

// 모든 전략 설정 저장
async function saveAllStrategySettings() {
    const settings = {
        // 단기 전략
        daytrading: {
            target: parseFloat(document.getElementById('daytrading_target').value),
            stoploss: parseFloat(document.getElementById('daytrading_stoploss').value),
            volume: parseFloat(document.getElementById('daytrading_volume').value),
            maxtime: parseInt(document.getElementById('daytrading_maxtime').value)
        },
        scalping: {
            target: parseFloat(document.getElementById('scalping_target').value),
            stoploss: parseFloat(document.getElementById('scalping_stoploss').value),
            maxtime: parseInt(document.getElementById('scalping_maxtime').value),
            spread: parseInt(document.getElementById('scalping_spread').value)
        },
        swing: {
            target: parseFloat(document.getElementById('swing_target').value),
            stoploss: parseFloat(document.getElementById('swing_stoploss').value),
            maxdays: parseInt(document.getElementById('swing_maxdays').value),
            rsi_high: parseInt(document.getElementById('swing_rsi_high').value),
            rsi_low: parseInt(document.getElementById('swing_rsi_low').value)
        },
        // 중기 전략
        trend: {
            target: parseFloat(document.getElementById('trend_target').value),
            stoploss: parseFloat(document.getElementById('trend_stoploss').value),
            maxweeks: parseInt(document.getElementById('trend_maxweeks').value),
            ma_short: parseInt(document.getElementById('trend_ma_short').value),
            ma_long: parseInt(document.getElementById('trend_ma_long').value)
        },
        momentum: {
            target: parseFloat(document.getElementById('momentum_target').value),
            stoploss: parseFloat(document.getElementById('momentum_stoploss').value),
            period: parseInt(document.getElementById('momentum_period').value),
            threshold: parseFloat(document.getElementById('momentum_threshold').value)
        },
        // 장기 전략
        value: {
            target: parseFloat(document.getElementById('value_target').value),
            stoploss: parseFloat(document.getElementById('value_stoploss').value),
            per_max: parseFloat(document.getElementById('value_per_max').value),
            pbr_max: parseFloat(document.getElementById('value_pbr_max').value),
            roe_min: parseFloat(document.getElementById('value_roe_min').value),
            dividend_min: parseFloat(document.getElementById('value_dividend_min').value)
        },
        growth: {
            target: parseFloat(document.getElementById('growth_target').value),
            stoploss: parseFloat(document.getElementById('growth_stoploss').value),
            revenue_min: parseFloat(document.getElementById('growth_revenue_min').value),
            profit_min: parseFloat(document.getElementById('growth_profit_min').value),
            min_holding: parseInt(document.getElementById('growth_min_holding').value)
        },
        dividend: {
            yield_min: parseFloat(document.getElementById('dividend_yield_min').value),
            payout_min: parseFloat(document.getElementById('dividend_payout_min').value),
            payout_max: parseFloat(document.getElementById('dividend_payout_max').value),
            years_min: parseInt(document.getElementById('dividend_years_min').value)
        }
    };

    // 유효성 검사
    const validationErrors = [];

    // 손절 비율 검사
    if (settings.daytrading.stoploss > 0) validationErrors.push('데이트레이딩 손절 비율은 0 이하여야 합니다.');
    if (settings.scalping.stoploss > 0) validationErrors.push('스캘핑 손절 비율은 0 이하여야 합니다.');
    if (settings.swing.stoploss > 0) validationErrors.push('스윙 손절 비율은 0 이하여야 합니다.');
    if (settings.trend.stoploss > 0) validationErrors.push('추세추종 손절 비율은 0 이하여야 합니다.');
    if (settings.momentum.stoploss > 0) validationErrors.push('모멘텀 손절 비율은 0 이하여야 합니다.');
    if (settings.value.stoploss > 0) validationErrors.push('가치투자 손절 비율은 0 이하여야 합니다.');
    if (settings.growth.stoploss > 0) validationErrors.push('성장주 손절 비율은 0 이하여야 합니다.');

    // RSI 범위 검사
    if (settings.swing.rsi_low >= settings.swing.rsi_high) {
        validationErrors.push('스윙 RSI 과매도 기준은 과매수 기준보다 작아야 합니다.');
    }

    // 배당성향 범위 검사
    if (settings.dividend.payout_min >= settings.dividend.payout_max) {
        validationErrors.push('배당성향 최소값은 최대값보다 작아야 합니다.');
    }

    // 이동평균선 범위 검사
    if (settings.trend.ma_short >= settings.trend.ma_long) {
        validationErrors.push('단기 이동평균선은 장기 이동평균선보다 작아야 합니다.');
    }

    if (validationErrors.length > 0) {
        showStrategySettingsMessage('설정 오류:\n' + validationErrors.join('\n'), 'error');
        return;
    }

    // 로컬 스토리지에 저장
    localStorage.setItem('allStrategySettings', JSON.stringify(settings));

    // 백엔드에 저장 시도
    try {
        const result = await apiRequest('/api/settings/all-strategies', 'POST', settings);
        if (result && result.success) {
            showStrategySettingsMessage('모든 전략 설정이 저장되었습니다! ✅', 'success');
        } else {
            showStrategySettingsMessage('로컬에는 저장되었으나, 서버 동기화에 실패했습니다.', 'warning');
        }
    } catch (error) {
        showStrategySettingsMessage('전략 설정이 로컬에 저장되었습니다.', 'success');
    }
}

// 모든 전략 설정 초기화
function resetAllStrategySettings() {
    if (!confirm('모든 전략 설정을 기본값으로 초기화하시겠습니까?')) {
        return;
    }

    localStorage.setItem('allStrategySettings', JSON.stringify(DEFAULT_ALL_STRATEGY_SETTINGS));
    loadAllStrategySettings();
    showStrategySettingsMessage('모든 전략 설정이 기본값으로 초기화되었습니다.', 'success');
}

// 전략 설정 메시지 표시
function showStrategySettingsMessage(message, type = 'info') {
    const messageDiv = document.getElementById('strategySettingsMessage');
    messageDiv.textContent = message;
    messageDiv.className = `settings-message ${type}`;
    messageDiv.style.display = 'block';

    // 5초 후 메시지 숨기기
    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 5000);
}

// 현재 전략 설정 가져오기 (API에서 사용 가능)
function getAllStrategySettings() {
    const savedSettings = localStorage.getItem('allStrategySettings');
    return savedSettings ? JSON.parse(savedSettings) : DEFAULT_ALL_STRATEGY_SETTINGS;
}

// ========== 주식 상세정보 모달 ==========

// 주식 상세정보 모달 표시
async function showStockDetail(stockCode, stockName) {
    const modal = document.getElementById('stockDetailModal');
    const content = document.getElementById('stockDetailContent');

    // 모달 표시
    modal.style.display = 'block';

    // 로딩 표시
    content.innerHTML = '<div class="modal-loading"><p>상세정보 로딩 중...</p></div>';

    // 백엔드에서 상세정보 가져오기
    const result = await apiRequest(`/api/stock/detail/${stockCode}`);

    if (result && result.success) {
        const stock = result.data;
        content.innerHTML = `
            <div class="stock-detail-header">
                <h2>${stockName} (${stockCode})</h2>
                <div class="stock-price-info">
                    <span class="current-price">${stock.current_price?.toLocaleString() || '-'}원</span>
                    <span class="price-change ${stock.change_rate >= 0 ? 'positive' : 'negative'}">
                        ${stock.change_rate >= 0 ? '▲' : '▼'} ${Math.abs(stock.change_rate || 0).toFixed(2)}%
                    </span>
                </div>
            </div>

            <div class="stock-detail-tabs">
                <button class="stock-detail-tab-btn active" onclick="showStockDetailTab('overview')">개요</button>
                <button class="stock-detail-tab-btn" onclick="showStockDetailTab('financial')">재무제표</button>
                <button class="stock-detail-tab-btn" onclick="showStockDetailTab('valuation')">밸류에이션</button>
                <button class="stock-detail-tab-btn" onclick="showStockDetailTab('technical')">기술적 분석</button>
            </div>

            <!-- 개요 탭 -->
            <div id="overviewTab" class="stock-detail-content active">
                <h3>📊 주요 지표</h3>
                <div class="stock-metrics-grid">
                    <div class="metric-item">
                        <span class="metric-label">시가총액</span>
                        <span class="metric-value">${stock.market_cap ? (stock.market_cap / 100000000).toFixed(0) + '억원' : '-'}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">거래량</span>
                        <span class="metric-value">${stock.volume?.toLocaleString() || '-'}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">거래대금</span>
                        <span class="metric-value">${stock.trading_value ? (stock.trading_value / 100000000).toFixed(0) + '억원' : '-'}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">52주 최고가</span>
                        <span class="metric-value">${stock.week52_high?.toLocaleString() || '-'}원</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">52주 최저가</span>
                        <span class="metric-value">${stock.week52_low?.toLocaleString() || '-'}원</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">상장주식수</span>
                        <span class="metric-value">${stock.listed_shares ? (stock.listed_shares / 1000000).toFixed(2) + '백만주' : '-'}</span>
                    </div>
                </div>
            </div>

            <!-- 재무제표 탭 -->
            <div id="financialTab" class="stock-detail-content">
                <h3>💰 손익계산서</h3>
                <div class="financial-table">
                    <div class="financial-row">
                        <span class="financial-label">매출액</span>
                        <span class="financial-value">${stock.revenue ? (stock.revenue / 100000000).toFixed(0) + '억원' : '-'}</span>
                    </div>
                    <div class="financial-row">
                        <span class="financial-label">영업이익</span>
                        <span class="financial-value">${stock.operating_profit ? (stock.operating_profit / 100000000).toFixed(0) + '억원' : '-'}</span>
                    </div>
                    <div class="financial-row">
                        <span class="financial-label">당기순이익</span>
                        <span class="financial-value">${stock.net_income ? (stock.net_income / 100000000).toFixed(0) + '억원' : '-'}</span>
                    </div>
                    <div class="financial-row">
                        <span class="financial-label">영업이익률</span>
                        <span class="financial-value">${stock.operating_margin ? stock.operating_margin.toFixed(2) + '%' : '-'}</span>
                    </div>
                    <div class="financial-row">
                        <span class="financial-label">순이익률</span>
                        <span class="financial-value">${stock.net_margin ? stock.net_margin.toFixed(2) + '%' : '-'}</span>
                    </div>
                </div>

                <h3>💼 재무상태표</h3>
                <div class="financial-table">
                    <div class="financial-row">
                        <span class="financial-label">총자산</span>
                        <span class="financial-value">${stock.total_assets ? (stock.total_assets / 100000000).toFixed(0) + '억원' : '-'}</span>
                    </div>
                    <div class="financial-row">
                        <span class="financial-label">총부채</span>
                        <span class="financial-value">${stock.total_liabilities ? (stock.total_liabilities / 100000000).toFixed(0) + '억원' : '-'}</span>
                    </div>
                    <div class="financial-row">
                        <span class="financial-label">자본총계</span>
                        <span class="financial-value">${stock.total_equity ? (stock.total_equity / 100000000).toFixed(0) + '억원' : '-'}</span>
                    </div>
                    <div class="financial-row">
                        <span class="financial-label">부채비율</span>
                        <span class="financial-value">${stock.debt_ratio ? stock.debt_ratio.toFixed(2) + '%' : '-'}</span>
                    </div>
                </div>
            </div>

            <!-- 밸류에이션 탭 -->
            <div id="valuationTab" class="stock-detail-content">
                <h3>📈 주요 밸류에이션 지표</h3>
                <div class="valuation-grid">
                    <div class="valuation-item">
                        <span class="valuation-label">PER (주가수익비율)</span>
                        <span class="valuation-value">${stock.per?.toFixed(2) || '-'}</span>
                        <span class="valuation-desc">업종평균: ${stock.sector_avg_per?.toFixed(2) || '-'}</span>
                    </div>
                    <div class="valuation-item">
                        <span class="valuation-label">PBR (주가순자산비율)</span>
                        <span class="valuation-value">${stock.pbr?.toFixed(2) || '-'}</span>
                        <span class="valuation-desc">업종평균: ${stock.sector_avg_pbr?.toFixed(2) || '-'}</span>
                    </div>
                    <div class="valuation-item">
                        <span class="valuation-label">PSR (주가매출비율)</span>
                        <span class="valuation-value">${stock.psr?.toFixed(2) || '-'}</span>
                        <span class="valuation-desc">낮을수록 저평가</span>
                    </div>
                    <div class="valuation-item">
                        <span class="valuation-label">PCR (주가현금흐름비율)</span>
                        <span class="valuation-value">${stock.pcr?.toFixed(2) || '-'}</span>
                        <span class="valuation-desc">현금창출력 대비 평가</span>
                    </div>
                    <div class="valuation-item">
                        <span class="valuation-label">ROE (자기자본이익률)</span>
                        <span class="valuation-value">${stock.roe?.toFixed(2) || '-'}%</span>
                        <span class="valuation-desc">자본 대비 수익성</span>
                    </div>
                    <div class="valuation-item">
                        <span class="valuation-label">ROA (총자산이익률)</span>
                        <span class="valuation-value">${stock.roa?.toFixed(2) || '-'}%</span>
                        <span class="valuation-desc">자산 대비 수익성</span>
                    </div>
                    <div class="valuation-item">
                        <span class="valuation-label">EPS (주당순이익)</span>
                        <span class="valuation-value">${stock.eps?.toLocaleString() || '-'}원</span>
                        <span class="valuation-desc">주당 벌어들이는 이익</span>
                    </div>
                    <div class="valuation-item">
                        <span class="valuation-label">BPS (주당순자산)</span>
                        <span class="valuation-value">${stock.bps?.toLocaleString() || '-'}원</span>
                        <span class="valuation-desc">주당 순자산가치</span>
                    </div>
                    <div class="valuation-item">
                        <span class="valuation-label">배당수익률</span>
                        <span class="valuation-value">${stock.dividend_yield?.toFixed(2) || '-'}%</span>
                        <span class="valuation-desc">연간 배당금/주가</span>
                    </div>
                </div>
            </div>

            <!-- 기술적 분석 탭 -->
            <div id="technicalTab" class="stock-detail-content">
                <h3>📊 기술적 지표</h3>
                <div class="technical-table">
                    <div class="technical-row">
                        <span class="technical-label">RSI (14일)</span>
                        <span class="technical-value ${stock.rsi > 70 ? 'negative' : stock.rsi < 30 ? 'positive' : ''}">
                            ${stock.rsi?.toFixed(2) || '-'}
                        </span>
                        <span class="technical-status">
                            ${stock.rsi > 70 ? '과매수' : stock.rsi < 30 ? '과매도' : '중립'}
                        </span>
                    </div>
                    <div class="technical-row">
                        <span class="technical-label">MACD</span>
                        <span class="technical-value">${stock.macd?.toFixed(2) || '-'}</span>
                        <span class="technical-status">${stock.macd_signal || '-'}</span>
                    </div>
                    <div class="technical-row">
                        <span class="technical-label">이동평균선 (20일)</span>
                        <span class="technical-value">${stock.ma20?.toLocaleString() || '-'}원</span>
                        <span class="technical-status">
                            ${stock.current_price && stock.ma20 ? (stock.current_price > stock.ma20 ? '상승세' : '하락세') : '-'}
                        </span>
                    </div>
                    <div class="technical-row">
                        <span class="technical-label">이동평균선 (60일)</span>
                        <span class="technical-value">${stock.ma60?.toLocaleString() || '-'}원</span>
                        <span class="technical-status">
                            ${stock.current_price && stock.ma60 ? (stock.current_price > stock.ma60 ? '상승세' : '하락세') : '-'}
                        </span>
                    </div>
                    <div class="technical-row">
                        <span class="technical-label">볼린저 밴드 상단</span>
                        <span class="technical-value">${stock.bb_upper?.toLocaleString() || '-'}원</span>
                    </div>
                    <div class="technical-row">
                        <span class="technical-label">볼린저 밴드 하단</span>
                        <span class="technical-value">${stock.bb_lower?.toLocaleString() || '-'}원</span>
                    </div>
                </div>
            </div>
        `;
    } else {
        content.innerHTML = '<div class="modal-error"><p>상세정보를 불러올 수 없습니다.</p></div>';
    }
}

// 주식 상세정보 모달 닫기
function closeStockDetailModal() {
    document.getElementById('stockDetailModal').style.display = 'none';
}

// 주식 상세정보 탭 전환
function showStockDetailTab(tabName) {
    // 모든 버튼 비활성화
    document.querySelectorAll('.stock-detail-tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // 모든 콘텐츠 숨기기
    document.querySelectorAll('.stock-detail-content').forEach(content => {
        content.classList.remove('active');
    });

    // 선택된 버튼 활성화
    event.target.classList.add('active');

    // 선택된 콘텐츠 표시
    document.getElementById(`${tabName}Tab`).classList.add('active');
}

// ==================== 기타 탭 함수들 ====================

// 기타 탭 서브 탭 전환
function showOtherSubTab(subTabName) {
    // 모든 서브 탭 버튼 비활성화
    document.querySelectorAll('.sub-nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // 모든 서브 탭 숨기기
    document.querySelectorAll('.sub-tab').forEach(tab => {
        tab.classList.remove('active');
    });

    // 클릭된 버튼 활성화
    event.target.classList.add('active');

    // 선택된 서브 탭 표시
    document.getElementById(`${subTabName}SubTab`).classList.add('active');
}

// 정치인 주식 거래 데이터 로드
let politicianTradesData = []; // 전역 변수로 데이터 저장

async function loadPoliticianTrades() {
    const content = document.getElementById('politicianTradesContent');
    content.innerHTML = '<p class="loading">정치인 거래 데이터 로딩 중...</p>';

    try {
        const response = await fetch(`${API_BASE_URL}/api/scraper/capitol-trades`, {
            headers: { 'Authorization': authToken }
        });

        const data = await response.json();

        if (data.success) {
            politicianTradesData = data.trades || [];
            displayPoliticianTrades(politicianTradesData);
        } else {
            content.innerHTML = `<p class="error">오류: ${data.message}</p>`;
        }
    } catch (error) {
        console.error('Error loading politician trades:', error);
        content.innerHTML = '<p class="error">정치인 거래 데이터를 불러오는데 실패했습니다.</p>';
    }
}

// 정치인 거래 데이터 표시
function displayPoliticianTrades(trades) {
    const content = document.getElementById('politicianTradesContent');

    if (!trades || trades.length === 0) {
        content.innerHTML = '<p>표시할 거래 데이터가 없습니다.</p>';
        return;
    }

    let html = '';
    trades.forEach(trade => {
        const tradeType = trade.type === 'purchase' ? 'purchase' : 'sale';
        const tradeTypeText = trade.type === 'purchase' ? '매수' : '매도';

        html += `
            <div class="politician-trade-card">
                <div class="trade-header">
                    <div class="politician-name">${trade.politician}</div>
                    <div class="trade-badge ${tradeType}">${tradeTypeText}</div>
                </div>
                <div class="trade-details">
                    <div class="trade-detail-item">
                        <div class="trade-detail-label">종목</div>
                        <div class="trade-detail-value">${trade.ticker || 'N/A'}</div>
                    </div>
                    <div class="trade-detail-item">
                        <div class="trade-detail-label">종목명</div>
                        <div class="trade-detail-value">${trade.asset || 'N/A'}</div>
                    </div>
                    <div class="trade-detail-item">
                        <div class="trade-detail-label">거래일</div>
                        <div class="trade-detail-value">${trade.date || 'N/A'}</div>
                    </div>
                    <div class="trade-detail-item">
                        <div class="trade-detail-label">금액 범위</div>
                        <div class="trade-detail-value">${trade.amount || 'N/A'}</div>
                    </div>
                    ${trade.price ? `
                    <div class="trade-detail-item">
                        <div class="trade-detail-label">가격</div>
                        <div class="trade-detail-value">$${trade.price}</div>
                    </div>` : ''}
                </div>
            </div>
        `;
    });

    content.innerHTML = html;
}

// 정치인 데이터 필터링
function filterPoliticianData() {
    const politicianFilter = document.getElementById('politicianFilter').value;
    const tradeTypeFilter = document.getElementById('tradeTypeFilter').value;

    let filteredData = [...politicianTradesData];

    if (politicianFilter !== 'all') {
        filteredData = filteredData.filter(trade =>
            trade.politician.toLowerCase().includes(politicianFilter.replace('-', ' '))
        );
    }

    if (tradeTypeFilter !== 'all') {
        filteredData = filteredData.filter(trade => trade.type === tradeTypeFilter);
    }

    displayPoliticianTrades(filteredData);
}

// StockNear 데이터 로드
async function loadStockNearData() {
    const trendingContent = document.getElementById('stocknearTrending');
    const volumeContent = document.getElementById('stocknearVolume');
    const insiderContent = document.getElementById('stocknearInsider');
    const detailContent = document.getElementById('stocknearDetailContent');

    trendingContent.innerHTML = '<p class="loading">로딩 중...</p>';
    volumeContent.innerHTML = '<p class="loading">로딩 중...</p>';
    insiderContent.innerHTML = '<p class="loading">로딩 중...</p>';
    detailContent.innerHTML = '<p class="loading">StockNear 데이터 로딩 중...</p>';

    try {
        const response = await fetch(`${API_BASE_URL}/api/scraper/stocknear`, {
            headers: { 'Authorization': authToken }
        });

        const data = await response.json();

        if (data.success) {
            displayStockNearTrending(data.trending || []);
            displayStockNearVolume(data.volume || []);
            displayStockNearInsider(data.insider || []);
            displayStockNearDetail(data.detail || {});
        } else {
            const errorMsg = `<p class="error">오류: ${data.message}</p>`;
            trendingContent.innerHTML = errorMsg;
            volumeContent.innerHTML = errorMsg;
            insiderContent.innerHTML = errorMsg;
            detailContent.innerHTML = errorMsg;
        }
    } catch (error) {
        console.error('Error loading StockNear data:', error);
        const errorMsg = '<p class="error">StockNear 데이터를 불러오는데 실패했습니다.</p>';
        trendingContent.innerHTML = errorMsg;
        volumeContent.innerHTML = errorMsg;
        insiderContent.innerHTML = errorMsg;
        detailContent.innerHTML = errorMsg;
    }
}

function displayStockNearTrending(stocks) {
    const content = document.getElementById('stocknearTrending');
    if (!stocks || stocks.length === 0) {
        content.innerHTML = '<p>데이터 없음</p>';
        return;
    }

    let html = '';
    stocks.forEach(stock => {
        const changeClass = stock.change >= 0 ? 'stock-change-positive' : 'stock-change-negative';
        html += `
            <div class="stock-item">
                <div>
                    <div class="stock-symbol">${stock.symbol}</div>
                    <div>${stock.name || ''}</div>
                </div>
                <div class="<span class="${changeClass}">${stock.change > 0 ? '+' : ''}${stock.change}%</span>
            </div>
        `;
    });
    content.innerHTML = html;
}

function displayStockNearVolume(stocks) {
    const content = document.getElementById('stocknearVolume');
    if (!stocks || stocks.length === 0) {
        content.innerHTML = '<p>데이터 없음</p>';
        return;
    }

    let html = '';
    stocks.forEach(stock => {
        html += `
            <div class="stock-item">
                <div>
                    <div class="stock-symbol">${stock.symbol}</div>
                    <div>${stock.name || ''}</div>
                </div>
                <div>${stock.volume || 'N/A'}</div>
            </div>
        `;
    });
    content.innerHTML = html;
}

function displayStockNearInsider(trades) {
    const content = document.getElementById('stocknearInsider');
    if (!trades || trades.length === 0) {
        content.innerHTML = '<p>데이터 없음</p>';
        return;
    }

    let html = '';
    trades.forEach(trade => {
        html += `
            <div class="stock-item">
                <div>
                    <div class="stock-symbol">${trade.symbol}</div>
                    <div>${trade.insider || 'N/A'}</div>
                </div>
                <div>${trade.type || 'N/A'}</div>
            </div>
        `;
    });
    content.innerHTML = html;
}

function displayStockNearDetail(detail) {
    const content = document.getElementById('stocknearDetailContent');
    content.innerHTML = `<pre>${JSON.stringify(detail, null, 2)}</pre>`;
}

// StockAnalysis 데이터 로드
async function loadStockAnalysisData() {
    const metricsContent = document.getElementById('analysisMetrics');
    const financialsContent = document.getElementById('analysisFinancials');
    const valuationContent = document.getElementById('analysisValuation');
    const detailContent = document.getElementById('analysisDetailContent');

    metricsContent.innerHTML = '<p class="loading">로딩 중...</p>';
    financialsContent.innerHTML = '<p class="loading">로딩 중...</p>';
    valuationContent.innerHTML = '<p class="loading">로딩 중...</p>';
    detailContent.innerHTML = '<p class="loading">StockAnalysis 데이터 로딩 중...</p>';

    try {
        const response = await fetch(`${API_BASE_URL}/api/scraper/stock-analysis`, {
            headers: { 'Authorization': authToken }
        });

        const data = await response.json();

        if (data.success) {
            displayAnalysisMetrics(data.metrics || {});
            displayAnalysisFinancials(data.financials || {});
            displayAnalysisValuation(data.valuation || {});
            detailContent.innerHTML = '<p>종목을 검색하여 상세 분석을 확인하세요.</p>';
        } else {
            const errorMsg = `<p class="error">오류: ${data.message}</p>`;
            metricsContent.innerHTML = errorMsg;
            financialsContent.innerHTML = errorMsg;
            valuationContent.innerHTML = errorMsg;
            detailContent.innerHTML = errorMsg;
        }
    } catch (error) {
        console.error('Error loading StockAnalysis data:', error);
        const errorMsg = '<p class="error">StockAnalysis 데이터를 불러오는데 실패했습니다.</p>';
        metricsContent.innerHTML = errorMsg;
        financialsContent.innerHTML = errorMsg;
        valuationContent.innerHTML = errorMsg;
        detailContent.innerHTML = errorMsg;
    }
}

function displayAnalysisMetrics(metrics) {
    const content = document.getElementById('analysisMetrics');
    if (!metrics || Object.keys(metrics).length === 0) {
        content.innerHTML = '<p>데이터 없음</p>';
        return;
    }

    let html = '<div class="metrics-grid">';
    for (const [key, value] of Object.entries(metrics)) {
        html += `
            <div class="metric-item">
                <div class="metric-label">${key}</div>
                <div class="metric-value">${value}</div>
            </div>
        `;
    }
    html += '</div>';
    content.innerHTML = html;
}

function displayAnalysisFinancials(financials) {
    const content = document.getElementById('analysisFinancials');
    if (!financials || Object.keys(financials).length === 0) {
        content.innerHTML = '<p>데이터 없음</p>';
        return;
    }

    let html = '<div class="metrics-grid">';
    for (const [key, value] of Object.entries(financials)) {
        html += `
            <div class="metric-item">
                <div class="metric-label">${key}</div>
                <div class="metric-value">${value}</div>
            </div>
        `;
    }
    html += '</div>';
    content.innerHTML = html;
}

function displayAnalysisValuation(valuation) {
    const content = document.getElementById('analysisValuation');
    if (!valuation || Object.keys(valuation).length === 0) {
        content.innerHTML = '<p>데이터 없음</p>';
        return;
    }

    let html = '<div class="metrics-grid">';
    for (const [key, value] of Object.entries(valuation)) {
        html += `
            <div class="metric-item">
                <div class="metric-label">${key}</div>
                <div class="metric-value">${value}</div>
            </div>
        `;
    }
    html += '</div>';
    content.innerHTML = html;
}

// StockAnalysis 종목 검색
async function searchStockAnalysis() {
    const searchInput = document.getElementById('analysisStockSearch');
    const symbol = searchInput.value.trim().toUpperCase();

    if (!symbol) {
        alert('종목 심볼을 입력하세요.');
        return;
    }

    const detailContent = document.getElementById('analysisDetailContent');
    detailContent.innerHTML = '<p class="loading">검색 중...</p>';

    try {
        const response = await fetch(`${API_BASE_URL}/api/scraper/stock-analysis/${symbol}`, {
            headers: { 'Authorization': authToken }
        });

        const data = await response.json();

        if (data.success) {
            detailContent.innerHTML = `<pre>${JSON.stringify(data.data, null, 2)}</pre>`;
        } else {
            detailContent.innerHTML = `<p class="error">오류: ${data.message}</p>`;
        }
    } catch (error) {
        console.error('Error searching stock:', error);
        detailContent.innerHTML = '<p class="error">종목 검색에 실패했습니다.</p>';
    }
}

// ChartExchange 데이터 로드
async function loadChartExchangeData() {
    const technicalsContent = document.getElementById('chartTechnicals');
    const patternsContent = document.getElementById('chartPatterns');
    const tradingContent = document.getElementById('chartTrading');
    const detailContent = document.getElementById('chartDetailContent');

    technicalsContent.innerHTML = '<p class="loading">로딩 중...</p>';
    patternsContent.innerHTML = '<p class="loading">로딩 중...</p>';
    tradingContent.innerHTML = '<p class="loading">로딩 중...</p>';
    detailContent.innerHTML = '<p class="loading">ChartExchange 데이터 로딩 중...</p>';

    try {
        const response = await fetch(`${API_BASE_URL}/api/scraper/chart-exchange`, {
            headers: { 'Authorization': authToken }
        });

        const data = await response.json();

        if (data.success) {
            displayChartTechnicals(data.technicals || {});
            displayChartPatterns(data.patterns || []);
            displayChartTrading(data.trading || {});
            detailContent.innerHTML = '<p>종목을 검색하여 차트 분석을 확인하세요.</p>';
        } else {
            const errorMsg = `<p class="error">오류: ${data.message}</p>`;
            technicalsContent.innerHTML = errorMsg;
            patternsContent.innerHTML = errorMsg;
            tradingContent.innerHTML = errorMsg;
            detailContent.innerHTML = errorMsg;
        }
    } catch (error) {
        console.error('Error loading ChartExchange data:', error);
        const errorMsg = '<p class="error">ChartExchange 데이터를 불러오는데 실패했습니다.</p>';
        technicalsContent.innerHTML = errorMsg;
        patternsContent.innerHTML = errorMsg;
        tradingContent.innerHTML = errorMsg;
        detailContent.innerHTML = errorMsg;
    }
}

function displayChartTechnicals(technicals) {
    const content = document.getElementById('chartTechnicals');
    if (!technicals || Object.keys(technicals).length === 0) {
        content.innerHTML = '<p>데이터 없음</p>';
        return;
    }

    let html = '<div class="metrics-grid">';
    for (const [key, value] of Object.entries(technicals)) {
        html += `
            <div class="metric-item">
                <div class="metric-label">${key}</div>
                <div class="metric-value">${value}</div>
            </div>
        `;
    }
    html += '</div>';
    content.innerHTML = html;
}

function displayChartPatterns(patterns) {
    const content = document.getElementById('chartPatterns');
    if (!patterns || patterns.length === 0) {
        content.innerHTML = '<p>데이터 없음</p>';
        return;
    }

    let html = '<ul>';
    patterns.forEach(pattern => {
        html += `<li>${pattern}</li>`;
    });
    html += '</ul>';
    content.innerHTML = html;
}

function displayChartTrading(trading) {
    const content = document.getElementById('chartTrading');
    if (!trading || Object.keys(trading).length === 0) {
        content.innerHTML = '<p>데이터 없음</p>';
        return;
    }

    let html = '<div class="metrics-grid">';
    for (const [key, value] of Object.entries(trading)) {
        html += `
            <div class="metric-item">
                <div class="metric-label">${key}</div>
                <div class="metric-value">${value}</div>
            </div>
        `;
    }
    html += '</div>';
    content.innerHTML = html;
}

// ChartExchange 종목 검색
async function searchChartExchange() {
    const searchInput = document.getElementById('chartStockSearch');
    const symbol = searchInput.value.trim().toUpperCase();

    if (!symbol) {
        alert('종목 심볼을 입력하세요. (예: NASDAQ:MNDR)');
        return;
    }

    const detailContent = document.getElementById('chartDetailContent');
    detailContent.innerHTML = '<p class="loading">검색 중...</p>';

    try {
        const response = await fetch(`${API_BASE_URL}/api/scraper/chart-exchange/${encodeURIComponent(symbol)}`, {
            headers: { 'Authorization': authToken }
        });

        const data = await response.json();

        if (data.success) {
            detailContent.innerHTML = `<pre>${JSON.stringify(data.data, null, 2)}</pre>`;
        } else {
            detailContent.innerHTML = `<p class="error">오류: ${data.message}</p>`;
        }
    } catch (error) {
        console.error('Error searching chart:', error);
        detailContent.innerHTML = '<p class="error">종목 검색에 실패했습니다.</p>';
    }
}

// 페이지 로드 시 초기화
window.addEventListener('DOMContentLoaded', () => {
    // 이미 로그인되어 있는 경우
    if (authToken) {
        document.getElementById('loginPage').classList.remove('active');
        document.getElementById('mainPage').classList.add('active');
        loadDashboard();
    }

    // Enter 키로 로그인
    document.getElementById('password').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            login();
        }
    });

    // 모달 외부 클릭 시 닫기
    window.onclick = function(event) {
        const modal = document.getElementById('stockDetailModal');
        if (event.target === modal) {
            closeStockDetailModal();
        }
    };
});

/**
 * User Settings Management
 * Handles authentication and user settings
 */

const API_BASE_URL = 'http://localhost:5000/api';

// Token management
function getAccessToken() {
    return localStorage.getItem('access_token');
}

function getRefreshToken() {
    return localStorage.getItem('refresh_token');
}

function setTokens(accessToken, refreshToken) {
    localStorage.setItem('access_token', accessToken);
    if (refreshToken) {
        localStorage.setItem('refresh_token', refreshToken);
    }
}

function clearTokens() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('username');
}

function isLoggedIn() {
    return !!getAccessToken();
}

// Show alert message
function showAlert(message, type = 'success') {
    const alert = document.getElementById('alert');
    alert.textContent = message;
    alert.className = `alert ${type} show`;

    setTimeout(() => {
        alert.classList.remove('show');
    }, 5000);
}

// Toggle between login and register forms
function toggleAuthMode() {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const authTitle = document.getElementById('auth-title');

    if (loginForm.style.display === 'none') {
        loginForm.style.display = 'block';
        registerForm.style.display = 'none';
        authTitle.textContent = '로그인';
    } else {
        loginForm.style.display = 'none';
        registerForm.style.display = 'block';
        authTitle.textContent = '회원가입';
    }
}

// API request with authentication
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const token = getAccessToken();

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(url, {
            ...options,
            headers
        });

        const data = await response.json();

        // Handle token expiration
        if (response.status === 401 && token) {
            // Try to refresh token
            const refreshed = await refreshAccessToken();
            if (refreshed) {
                // Retry original request
                return apiRequest(endpoint, options);
            } else {
                // Refresh failed, logout
                logout();
                return { success: false, error: 'Session expired. Please login again.' };
            }
        }

        return data;

    } catch (error) {
        console.error('API Request Error:', error);
        return { success: false, error: error.message };
    }
}

// Refresh access token
async function refreshAccessToken() {
    const refreshToken = getRefreshToken();

    if (!refreshToken) {
        return false;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/user/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken })
        });

        const data = await response.json();

        if (data.success) {
            setTokens(data.access_token, null);
            return true;
        }

        return false;

    } catch (error) {
        console.error('Token refresh error:', error);
        return false;
    }
}

// Login
async function login(username, password) {
    const result = await apiRequest('/user/login', {
        method: 'POST',
        body: JSON.stringify({ username, password })
    });

    if (result.success) {
        setTokens(result.access_token, result.refresh_token);
        localStorage.setItem('username', username);
        return true;
    } else {
        showAlert(result.error || '로그인 실패', 'error');
        return false;
    }
}

// Register
async function register(username, password, email, fullName) {
    const result = await apiRequest('/user/register', {
        method: 'POST',
        body: JSON.stringify({
            username,
            password,
            email: email || undefined,
            full_name: fullName || undefined
        })
    });

    if (result.success) {
        setTokens(result.access_token, result.refresh_token);
        localStorage.setItem('username', username);
        return true;
    } else {
        showAlert(result.error || '회원가입 실패', 'error');
        return false;
    }
}

// Logout
function logout() {
    clearTokens();
    window.location.reload();
}

// Load user settings
async function loadUserSettings() {
    const result = await apiRequest('/user/settings');

    if (result.success && result.settings) {
        const settings = result.settings;

        // Populate form fields
        document.getElementById('investment-style').value = settings.investment_style || '';
        document.getElementById('risk-tolerance').value = settings.risk_tolerance || '';
        document.getElementById('max-position-size').value = settings.max_position_size || '';
        document.getElementById('max-positions').value = settings.max_positions || '';

        // Checkboxes
        document.getElementById('enable-telegram-notifications').checked = settings.enable_telegram_notifications || false;
        document.getElementById('enable-trade-alerts').checked = settings.enable_trade_alerts || false;
        document.getElementById('enable-monthly-reports').checked = settings.enable_monthly_reports || false;
    }
}

// Save user settings
async function saveUserSettings(formData) {
    const result = await apiRequest('/user/settings', {
        method: 'PUT',
        body: JSON.stringify(formData)
    });

    if (result.success) {
        showAlert('설정이 저장되었습니다.', 'success');
    } else {
        showAlert(result.error || '설정 저장 실패', 'error');
    }
}

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    const loggedIn = isLoggedIn();

    // Show/hide elements based on login status
    document.getElementById('auth-container').style.display = loggedIn ? 'none' : 'block';
    document.getElementById('settings-panel').style.display = loggedIn ? 'block' : 'none';
    document.getElementById('navbar').style.display = loggedIn ? 'flex' : 'none';

    if (loggedIn) {
        // Show username
        const username = localStorage.getItem('username');
        document.getElementById('username-display').textContent = `👤 ${username}`;

        // Load settings
        loadUserSettings();
    }

    // Login form handler
    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();

        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;

        const success = await login(username, password);

        if (success) {
            showAlert('로그인 성공!', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        }
    });

    // Register form handler
    document.getElementById('register-form').addEventListener('submit', async (e) => {
        e.preventDefault();

        const username = document.getElementById('reg-username').value;
        const email = document.getElementById('reg-email').value;
        const fullName = document.getElementById('reg-fullname').value;
        const password = document.getElementById('reg-password').value;
        const passwordConfirm = document.getElementById('reg-password-confirm').value;

        // Validate password match
        if (password !== passwordConfirm) {
            showAlert('비밀번호가 일치하지 않습니다.', 'error');
            return;
        }

        const success = await register(username, password, email, fullName);

        if (success) {
            showAlert('회원가입 성공!', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        }
    });

    // Settings form handler
    if (loggedIn) {
        document.getElementById('settings-form').addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = {
                investment_style: document.getElementById('investment-style').value || undefined,
                risk_tolerance: parseInt(document.getElementById('risk-tolerance').value) || undefined,
                max_position_size: parseInt(document.getElementById('max-position-size').value) || undefined,
                max_positions: parseInt(document.getElementById('max-positions').value) || undefined,
                telegram_bot_token: document.getElementById('telegram-bot-token').value || undefined,
                telegram_chat_id: document.getElementById('telegram-chat-id').value || undefined,
                enable_telegram_notifications: document.getElementById('enable-telegram-notifications').checked,
                enable_trade_alerts: document.getElementById('enable-trade-alerts').checked,
                enable_monthly_reports: document.getElementById('enable-monthly-reports').checked
            };

            // Remove undefined values
            Object.keys(formData).forEach(key => {
                if (formData[key] === undefined) {
                    delete formData[key];
                }
            });

            await saveUserSettings(formData);
        });
    }
});

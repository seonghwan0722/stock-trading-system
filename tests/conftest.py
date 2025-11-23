"""
Pytest Configuration and Shared Fixtures
"""

import pytest
import sys
import os
from unittest.mock import Mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))


@pytest.fixture
def app():
    """Flask app fixture"""
    from app import app as flask_app
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test-secret-key'
    yield flask_app


@pytest.fixture
def client(app):
    """Flask test client"""
    return app.test_client()


@pytest.fixture
def auth_headers():
    """Auth headers with mock token"""
    return {
        'Authorization': 'Bearer test-token',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def mock_kis_api():
    """Mock KIS API"""
    from api.kis_api import KISApi
    mock = Mock(spec=KISApi)
    mock.get_current_price.return_value = {
        'stock_code': '005930',
        'current_price': 70000,
        'change_rate': 2.5,
        'volume': 1000000
    }
    mock.get_balance.return_value = {
        'success': True,
        'cash_balance': 1000000,
        'positions': []
    }
    return mock


@pytest.fixture
def sample_stock_data():
    """Sample stock data"""
    return {
        'stock_code': '005930',
        'stock_name': 'º1ê',
        'current_price': 70000,
        'change_rate': 2.5,
        'volume': 1000000
    }

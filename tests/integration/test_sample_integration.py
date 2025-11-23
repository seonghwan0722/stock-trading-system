"""
샘플 통합 테스트
여러 모듈이 함께 동작하는 것을 테스트하는 예제
"""
import pytest


@pytest.mark.integration
class TestDatabaseIntegration:
    """데이터베이스 통합 테스트 (예제)"""

    def test_database_connection(self, temp_db_path):
        """데이터베이스 연결 테스트"""
        # 실제 구현 시 SQLite 연결 테스트
        assert temp_db_path is not None
        assert str(temp_db_path).endswith('.db')

    @pytest.mark.slow
    def test_company_data_retrieval(self, sample_stock_code):
        """종목 데이터 조회 테스트 (slow)"""
        # 실제 구현 시 DB에서 데이터 조회
        assert sample_stock_code is not None
        # TODO: 실제 DB 조회 로직 추가


@pytest.mark.integration
@pytest.mark.dart
class TestDARTAPIIntegration:
    """DART API 통합 테스트 (예제)"""

    def test_api_response_structure(self, mock_financial_data):
        """API 응답 구조 테스트"""
        assert "status" in mock_financial_data
        assert "message" in mock_financial_data
        assert "list" in mock_financial_data

    def test_financial_data_parsing(self, mock_financial_data):
        """재무 데이터 파싱 테스트"""
        data_list = mock_financial_data.get("list", [])
        assert len(data_list) > 0

        first_item = data_list[0]
        assert "account_nm" in first_item
        assert "thstrm_amount" in first_item

"""
샘플 유닛 테스트
DART API 클라이언트의 기본 기능을 테스트하는 예제
"""
import pytest


class TestSampleUnit:
    """샘플 유닛 테스트 클래스"""

    def test_basic_assertion(self):
        """기본 assertion 테스트"""
        assert 1 + 1 == 2

    def test_string_operations(self):
        """문자열 연산 테스트"""
        result = "Hello" + " " + "World"
        assert result == "Hello World"
        assert len(result) == 11

    def test_list_operations(self):
        """리스트 연산 테스트"""
        sample_list = [1, 2, 3]
        sample_list.append(4)
        assert len(sample_list) == 4
        assert 4 in sample_list


@pytest.mark.unit
class TestStockCodeValidation:
    """종목 코드 검증 테스트"""

    def test_valid_stock_code(self, sample_stock_code):
        """유효한 종목 코드 테스트"""
        assert len(sample_stock_code) == 6
        assert sample_stock_code.isdigit()

    def test_stock_code_format(self):
        """종목 코드 형식 테스트"""
        valid_codes = ["005930", "000660", "035720"]
        for code in valid_codes:
            assert len(code) == 6
            assert code.isdigit()

    def test_invalid_stock_code(self):
        """잘못된 종목 코드 테스트"""
        invalid_codes = ["12345", "ABCDEF", "123-456"]
        for code in invalid_codes:
            # 6자리 숫자가 아닌 경우
            is_valid = len(code) == 6 and code.isdigit()
            assert not is_valid


@pytest.mark.unit
class TestCompanyNameValidation:
    """회사명 검증 테스트"""

    def test_valid_company_name(self, sample_company_name):
        """유효한 회사명 테스트"""
        assert sample_company_name is not None
        assert len(sample_company_name) > 0

    def test_company_name_type(self, sample_company_name):
        """회사명 타입 테스트"""
        assert isinstance(sample_company_name, str)

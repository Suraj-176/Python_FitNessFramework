import pytest
from core.validators import RequestValidator, ValidationError

class TestRequestValidator:
    """Test input validation logic"""
    
    def test_validate_url_valid_http(self):
        """Valid HTTP URL should pass validation"""
        url = "http://api.example.com/users"
        result = RequestValidator.validate_url(url)
        assert result == url
    
    def test_validate_url_valid_https(self):
        """Valid HTTPS URL should pass validation"""
        url = "https://api.example.com/users"
        result = RequestValidator.validate_url(url)
        assert result == url
    
    def test_validate_url_empty_raises_error(self):
        """Empty URL should raise ValidationError"""
        with pytest.raises(ValidationError, match="URL cannot be empty"):
            RequestValidator.validate_url("")
    
    def test_validate_url_invalid_scheme_raises_error(self):
        """Invalid URL scheme should raise ValidationError"""
        with pytest.raises(ValidationError, match="URL must start with http:// or https://"):
            RequestValidator.validate_url("ftp://example.com")
    
    def test_validate_json_valid(self):
        """Valid JSON string should pass validation"""
        json_str = '{"name": "John", "age": 30}'
        result = RequestValidator.validate_json(json_str)
        assert result == json_str
    
    def test_validate_json_invalid_raises_error(self):
        """Invalid JSON should raise ValidationError"""
        with pytest.raises(ValidationError, match="Invalid JSON"):
            RequestValidator.validate_json('{"name": "John", age: 30}')
    
    def test_validate_status_code_valid(self):
        """Valid status code should pass validation"""
        assert RequestValidator.validate_status_code(200) == 200
        assert RequestValidator.validate_status_code(404) == 404
        assert RequestValidator.validate_status_code(500) == 500
    
    def test_validate_status_code_out_of_range_raises_error(self):
        """Status code outside 100-599 should raise ValidationError"""
        with pytest.raises(ValidationError, match="Status code must be between 100 and 599"):
            RequestValidator.validate_status_code(99)
        with pytest.raises(ValidationError, match="Status code must be between 100 and 599"):
            RequestValidator.validate_status_code(600)

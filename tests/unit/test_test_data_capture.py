import pytest
import json
from core.test_data_capture import TestDataCapture

class TestTestDataCapture:
    """Test data sanitization and masking logic"""
    
    def test_sanitize_authorization_header(self):
        """Authorization header should be redacted"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer my_secret_token_123"
        }
        sanitized = TestDataCapture.sanitize_headers(headers)
        assert sanitized["Content-Type"] == "application/json"
        assert sanitized["Authorization"] == "[REDACTED]"
        
    def test_sanitize_keys_header_case_insensitive(self):
        """Sensitive headers should be case-insensitive matched"""
        headers = {
            "X-API-KEY": "secret-key",
            "password": "my_password"
        }
        sanitized = TestDataCapture.sanitize_headers(headers)
        assert sanitized["X-API-KEY"] == "secret-key"  # Not in sensitive keys
        assert sanitized["password"] == "[REDACTED]"
        
    def test_sanitize_json_body(self):
        """JSON body passwords and secrets should be redacted"""
        body = '{"username": "admin", "password": "secret_password", "token": "abc123token"}'
        sanitized = TestDataCapture.sanitize_body(body)
        
        data = json.loads(sanitized)
        assert data["username"] == "admin"
        assert data["password"] == "[REDACTED]"
        assert data["token"] == "[REDACTED]"
        
    def test_sanitize_query_params_body(self):
        """Urlencoded body fields should be redacted via regex fallback"""
        body = "username=admin&password=secret_password&grant_type=password&client_secret=secret123"
        sanitized = TestDataCapture.sanitize_body(body)
        
        assert "username=admin" in sanitized
        assert "password=[REDACTED]" in sanitized
        assert "client_secret=[REDACTED]" in sanitized
        assert "grant_type=password" in sanitized
        
    def test_capture_payload_dictionary(self):
        """capture_payload should yield cleanly sanitized logs dictionary"""
        headers = {"Authorization": "Basic xxx", "Accept": "application/json"}
        body = '{"client_secret": "my_secret", "action": "test"}'
        
        payload = TestDataCapture.capture_payload("POST", "https://api.com", headers, body)
        
        assert payload["method"] == "POST"
        assert payload["url"] == "https://api.com"
        assert payload["headers"]["Authorization"] == "[REDACTED]"
        assert payload["headers"]["Accept"] == "application/json"
        
        body_data = json.loads(payload["body"])
        assert body_data["client_secret"] == "[REDACTED]"
        assert body_data["action"] == "test"

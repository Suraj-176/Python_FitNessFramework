import pytest
from fixtures.get_request_fixture import GetRequestFixture
from fixtures.post_request_fixture import PostRequestFixture
from fixtures.auth_fixture import AuthFixture
from core.config import Config

@pytest.mark.integration
class TestGetRequestIntegration:
    """Integration tests for GET requests"""
    
    def test_get_request_to_real_api(self):
        """GET request to public API should succeed"""
        fixture = GetRequestFixture()
        fixture.set_url("https://jsonplaceholder.typicode.com/posts/1")
        fixture.set_status_codes("200")
        
        result = fixture.execute()
        
        assert result is True
        assert fixture.get_response_status() == 200
        assert "userId" in fixture.get_response_body()
    
    def test_get_request_with_query_params(self):
        """GET request with query parameters should work"""
        fixture = GetRequestFixture()
        fixture.set_url("https://jsonplaceholder.typicode.com/posts?userId=1")
        fixture.set_status_codes("200")
        
        result = fixture.execute()
        
        assert result is True
        response = fixture.get_response_body_json()
        assert isinstance(response, list)
        assert len(response) > 0

@pytest.mark.integration
class TestPostRequestIntegration:
    """Integration tests for POST requests"""
    
    def test_post_request_with_json_body(self):
        """POST request with JSON body should succeed"""
        fixture = PostRequestFixture()
        fixture.set_url("https://jsonplaceholder.typicode.com/posts")
        fixture.set_body_json('{"title": "Test", "body": "Content", "userId": 1}')
        fixture.set_status_codes("201")
        
        result = fixture.execute()
        
        assert result is True
        assert fixture.get_response_status() == 201
        response = fixture.get_response_body_json()
        assert response.get("title") == "Test"

@pytest.mark.integration
class TestAuthenticationIntegration:
    """Integration tests for authentication flow"""
    
    def test_oauth2_password_flow(self):
        """OAuth2 password grant flow should work"""
        auth_fixture = AuthFixture()
        auth_fixture.set_auth_url("https://dummyjson.com/auth/login")
        auth_fixture.set_username("emilys")
        auth_fixture.set_password("emilyspass")
        auth_fixture.set_grant_type("password")
        
        success = auth_fixture.authenticate()
        
        assert success is True
        token = auth_fixture.get_access_token()
        assert token is not None
        assert len(token) > 0

@pytest.mark.integration
class TestRetryMechanism:
    """Integration tests for retry mechanism"""
    
    def test_retry_on_failure(self):
        """Failed request should retry automatically"""
        fixture = GetRequestFixture()
        fixture.set_url("https://httpstat.us/500")  # Always returns 500
        fixture.set_retries("2")
        fixture.set_retry_delay("0.5")
        fixture.set_status_codes("200")
        
        result = fixture.execute()
        
        # Should fail after retries
        assert result is False
        assert fixture.get_response_status() == 500

@pytest.mark.integration
class TestConfigurationIntegration:
    """Integration tests for configuration loading"""
    
    def test_load_config_from_environment(self):
        """Should load configuration from environment variables"""
        base_url = Config.get_base_url()
        assert base_url is not None
        assert base_url.startswith("http")

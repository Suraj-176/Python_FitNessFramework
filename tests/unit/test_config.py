import pytest
from unittest.mock import patch
from core.config import Config

class TestConfig:
    """Test configuration management"""
    
    def test_get_base_url_dev(self):
        """Dev environment should return dev URL"""
        with patch.dict('os.environ', {'ENVIRONMENT': 'dev', 'DEV_BASE_URL': 'https://dev.api.com'}):
            assert Config.get_base_url() == 'https://dev.api.com'
    
    def test_get_base_url_staging(self):
        """Staging environment should return staging URL"""
        with patch.dict('os.environ', {'ENVIRONMENT': 'staging', 'STAGING_BASE_URL': 'https://staging.api.com'}):
            assert Config.get_base_url() == 'https://staging.api.com'
    
    def test_get_base_url_uat(self):
        """UAT environment should return UAT URL"""
        with patch.dict('os.environ', {'ENVIRONMENT': 'uat', 'UAT_BASE_URL': 'https://uat.api.com'}):
            assert Config.get_base_url() == 'https://uat.api.com'
    
    def test_get_base_url_prod(self):
        """Prod environment should return prod URL"""
        with patch.dict('os.environ', {'ENVIRONMENT': 'prod', 'PROD_BASE_URL': 'https://api.com'}):
            assert Config.get_base_url() == 'https://api.com'
    
    def test_get_credentials_admin(self):
        """Should return admin credentials from environment"""
        with patch.dict('os.environ', {'API_ADMIN_USER': 'admin', 'API_ADMIN_PASS': 'secret123'}):
            user, pwd = Config.get_credentials('admin')
            assert user == 'admin'
            assert pwd == 'secret123'

    def test_get_credentials_qa(self):
        """Should return QA credentials from environment"""
        with patch.dict('os.environ', {'API_QA_USER': 'qa_user', 'API_QA_PASS': 'qa_secret'}):
            user, pwd = Config.get_credentials('qa')
            assert user == 'qa_user'
            assert pwd == 'qa_secret'

    def test_get_credentials_dev(self):
        """Should return dev credentials from environment"""
        with patch.dict('os.environ', {'API_DEV_USER': 'dev_user', 'API_DEV_PASS': 'dev_secret'}):
            user, pwd = Config.get_credentials('dev')
            assert user == 'dev_user'
            assert pwd == 'dev_secret'

    def test_get_credentials_reader(self):
        """Should return reader credentials from environment"""
        with patch.dict('os.environ', {'API_READER_USER': 'reader_user', 'API_READER_PASS': 'reader_secret'}):
            user, pwd = Config.get_credentials('reader')
            assert user == 'reader_user'
            assert pwd == 'reader_secret'
    
    def test_get_credentials_invalid_user_type(self):
        """Invalid user type should raise ValueError"""
        with pytest.raises(ValueError, match="Invalid user type"):
            Config.get_credentials('invalid_user')

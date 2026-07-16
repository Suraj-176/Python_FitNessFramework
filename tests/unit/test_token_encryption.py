import pytest
from core.token_encryption import TokenEncryption, SecureTokenStorage

class TestTokenEncryption:
    """Test token encryption functionality"""
    
    def test_encrypt_decrypt_roundtrip(self):
        """Encrypted token should decrypt back to original"""
        encryption = TokenEncryption()
        original = "my_secret_token_12345"
        
        encrypted = encryption.encrypt(original)
        decrypted = encryption.decrypt(encrypted)
        
        assert decrypted == original
        assert encrypted != original  # Ensure it's actually encrypted
    
    def test_encrypt_empty_string(self):
        """Empty string should encrypt and decrypt correctly"""
        encryption = TokenEncryption()
        original = ""
        
        encrypted = encryption.encrypt(original)
        decrypted = encryption.decrypt(encrypted)
        
        assert decrypted == original
    
    def test_decrypt_with_wrong_key_raises_error(self):
        """Decrypting with wrong key should fail"""
        from cryptography.fernet import Fernet
        encryption1 = TokenEncryption(Fernet.generate_key())
        encryption2 = TokenEncryption(Fernet.generate_key())  # Different key
        
        encrypted = encryption1.encrypt("secret")
        
        with pytest.raises(Exception):  # Fernet raises cryptography exceptions
            encryption2.decrypt(encrypted)
    
    def test_encrypt_unicode(self):
        """Unicode characters should encrypt and decrypt correctly"""
        encryption = TokenEncryption()
        original = "Token with émojis 🔐 and spëcial chars"
        
        encrypted = encryption.encrypt(original)
        decrypted = encryption.decrypt(encrypted)
        
        assert decrypted == original

class TestSecureTokenStorage:
    """Test secure token storage"""
    
    def test_store_and_retrieve_access_token(self):
        """Should store and retrieve access token"""
        storage = SecureTokenStorage()
        token = "access_token_xyz_12345"
        
        storage.store_access_token(token)
        retrieved = storage.get_access_token()
        
        assert retrieved == token
    
    def test_store_and_retrieve_refresh_token(self):
        """Should store and retrieve refresh token"""
        storage = SecureTokenStorage()
        token = "refresh_token_abc_67890"
        
        storage.store_refresh_token(token)
        retrieved = storage.get_refresh_token()
        
        assert retrieved == token
    
    def test_clear_tokens(self):
        """Should clear all stored tokens"""
        storage = SecureTokenStorage()
        
        storage.store_access_token("access_123")
        storage.store_refresh_token("refresh_456")
        storage.clear()
        
        assert storage.get_access_token() is None
        assert storage.get_refresh_token() is None

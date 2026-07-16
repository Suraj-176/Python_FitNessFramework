import os
from cryptography.fernet import Fernet

class TokenEncryption:
    """Class to encrypt and decrypt sensitive token strings"""
    
    def __init__(self, key=None):
        if not key:
            env_key = os.getenv("TOKEN_ENCRYPTION_KEY")
            if env_key and env_key != "generate_your_own_key_here":
                # Ensure it is converted to bytes for Fernet initialization
                self.key = env_key.encode('utf-8')
            else:
                self.key = Fernet.generate_key()
        else:
            self.key = key
        self.fernet = Fernet(self.key)
        
    def encrypt(self, plain_text: str) -> str:
        if plain_text is None:
            plain_text = ""
        return self.fernet.encrypt(plain_text.encode('utf-8')).decode('utf-8')
        
    def decrypt(self, encrypted_text: str) -> str:
        if encrypted_text is None:
            return ""
        return self.fernet.decrypt(encrypted_text.encode('utf-8')).decode('utf-8')

class SecureTokenStorage:
    """Mock storage class to store encrypted access and refresh tokens"""
    
    _access_token = None
    _refresh_token = None
    
    def store_access_token(self, token: str):
        SecureTokenStorage._access_token = token
        
    def get_access_token(self) -> str:
        return SecureTokenStorage._access_token
        
    def store_refresh_token(self, token: str):
        SecureTokenStorage._refresh_token = token
        
    def get_refresh_token(self) -> str:
        return SecureTokenStorage._refresh_token
        
    def clear(self):
        SecureTokenStorage._access_token = None
        SecureTokenStorage._refresh_token = None

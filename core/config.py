import os

def load_dotenv():
    # Attempt to locate and parse .env file from common directories
    for path in ['.env', '../.env', '../../.env']:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '=' in line:
                            key, val = line.split('=', 1)
                            key = key.strip()
                            val = val.strip().strip('"').strip("'")
                            os.environ[key] = val
            except Exception:
                pass
            break

# Auto-load environment parameters on module import
load_dotenv()

class Config:
    """Configuration helper class"""
    
    @staticmethod
    def get_base_url() -> str:
        env = os.getenv("ENVIRONMENT", "uat").lower()
        if env == "dev":
            return os.getenv("DEV_BASE_URL", "https://dev.api.com")
        elif env == "staging":
            return os.getenv("STAGING_BASE_URL", "https://staging.api.com")
        elif env == "uat":
            return os.getenv("UAT_BASE_URL", "https://uat.api.com")
        elif env == "prod":
            return os.getenv("PROD_BASE_URL", "https://api.com")
        return os.getenv("UAT_BASE_URL", "https://uat.api.com")
        
    @staticmethod
    def get_credentials(user_type: str) -> tuple:
        ut = str(user_type).lower().strip()
        if ut == "admin":
            return (os.getenv("API_ADMIN_USER", "admin"), os.getenv("API_ADMIN_PASS", "secret123"))
        elif ut == "qa":
            return (os.getenv("API_QA_USER", "qa"), os.getenv("API_QA_PASS", "changeme456!"))
        elif ut == "dev":
            return (os.getenv("API_DEV_USER", "dev"), os.getenv("API_DEV_PASS", "changeme789!"))
        elif ut == "reader":
            return (os.getenv("API_READER_USER", "reader"), os.getenv("API_READER_PASS", "readonly123!"))
        else:
            raise ValueError("Invalid user type")

import json
import re

class TestDataCapture:
    """Helper class to capture, format, and sanitize execution logs and data payloads."""
    
    SENSITIVE_KEYS = {"authorization", "password", "token", "secret", "api_key", "client_secret"}
    
    @staticmethod
    def sanitize_headers(headers: dict) -> dict:
        if not headers:
            return {}
        sanitized = {}
        for k, v in headers.items():
            if k.lower() in TestDataCapture.SENSITIVE_KEYS:
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = v
        return sanitized
        
    @staticmethod
    def sanitize_body(body: str) -> str:
        if not body:
            return ""
        # Try to parse as JSON and sanitize keys
        try:
            data = json.loads(body)
            sanitized_data = TestDataCapture._sanitize_dict(data)
            return json.dumps(sanitized_data)
        except Exception:
            # Fallback to Regex replacement for raw strings/query params
            sanitized = body
            for key in TestDataCapture.SENSITIVE_KEYS:
                # Replace pattern like "password":"value" or password=value
                pattern = rf'("?{key}"?\s*[:=]\s*)"([^"]*)"'
                sanitized = re.sub(pattern, r'\1"[REDACTED]"', sanitized, flags=re.IGNORECASE)
                # handle urlencoded query params like password=value
                query_pattern = rf'({key}=)([^&]*)'
                sanitized = re.sub(query_pattern, r'\1[REDACTED]', sanitized, flags=re.IGNORECASE)
            return sanitized
            
    @staticmethod
    def _sanitize_dict(data):
        if isinstance(data, dict):
            return {k: ("[REDACTED]" if k.lower() in TestDataCapture.SENSITIVE_KEYS else TestDataCapture._sanitize_dict(v)) for k, v in data.items()}
        elif isinstance(data, list):
            return [TestDataCapture._sanitize_dict(item) for item in data]
        return data

    @staticmethod
    def capture_payload(method: str, url: str, headers: dict, body: str) -> dict:
        return {
            "method": method,
            "url": url,
            "headers": TestDataCapture.sanitize_headers(headers),
            "body": TestDataCapture.sanitize_body(body)
        }

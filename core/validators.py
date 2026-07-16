import json

class ValidationError(Exception):
    """Custom validation error class"""
    pass

class RequestValidator:
    """Validator helper class for Request inputs"""
    
    @staticmethod
    def validate_url(url: str) -> str:
        if not url:
            raise ValidationError("URL cannot be empty")
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ValidationError("URL must start with http:// or https://")
        return url
        
    @staticmethod
    def validate_json(json_str: str) -> str:
        try:
            json.loads(json_str)
            return json_str
        except Exception:
            raise ValidationError("Invalid JSON")
            
    @staticmethod
    def validate_status_code(code: int) -> int:
        try:
            icode = int(code)
        except Exception:
            raise ValidationError("Status code must be an integer")
        if icode < 100 or icode > 599:
            raise ValidationError("Status code must be between 100 and 599")
        return icode

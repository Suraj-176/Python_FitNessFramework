import json
import requests
from typing import List

class AuthFixture:
    """
    Python SLIM Decision Table fixture for bearer-token authentication.
    Generates a token via POST login and stores it statically so all other
    fixtures (Get/Post/Put/Patch/Delete) pick it up automatically.
    """
    _auth_token = ""  # Static/Class variable to share token across requests

    def __init__(self) -> None:
        self._token_url: str = ""
        self._body_json: str = "{}"
        self._token_field: str = "token"
        self._expected_codes: List[int] = []
        
        self._actual_status_code: int = 0
        self._response_body: str = ""

    @classmethod
    def get_stored_token(cls) -> str:
        """Returns the currently stored bearer token."""
        return cls._auth_token

    @classmethod
    def set_stored_token(cls, token: str) -> None:
        """Sets the stored bearer token statically."""
        cls._auth_token = token

    @classmethod
    def clear_token(cls) -> None:
        """Clears the stored token."""
        cls._auth_token = ""

    # Setters mapped to columns
    def set_token_url(self, token_url: str) -> None:
        self._token_url = token_url

    def set_body_json(self, body_json: str) -> None:
        self._body_json = body_json

    def set_token_field(self, token_field: str) -> None:
        self._token_field = token_field

    def set_status_codes(self, codes: str) -> None:
        self._expected_codes = []
        for code in codes.split(","):
            try:
                self._expected_codes.append(int(code.strip()))
            except ValueError:
                print(f"Invalid status code: {code}")

    # Action mapped to execute
    def generate_token(self) -> bool:
        """Sends a POST request to generate the token and stores it statically."""
        try:
            # Automatically unescape HTML entities (like &quot;) in the request body!
            import html
            unescaped_body = html.unescape(self._body_json)
            
            headers = {"Content-Type": "application/json"}
            response = requests.post(self._token_url, data=unescaped_body.encode('utf-8'), headers=headers, timeout=15)
            
            self._actual_status_code = response.status_code
            self._response_body = response.text
            
            if response.status_code != 200:
                print(f"[Auth] FAILED code={response.status_code} body={response.text}")
                return False

            try:
                json_data = response.json()
            except Exception:
                print(f"[Auth] Invalid JSON response body: {response.text}")
                return False

            # Extract the token field (supports nested dictionary optString fallback)
            token = json_data.get(self._token_field, "")
            if not token:
                print(f"[Auth] Token field '{self._token_field}' not found in response: {response.text}")
                return False

            AuthFixture._auth_token = str(token)
            print("[Auth] Token acquired successfully.")
            return True

        except Exception as e:
            print(f"[Auth] Exception: {str(e)}")
            return False

    # Getters/Assertions mapped to columns
    def actual_status_code(self) -> int:
        return self._actual_status_code

    def status_code(self) -> str:
        """Returns the actual status code as a string."""
        return str(self._actual_status_code)

    def status_codes(self) -> str:
        if not self._expected_codes:
            return str(self._actual_status_code)
        if self._actual_status_code in self._expected_codes:
            return str(self._actual_status_code)
        return f"{self._actual_status_code} (expected: {self._expected_codes})"

    def token(self) -> str:
        """Returns the dynamically generated token."""
        return AuthFixture._auth_token

    def response_body(self) -> str:
        """Returns the pretty-printed JSON response body wrapped in preformatted code tags."""
        try:
            # Try to parse and pretty-print JSON response
            json_data = json.loads(self._response_body)
            pretty_json = json.dumps(json_data, indent=2)
            return f"\n{{{{\n{pretty_json}\n}}}}\n"
        except Exception:
            return f"\n{{{{\n{self._response_body}\n}}}}\n"

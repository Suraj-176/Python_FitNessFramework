import html
import json
import base64
import requests
import time
from typing import List
from .json_utils import extract_json_field
from core.logger import logger, log_request, log_response

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
        self._basic_auth_header: str = ""
        
        self._actual_status_code: int = 0
        self._response_body: str = ""
        self._response_body_json: dict = {}
        self._response_time_ms: int = 0

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
    def setTokenUrl(self, token_url: str) -> None:
        self.set_token_url(token_url)
        
    def set_url(self, url: str) -> None:
        """Alias to support 'url' column natively, matching PostRequestFixture."""
        self._token_url = url
    def setUrl(self, url: str) -> None:
        self.set_url(url)

    def set_body_json(self, body_json: str) -> None:
        self._body_json = body_json
    def setBodyJson(self, body_json: str) -> None:
        self.set_body_json(body_json)

    def set_token_field(self, token_field: str) -> None:
        self._token_field = token_field
    def setTokenField(self, token_field: str) -> None:
        self.set_token_field(token_field)

    def set_basic_auth(self, credentials: str) -> None:
        unescaped_cred = html.unescape(credentials)
        if ":" in unescaped_cred:
            user, pwd = unescaped_cred.split(":", 1)
            encoded = base64.b64encode(f"{user}:{pwd}".encode("utf-8")).decode("utf-8")
            self._basic_auth_header = f"Basic {encoded}"
        else:
            logger.warning(f"[Auth] Invalid basic auth format: '{credentials}'")
    def setBasicAuth(self, credentials: str) -> None:
        self.set_basic_auth(credentials)

    def set_status_codes(self, codes: str) -> None:
        self._expected_codes = []
        for code in codes.split(","):
            try:
                self._expected_codes.append(int(code.strip()))
            except ValueError:
                logger.warning(f"[Auth] Invalid status code: {code}")
    def setStatusCodes(self, codes: str) -> None:
        self.set_status_codes(codes)

    # Action mapped to execute
    def execute(self) -> bool:
        """Standard Decision Table execution alias."""
        return self.generate_token()

    def generate_token(self) -> bool:
        """Sends a POST request to generate the token and stores it statically."""
        try:
            unescaped_body = html.unescape(self._body_json)
            
            headers = {"Content-Type": "application/json"}
            if self._basic_auth_header:
                headers["Authorization"] = self._basic_auth_header

            # Log Request
            log_request("POST", self._token_url, headers=headers, payload=unescaped_body)

            start = time.perf_counter()
            
            try:
                # NATIVE JSON serialization to match Postman! 🟢
                json_payload = json.loads(unescaped_body)
                response = requests.post(self._token_url, json=json_payload, headers=headers, timeout=15)
            except Exception:
                # Fallback to raw data bytes
                response = requests.post(self._token_url, data=unescaped_body.encode('utf-8'), headers=headers, timeout=15)
                
            self._response_time_ms = int((time.perf_counter() - start) * 1000)
            self._actual_status_code = response.status_code
            self._response_body = response.text

            try:
                self._response_body_json = response.json()
            except Exception:
                self._response_body_json = {}

            # Log Response
            log_response(self._actual_status_code, self._response_body, dict(response.headers))

            if response.status_code != 200:
                logger.error(f"[Auth] FAILED code={response.status_code} body={response.text}")
                return False

            if not self._response_body_json:
                logger.error(f"[Auth] Invalid JSON response body: {response.text}")
                return False

            token = extract_json_field(self._response_body_json, self._token_field)
            if not token or token in ("key not found", "no key set"):
                logger.error(f"[Auth] Token field '{self._token_field}' not found in response: {response.text}")
                return False

            AuthFixture._auth_token = token
            logger.info("[Auth] Token acquired successfully.")
            
            # Auto-generate our 3rd-party corporate HTML report dynamically on the fly!
            try:
                from core.report_generator import generate_html_report
                generate_html_report()
            except Exception as e:
                logger.error(f"[Report] Failed to trigger report generator: {e}")
                
            return True

        except requests.exceptions.Timeout:
            logger.error(f"[Auth] Timeout [{self._token_url}]")
            return False
        except requests.exceptions.ConnectionError as e:
            logger.error(f"[Auth] Connection error [{self._token_url}]: {e}")
            return False
        except Exception as e:
            logger.error(f"[Auth] Exception: {e}")
            return False

    # Getters/Assertions mapped to columns
    def actual_status_code(self) -> int:
        return self._actual_status_code

    def status_code(self) -> str:
        return str(self._actual_status_code)

    def status_codes(self) -> str:
        if not self._expected_codes:
            return str(self._actual_status_code)
        if self._actual_status_code in self._expected_codes:
            return str(self._actual_status_code)
        return f"{self._actual_status_code} (expected: {self._expected_codes})"

    def response_time(self) -> int:
        return self._response_time_ms

    def token(self) -> str:
        return AuthFixture._auth_token

    def response_body(self) -> str:
        try:
            json_data = json.loads(self._response_body)
            pretty_json = json.dumps(json_data, indent=2)
            return f"\n{{{{\n{pretty_json}\n}}}}\n"
        except Exception:
            return f"\n{{{{\n{self._response_body}\n}}}}\n"

import html
import json
import time
import base64
from typing import List, Optional
import requests
from .auth_fixture import AuthFixture
from .json_utils import extract_json_field
from core.logger import logger, log_request, log_response

class BaseRequestFixture:
    """
    Shared engine inherited by Get/Post/Put/Patch/Delete fixtures.
    Handles: auth injection, timing, status checks, JSONPath lookups, logging.
    """
    def __init__(self) -> None:
        self._url: str = ""
        self._body_json: str = ""
        self._key: str = ""
        self._expected_codes: List[int] = []
        self._basic_auth_header: str = ""

        self._executed: bool = False
        self._actual_status_code: int = 0
        self._response_body: str = ""
        self._response_time_ms: int = 0
        self._response_body_json: dict = {}

    # Setters (Supporting both camelCase and snake_case natively for compatibility!)
    def set_url(self, url: str) -> None:
        self._url = url
    def setUrl(self, url: str) -> None:
        self.set_url(url)

    def set_body_json(self, body_json: str) -> None:
        self._body_json = body_json
    def setBodyJson(self, body_json: str) -> None:
        self.set_body_json(body_json)

    def set_key(self, key: str) -> None:
        self._key = key
    def setKey(self, key: str) -> None:
        self.set_key(key)

    def set_basic_auth(self, credentials: str) -> None:
        """
        Sets Basic Authentication header.
        Format inside FitNesse cell: username:password (e.g. suraj:Sur$0402)
        """
        unescaped_cred = html.unescape(credentials)
        if ":" in unescaped_cred:
            user, pwd = unescaped_cred.split(":", 1)
            encoded = base64.b64encode(f"{user}:{pwd}".encode("utf-8")).decode("utf-8")
            self._basic_auth_header = f"Basic {encoded}"
        else:
            logger.warning(f"Invalid basic auth format: '{credentials}'")
    def setBasicAuth(self, credentials: str) -> None:
        self.set_basic_auth(credentials)

    def set_status_codes(self, codes: str) -> None:
        self._expected_codes = []
        for code in codes.split(","):
            try:
                self._expected_codes.append(int(code.strip()))
            except ValueError:
                logger.warning(f"Invalid status code: {code}")
    def setStatusCodes(self, codes: str) -> None:
        self.set_status_codes(codes)

    def _make_request(self, method: str) -> bool:
        try:
            headers: dict = {}
            
            # Use Basic Auth if specified, otherwise fall back to cached Bearer Token
            if self._basic_auth_header:
                headers["Authorization"] = self._basic_auth_header
            else:
                token = AuthFixture.get_stored_token()
                if token:
                    headers["Authorization"] = f"Bearer {token}"

            unescaped_body = html.unescape(self._body_json)
            
            # Log Request
            log_request(method, self._url, headers=headers, payload=unescaped_body or None)

            start = time.perf_counter()
            
            # Perform POST / PUT / PATCH natively with dictionary payloads if available!
            if method in ("POST", "PUT", "PATCH") and unescaped_body:
                try:
                    json_payload = json.loads(unescaped_body)
                    response = requests.request(method, self._url, json=json_payload, headers=headers, timeout=15)
                except Exception:
                    response = requests.request(method, self._url, data=unescaped_body.encode('utf-8'), headers=headers, timeout=15)
            else:
                response = requests.request(method, self._url, headers=headers, timeout=15)
                
            self._response_time_ms = int((time.perf_counter() - start) * 1000)
            self._actual_status_code = response.status_code
            self._response_body = response.text

            try:
                self._response_body_json = response.json()
            except Exception:
                self._response_body_json = {}

            # Log Response
            log_response(self._actual_status_code, self._response_body, dict(response.headers))
            logger.info(f"[{method}] {self._url} -> {self._actual_status_code} ({self._response_time_ms}ms)")
            
            # Auto-generate our 3rd-party corporate HTML report dynamically on the fly!
            try:
                from core.report_generator import generate_html_report
                generate_html_report()
            except Exception as e:
                logger.error(f"[Report] Failed to trigger report generator: {e}")
            
            self._executed = True
            return True

        except Exception as e:
            logger.error(f"[{method}] Unexpected exception [{self._url}]: {str(e)}")
            return False

    def executed(self) -> bool:
        return self._executed

    def actual_status_code(self) -> int:
        return self._actual_status_code

    def status_code(self) -> str:
        """Returns the actual status code as a string (supports statusCode?)."""
        return str(self._actual_status_code)

    def response_body(self) -> str:
        try:
            json_data = json.loads(self._response_body)
            pretty_json = json.dumps(json_data, indent=2)
            return f"\n{{{{\n{pretty_json}\n}}}}\n"
        except Exception:
            return f"\n{{{{\n{self._response_body}\n}}}}\n"

    def response_time(self) -> int:
        return self._response_time_ms

    def status_codes(self) -> str:
        if not self._expected_codes:
            return str(self._actual_status_code)
        if self._actual_status_code in self._expected_codes:
            return str(self._actual_status_code)
        return f"{self._actual_status_code} (expected: {self._expected_codes})"

    def response_field(self) -> str:
        return extract_json_field(self._response_body_json, self._key)

    def json_value(self) -> str:
        return self.response_field()

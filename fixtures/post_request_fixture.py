import json
import html
from core.logger import logger, log_request, log_response
import time
from typing import List, Optional
import requests
from .auth_fixture import AuthFixture

class PostRequestFixture:
    def __init__(self) -> None:
        self._url: str = ""
        self._body_json: str = "{}"
        self._key: str = ""
        self._expected_codes: List[int] = []
        self._executed: bool = False
        self._actual_status_code: int = 0
        self._response_body: str = ""
        self._response_time_ms: int = 0
        self._response_body_json: dict = {}

    def set_url(self, url: str) -> None:
        self._url = url

    def set_body_json(self, body_json: str) -> None:
        self._body_json = body_json

    def set_key(self, key: str) -> None:
        self._key = key

    def set_status_codes(self, codes: str) -> None:
        self._expected_codes = []
        for code in codes.split(","):
            try:
                self._expected_codes.append(int(code.strip()))
            except ValueError:
                logger.warning(f"Invalid status code: {code}")

    def execute(self) -> bool:
        try:
            headers = {"Content-Type": "application/json"}
            token = AuthFixture.get_stored_token()
            if token:
                headers["Authorization"] = f"Bearer {token}"

            # Log Request
            log_request("POST", self._url, headers=headers, payload=html.unescape(self._body_json))

            start = time.perf_counter()
            response = requests.post(self._url, json=json.loads(html.unescape(self._body_json)), headers=headers, timeout=15)
            self._response_time_ms = int((time.perf_counter() - start) * 1000)

            self._actual_status_code = response.status_code
            self._response_body = response.text

            try:
                self._response_body_json = response.json()
            except Exception:
                self._response_body_json = {}

            # Log Response
            log_response(self._actual_status_code, self._response_body, dict(response.headers))
            logger.info(f"[POST] {self._url} -> {self._actual_status_code} ({self._response_time_ms}ms)")
            
            self._executed = True
            return True

        except Exception as e:
            logger.error(f"[POST] Exception [{self._url}]: {str(e)}")
            return False

    def executed(self) -> bool:
        return self._executed

    def actual_status_code(self) -> int:
        return self._actual_status_code

    def response_body(self) -> str:
        return self._response_body

    def response_time(self) -> int:
        return self._response_time_ms

    def status_codes(self) -> str:
        if not self._expected_codes:
            return str(self._actual_status_code)
        if self._actual_status_code in self._expected_codes:
            return str(self._actual_status_code)
        return f"{self._actual_status_code} (expected: {self._expected_codes})"

    def response_field(self) -> str:
        if not self._key:
            return "no key set"
        try:
            if self._key.startswith("$."):
                path_parts = self._key[2:].split(".")
                val = self._response_body_json
                for part in path_parts:
                    val = val[part]
                return str(val)
            else:
                return str(self._response_body_json.get(self._key, "key not found"))
        except Exception:
            return "key not found"

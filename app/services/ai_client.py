"""Client for the external AI completion service, with retries and typed errors."""
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

import requests

from app.config import settings
from app.core.constants import FALLBACK_REPLY
from app.core.instruction import Instruction

logger = logging.getLogger(__name__)


class APIErrorType(Enum):
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    AUTH_ERROR = "auth_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    SERVER_ERROR = "server_error"
    INVALID_RESPONSE = "invalid_response"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class APIConfig:
    base_url: str = settings.api_base_url
    token: str = settings.api_token
    model: str = settings.ai_model
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    fallback_message: str = FALLBACK_REPLY


@dataclass
class APIResponse:
    success: bool
    content: str
    error_type: Optional[APIErrorType] = None
    status_code: Optional[int] = None
    response_time: Optional[float] = None


_RETRYABLE_ERRORS = {
    APIErrorType.NETWORK_ERROR,
    APIErrorType.TIMEOUT_ERROR,
    APIErrorType.SERVER_ERROR,
}

_ERROR_MESSAGES = {
    APIErrorType.NETWORK_ERROR: "Network connection failed",
    APIErrorType.AUTH_ERROR: "Authentication failed - check API token",
    APIErrorType.RATE_LIMIT_ERROR: "Rate limit exceeded - too many requests",
    APIErrorType.INVALID_RESPONSE: "Invalid or empty response from API",
    APIErrorType.UNKNOWN_ERROR: "Unknown error occurred",
}


class AIClient:
    """AI completion client with exponential-backoff retries."""

    def __init__(self, config: Optional[APIConfig] = None) -> None:
        self.config = config or APIConfig()
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "Authorization": f"Bearer {self.config.token}",
                "Content-Type": "application/json",
                "User-Agent": "PrincessSelene-Bot/2.0",
            }
        )
        return session

    def get_response(self, user_message: str) -> str:
        """Get an AI reply, falling back to a friendly stock message on failure."""
        response = self._request_with_retry(user_message)
        if response.success:
            logger.info("API request successful in %.2fs", response.response_time or 0.0)
            return response.content

        self._log_error(response)
        return self.config.fallback_message

    def health_check(self) -> bool:
        try:
            return self._make_single_request("Hello").success
        except Exception:
            return False

    def _request_with_retry(self, user_message: str) -> APIResponse:
        last_response: Optional[APIResponse] = None

        for attempt in range(self.config.max_retries):
            try:
                response = self._make_single_request(user_message)
            except Exception as exc:
                logger.error("Unexpected error during API request: %s", exc)
                response = APIResponse(success=False, content="", error_type=APIErrorType.UNKNOWN_ERROR)

            if response.success or response.error_type not in _RETRYABLE_ERRORS:
                return response

            last_response = response
            if attempt < self.config.max_retries - 1:
                delay = self.config.retry_delay * (2 ** attempt)
                logger.warning("Retrying API request in %.1fs (attempt %d)", delay, attempt + 1)
                time.sleep(delay)

        return last_response or APIResponse(success=False, content="", error_type=APIErrorType.UNKNOWN_ERROR)

    def _make_single_request(self, user_message: str) -> APIResponse:
        start = time.time()
        url = f"{self.config.base_url}{self.config.model}"
        payload = self._build_payload(user_message)

        try:
            response = self.session.post(url, json=payload, timeout=self.config.timeout)
            return self._process_response(response, time.time() - start)
        except requests.exceptions.Timeout:
            return APIResponse(success=False, content="", error_type=APIErrorType.TIMEOUT_ERROR, response_time=time.time() - start)
        except requests.exceptions.ConnectionError:
            return APIResponse(success=False, content="", error_type=APIErrorType.NETWORK_ERROR, response_time=time.time() - start)
        except requests.exceptions.RequestException:
            return APIResponse(success=False, content="", error_type=APIErrorType.NETWORK_ERROR, response_time=time.time() - start)

    def _build_payload(self, user_message: str) -> Dict[str, Any]:
        return {
            "messages": [
                {"role": "system", "content": Instruction.system_prompt()},
                {"role": "user", "content": user_message},
            ]
        }

    def _process_response(self, response: requests.Response, response_time: float) -> APIResponse:
        try:
            data = response.json()
        except ValueError:
            return APIResponse(False, "", APIErrorType.INVALID_RESPONSE, response.status_code, response_time)

        if response.status_code == 401:
            return APIResponse(False, "", APIErrorType.AUTH_ERROR, response.status_code, response_time)
        if response.status_code == 429:
            return APIResponse(False, "", APIErrorType.RATE_LIMIT_ERROR, response.status_code, response_time)
        if response.status_code >= 500:
            return APIResponse(False, "", APIErrorType.SERVER_ERROR, response.status_code, response_time)
        if not response.ok:
            return APIResponse(False, "", APIErrorType.UNKNOWN_ERROR, response.status_code, response_time)

        if data.get("success") and data.get("result", {}).get("response"):
            return APIResponse(True, data["result"]["response"], status_code=response.status_code, response_time=response_time)

        return APIResponse(False, "", APIErrorType.INVALID_RESPONSE, response.status_code, response_time)

    def _log_error(self, response: APIResponse) -> None:
        if response.error_type == APIErrorType.TIMEOUT_ERROR:
            message = f"Request timed out after {self.config.timeout}s"
        elif response.error_type == APIErrorType.SERVER_ERROR:
            message = f"Server error (HTTP {response.status_code})"
        else:
            message = _ERROR_MESSAGES.get(response.error_type, "Unexpected error")

        if response.response_time:
            message += f" (took {response.response_time:.2f}s)"
        logger.error("API request failed: %s", message)

    def __enter__(self) -> "AIClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.session.close()


_client: Optional[AIClient] = None


def get_ai_client() -> AIClient:
    """Return the process-wide singleton AI client."""
    global _client
    if _client is None:
        _client = AIClient()
    return _client

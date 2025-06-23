"""API client for external AI service with enhanced error handling and configuration."""
import requests
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import time
from config import API_BASE_URL, API_TOKEN
from instruction import Instruction

logger = logging.getLogger(__name__)

class APIErrorType(Enum):
    """Types of API errors for better error categorization."""
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    AUTH_ERROR = "auth_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    SERVER_ERROR = "server_error"
    INVALID_RESPONSE = "invalid_response"
    UNKNOWN_ERROR = "unknown_error"

@dataclass
class APIConfig:
    """API configuration with defaults."""
    base_url: str = API_BASE_URL
    token: str = API_TOKEN
    model: str = "@cf/meta/llama-3-8b-instruct"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    fallback_message: str = "Oops! Something went wrong. 😅"

@dataclass
class APIResponse:
    """Structured API response with metadata."""
    success: bool
    content: str
    error_type: Optional[APIErrorType] = None
    status_code: Optional[int] = None
    response_time: Optional[float] = None

class AIAPIClient:
    """Enhanced AI API client with robust error handling and retry logic."""
    
    def __init__(self, config: Optional[APIConfig] = None):
        self.config = config or APIConfig()
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create configured requests session with connection pooling."""
        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {self.config.token}",
            "Content-Type": "application/json",
            "User-Agent": "PrincessSelene-Bot/1.0"
        })
        return session
    
    def get_response(self, user_message: str) -> str:
        """Get AI response with comprehensive error handling."""
        api_response = self._make_request_with_retry(user_message)
        
        if api_response.success:
            logger.info(f"API request successful in {api_response.response_time:.2f}s")
            return api_response.content
        
        self._log_error(api_response)
        return self.config.fallback_message
    
    def _make_request_with_retry(self, user_message: str) -> APIResponse:
        """Make API request with retry logic."""
        last_response = None
        
        for attempt in range(self.config.max_retries):
            try:
                response = self._make_single_request(user_message)
                
                if response.success or response.error_type not in [
                    APIErrorType.NETWORK_ERROR,
                    APIErrorType.TIMEOUT_ERROR,
                    APIErrorType.SERVER_ERROR
                ]:
                    return response
                
                last_response = response
                
                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Retrying API request in {delay}s (attempt {attempt + 1})")
                    time.sleep(delay)
                    
            except Exception as e:
                logger.error(f"Unexpected error during API request: {e}")
                last_response = APIResponse(
                    success=False,
                    content="",
                    error_type=APIErrorType.UNKNOWN_ERROR
                )
        
        return last_response or APIResponse(
            success=False,
            content="",
            error_type=APIErrorType.UNKNOWN_ERROR
        )
    
    def _make_single_request(self, user_message: str) -> APIResponse:
        """Make single API request with timing and error handling."""
        start_time = time.time()
        
        payload = self._build_payload(user_message)
        url = f"{self.config.base_url}{self.config.model}"
        
        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=self.config.timeout
            )
            
            response_time = time.time() - start_time
            
            return self._process_response(response, response_time)
            
        except requests.exceptions.Timeout:
            return APIResponse(
                success=False,
                content="",
                error_type=APIErrorType.TIMEOUT_ERROR,
                response_time=time.time() - start_time
            )
        except requests.exceptions.ConnectionError:
            return APIResponse(
                success=False,
                content="",
                error_type=APIErrorType.NETWORK_ERROR,
                response_time=time.time() - start_time
            )
        except requests.exceptions.RequestException as e:
            return APIResponse(
                success=False,
                content="",
                error_type=APIErrorType.NETWORK_ERROR,
                response_time=time.time() - start_time
            )
    
    def _build_payload(self, user_message: str) -> Dict[str, Any]:
        """Build API request payload."""
        return {
            "messages": [
                {"role": "system", "content": Instruction.system_prompt()},
                {"role": "user", "content": user_message}
            ]
        }
    
    def _process_response(self, response: requests.Response, response_time: float) -> APIResponse:
        """Process HTTP response and extract content."""
        try:
            data = response.json()
        except ValueError:
            return APIResponse(
                success=False,
                content="",
                error_type=APIErrorType.INVALID_RESPONSE,
                status_code=response.status_code,
                response_time=response_time
            )
        
        if response.status_code == 401:
            return APIResponse(
                success=False,
                content="",
                error_type=APIErrorType.AUTH_ERROR,
                status_code=response.status_code,
                response_time=response_time
            )
        elif response.status_code == 429:
            return APIResponse(
                success=False,
                content="",
                error_type=APIErrorType.RATE_LIMIT_ERROR,
                status_code=response.status_code,
                response_time=response_time
            )
        elif response.status_code >= 500:
            return APIResponse(
                success=False,
                content="",
                error_type=APIErrorType.SERVER_ERROR,
                status_code=response.status_code,
                response_time=response_time
            )
        elif not response.ok:
            return APIResponse(
                success=False,
                content="",
                error_type=APIErrorType.UNKNOWN_ERROR,
                status_code=response.status_code,
                response_time=response_time
            )
        
        if data.get('success', False):
            content = data.get('result', {}).get('response', '')
            if content:
                return APIResponse(
                    success=True,
                    content=content,
                    status_code=response.status_code,
                    response_time=response_time
                )
        
        return APIResponse(
            success=False,
            content="",
            error_type=APIErrorType.INVALID_RESPONSE,
            status_code=response.status_code,
            response_time=response_time
        )
    
    def _log_error(self, api_response: APIResponse) -> None:
        """Log API errors with appropriate detail level."""
        error_messages = {
            APIErrorType.NETWORK_ERROR: "Network connection failed",
            APIErrorType.TIMEOUT_ERROR: f"Request timed out after {self.config.timeout}s",
            APIErrorType.AUTH_ERROR: "Authentication failed - check API token",
            APIErrorType.RATE_LIMIT_ERROR: "Rate limit exceeded - too many requests",
            APIErrorType.SERVER_ERROR: f"Server error (HTTP {api_response.status_code})",
            APIErrorType.INVALID_RESPONSE: "Invalid or empty response from API",
            APIErrorType.UNKNOWN_ERROR: "Unknown error occurred"
        }
        
        message = error_messages.get(api_response.error_type, "Unexpected error")
        
        if api_response.response_time:
            message += f" (took {api_response.response_time:.2f}s)"
        
        logger.error(f"API request failed: {message}")
    
    def health_check(self) -> bool:
        """Check API health with a simple test request."""
        try:
            response = self._make_single_request("Hello")
            return response.success
        except Exception:
            return False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session."""
        self.session.close()

# Singleton instance for easy access
_client_instance = None

def get_api_client() -> AIAPIClient:
    """Get singleton API client instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = AIAPIClient()
    return _client_instance

# Backward compatibility
class ScorpiAPI:
    """Legacy API wrapper for backward compatibility."""
    
    @staticmethod
    def get_response(user_message: str) -> str:
        """Legacy method - use AIAPIClient directly for new code."""
        return get_api_client().get_response(user_message)
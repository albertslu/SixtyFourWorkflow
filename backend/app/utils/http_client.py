"""
HTTP client utilities and configuration
"""
import httpx
from typing import Dict, Any, Optional
from loguru import logger

from core.config import settings


class HTTPClient:
    """Configured HTTP client for external API calls"""
    
    def __init__(self):
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
        
    async def create_client(self, headers: Optional[Dict[str, str]] = None) -> httpx.AsyncClient:
        """Create an async HTTP client with proper configuration"""
        default_headers = {
            "User-Agent": "SixtyFour-Workflow-Engine/1.0.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        if headers:
            default_headers.update(headers)
            
        return httpx.AsyncClient(
            headers=default_headers,
            timeout=self.timeout,
            limits=self.limits,
            follow_redirects=True
        )
    
    async def make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        """Make an HTTP request with proper error handling"""
        
        async with await self.create_client(headers) as client:
            try:
                logger.info(f"Making {method.upper()} request to {url}")
                
                response = await client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params
                )
                
                logger.info(f"Response: {response.status_code} from {url}")
                return response
                
            except httpx.TimeoutException:
                logger.error(f"Request to {url} timed out")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error for {url}: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error for {url}: {str(e)}")
                raise


# Global HTTP client instance
http_client = HTTPClient()

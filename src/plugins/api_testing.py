"""
API Testing Plugin for JARVIS 2.0

HTTP API testing framework with:
- Request building and execution
- Response validation
- Test assertions
- Performance monitoring
- Mock server support
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
import aiohttp
from src.core.tools.base import BaseTool, ToolParameter


@dataclass
class APIRequest:
    """API request configuration"""
    method: str
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    body: Optional[Dict[str, Any]] = None
    timeout: int = 30


@dataclass
class APIResponse:
    """API response data"""
    status_code: int
    headers: Dict[str, str]
    body: Any
    response_time: float
    success: bool
    error: Optional[str] = None


@dataclass
class TestAssertion:
    """Test assertion result"""
    assertion_type: str
    expected: Any
    actual: Any
    passed: bool
    message: str


class APITester:
    """API testing engine"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.test_results: List[Dict[str, Any]] = []
    
    async def execute_request(self, request: APIRequest) -> APIResponse:
        """Execute HTTP request"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        start_time = time.time()
        
        try:
            async with self.session.request(
                method=request.method,
                url=request.url,
                headers=request.headers,
                params=request.params,
                json=request.body,
                timeout=aiohttp.ClientTimeout(total=request.timeout)
            ) as response:
                response_time = time.time() - start_time
                
                # Try to parse as JSON
                try:
                    body = await response.json()
                except:
                    body = await response.text()
                
                return APIResponse(
                    status_code=response.status,
                    headers=dict(response.headers),
                    body=body,
                    response_time=response_time,
                    success=200 <= response.status < 300
                )
        except asyncio.TimeoutError:
            return APIResponse(
                status_code=0,
                headers={},
                body=None,
                response_time=time.time() - start_time,
                success=False,
                error="Request timeout"
            )
        except Exception as e:
            return APIResponse(
                status_code=0,
                headers={},
                body=None,
                response_time=time.time() - start_time,
                success=False,
                error=str(e)
            )
    
    def assert_status_code(self, response: APIResponse, expected: int) -> TestAssertion:
        """Assert status code"""
        passed = response.status_code == expected
        return TestAssertion(
            assertion_type="status_code",
            expected=expected,
            actual=response.status_code,
            passed=passed,
            message=f"Status code {'matches' if passed else 'does not match'}"
        )
    
    def assert_response_time(self, response: APIResponse, max_time: float) -> TestAssertion:
        """Assert response time"""
        passed = response.response_time <= max_time
        return TestAssertion(
            assertion_type="response_time",
            expected=f"<= {max_time}s",
            actual=f"{response.response_time:.3f}s",
            passed=passed,
            message=f"Response time {'within' if passed else 'exceeds'} limit"
        )
    
    def assert_contains(self, response: APIResponse, field: str, value: Any) -> TestAssertion:
        """Assert response contains field with value"""
        if not isinstance(response.body, dict):
            return TestAssertion(
                assertion_type="contains",
                expected=value,
                actual=None,
                passed=False,
                message="Response body is not JSON object"
            )
        
        actual = response.body.get(field)
        passed = actual == value
        
        return TestAssertion(
            assertion_type="contains",
            expected=value,
            actual=actual,
            passed=passed,
            message=f"Field '{field}' {'matches' if passed else 'does not match'}"
        )
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()


class APITestingTool(BaseTool):
    """API testing tool"""
    
    def __init__(self):
        super().__init__()
        self.tester = APITester()
    
    def get_parameters(self) -> Dict[str, ToolParameter]:
        """Get tool parameters"""
        return {
            "action": ToolParameter(
                name="action",
                type="string",
                description="API testing action",
                required=True,
                enum=[
                    "send_request", "get", "post", "put", "delete",
                    "assert_status", "assert_time", "assert_contains",
                    "run_test_suite", "get_results", "clear_results"
                ]
            ),
            "url": ToolParameter(
                name="url",
                type="string",
                description="API endpoint URL",
                required=False
            ),
            "method": ToolParameter(
                name="method",
                type="string",
                description="HTTP method",
                required=False
            ),
            "headers": ToolParameter(
                name="headers",
                type="object",
                description="Request headers",
                required=False
            ),
            "body": ToolParameter(
                name="body",
                type="object",
                description="Request body",
                required=False
            )
        }
    
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute API testing action"""
        
        if action == "send_request":
            return await self._send_request(**kwargs)
        elif action == "get":
            return await self._get(**kwargs)
        elif action == "post":
            return await self._post(**kwargs)
        elif action == "put":
            return await self._put(**kwargs)
        elif action == "delete":
            return await self._delete(**kwargs)
        elif action == "assert_status":
            return self._assert_status(**kwargs)
        elif action == "assert_time":
            return self._assert_time(**kwargs)
        elif action == "assert_contains":
            return self._assert_contains(**kwargs)
        elif action == "get_results":
            return self._get_results(**kwargs)
        elif action == "clear_results":
            return self._clear_results(**kwargs)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
    
    async def _send_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        **kwargs
    ) -> Dict[str, Any]:
        """Send HTTP request"""
        request = APIRequest(
            method=method.upper(),
            url=url,
            headers=headers or {},
            params=params or {},
            body=body,
            timeout=timeout
        )
        
        response = await self.tester.execute_request(request)
        
        result = {
            "success": response.success,
            "status_code": response.status_code,
            "response_time": response.response_time,
            "body": response.body,
            "headers": dict(response.headers),
            "error": response.error
        }
        
        self.tester.test_results.append({
            "request": asdict(request),
            "response": result,
            "timestamp": time.time()
        })
        
        return result
    
    async def _get(self, url: str, **kwargs) -> Dict[str, Any]:
        """Send GET request"""
        return await self._send_request(method="GET", url=url, **kwargs)
    
    async def _post(self, url: str, body: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Send POST request"""
        return await self._send_request(method="POST", url=url, body=body, **kwargs)
    
    async def _put(self, url: str, body: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Send PUT request"""
        return await self._send_request(method="PUT", url=url, body=body, **kwargs)
    
    async def _delete(self, url: str, **kwargs) -> Dict[str, Any]:
        """Send DELETE request"""
        return await self._send_request(method="DELETE", url=url, **kwargs)
    
    def _assert_status(
        self,
        response: Dict[str, Any],
        expected_status: int,
        **kwargs
    ) -> Dict[str, Any]:
        """Assert status code"""
        actual = response.get("status_code", 0)
        passed = actual == expected_status
        
        return {
            "success": True,
            "assertion": "status_code",
            "passed": passed,
            "expected": expected_status,
            "actual": actual,
            "message": f"Status code {'matches' if passed else 'does not match'}"
        }
    
    def _assert_time(
        self,
        response: Dict[str, Any],
        max_time: float,
        **kwargs
    ) -> Dict[str, Any]:
        """Assert response time"""
        actual = response.get("response_time", 0)
        passed = actual <= max_time
        
        return {
            "success": True,
            "assertion": "response_time",
            "passed": passed,
            "expected": f"<= {max_time}s",
            "actual": f"{actual:.3f}s",
            "message": f"Response time {'within' if passed else 'exceeds'} limit"
        }
    
    def _assert_contains(
        self,
        response: Dict[str, Any],
        field: str,
        value: Any,
        **kwargs
    ) -> Dict[str, Any]:
        """Assert response contains field"""
        body = response.get("body", {})
        if not isinstance(body, dict):
            return {
                "success": True,
                "assertion": "contains",
                "passed": False,
                "expected": value,
                "actual": None,
                "message": "Response body is not JSON"
            }
        
        actual = body.get(field)
        passed = actual == value
        
        return {
            "success": True,
            "assertion": "contains",
            "passed": passed,
            "expected": value,
            "actual": actual,
            "message": f"Field '{field}' {'matches' if passed else 'does not match'}"
        }
    
    def _get_results(self, **kwargs) -> Dict[str, Any]:
        """Get test results"""
        return {
            "success": True,
            "results": self.tester.test_results,
            "count": len(self.tester.test_results)
        }
    
    def _clear_results(self, **kwargs) -> Dict[str, Any]:
        """Clear test results"""
        count = len(self.tester.test_results)
        self.tester.test_results = []
        
        return {
            "success": True,
            "message": f"Cleared {count} test results",
            "count": count
        }
    
    async def __del__(self):
        """Cleanup"""
        await self.tester.close()

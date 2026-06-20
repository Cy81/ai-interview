import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.services.common.redis import redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """基于 Redis 的滑动窗口速率限制中间件"""

    def __init__(self, app, requests_per_minute: int = None):
        super().__init__(app)
        self.rpm = requests_per_minute or settings.RATE_LIMIT_PER_MINUTE

    async def dispatch(self, request: Request, call_next):
        # 跳过文档和健康检查路径
        path = request.url.path
        if path in ("/", "/docs", "/redoc", "/openapi.json") or path.startswith("/api-docs"):
            return await call_next(request)

        # 获取客户端标识
        client_ip = request.client.host if request.client else "unknown"
        # 对已认证用户用 user_id 限流，否则用 IP
        user_id = None
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            # 简单提取 token 做 key，不验证（验证留给依赖注入）
            user_id = auth_header[7:23]  # 取 token 前 16 字符作为标识

        rate_key = f"rate:{user_id or client_ip}"

        try:
            pipe = redis_client.pipeline()
            pipe.incr(rate_key)
            pipe.expire(rate_key, 60)
            results = await pipe.execute()
            current_count = results[0]

            if current_count > self.rpm:
                return JSONResponse(
                    status_code=429,
                    content={"message": "请求过于频繁，请稍后再试", "code": 429},
                    headers={"Retry-After": "60"}
                )

            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(self.rpm)
            response.headers["X-RateLimit-Remaining"] = str(max(0, self.rpm - current_count))
            return response

        except Exception as e:
            # Redis 故障时放行，不限流
            logger.warning(f"Rate limiter Redis error: {e}")
            return await call_next(request)

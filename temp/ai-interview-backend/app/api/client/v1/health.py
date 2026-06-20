from fastapi import APIRouter
from app.schemas.response import ApiResponse
from app.db.session import get_db
from sqlalchemy import text

router = APIRouter()


@router.get("")
async def health_check():
    """健康检查端点"""
    health_status = {
        "status": "healthy",
        "services": {
            "api": "up",
            "database": "unknown",
        }
    }

    try:
        async for db in get_db():
            result = await db.execute(text("SELECT 1"))
            if result.scalar() == 1:
                health_status["services"]["database"] = "up"
            break
    except Exception:
        health_status["services"]["database"] = "down"
        health_status["status"] = "unhealthy"

    if health_status["status"] == "unhealthy":
        return ApiResponse.failed(
            message="Service unhealthy",
            body_code=503,
            http_code=503,
            data=health_status
        )

    return ApiResponse.success(data=health_status)

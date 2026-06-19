from app.route import create_app
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

app = create_app()

if __name__ == "__main__":
    import uvicorn

    # For production environment, recommend using config file to start
    uvicorn.run(
    "main:app",
    host="0.0.0.0",
    port=settings.API_PORT,
    reload=settings.ENV == "development",
    workers=1 if settings.ENV == "development" else 4,
    env_file=".env",
    reload_excludes=["logs/*", "uploads/*", "*.db"],  # 排除日志和上传目录
)


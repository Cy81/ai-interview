# 导入 Base 供其他模块使用
from app.db.base import Base  # noqa: F401

# 导入所有模型，确保 Alembic 能发现它们
from app.models.base import BaseModel  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.admin import Admin  # noqa: F401
from app.models.token import Token  # noqa: F401

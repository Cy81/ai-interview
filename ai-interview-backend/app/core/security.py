from datetime import datetime, timedelta, UTC
from typing import Optional, Dict
from jose import jwt, JWTError
from app.core.config import settings
import uuid
import bcrypt


def _hash_password(password: str) -> str:
    """使用 bcrypt 哈希密码（直接调用，不依赖 passlib）"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    """验证 bcrypt 密码"""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


class AuthBase:
    @staticmethod
    def create_access_token(
        subject: str,
        scope: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建访问令牌"""
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode = {
            "exp": expire,
            "sub": str(subject),
            "scope": scope,  # 添加 scope 以区分权限
            "jti": str(uuid.uuid4())  # 唯一标识符
        }
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def create_refresh_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
        """创建刷新令牌"""
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode = {
            "exp": expire,
            "sub": str(subject),
            "jti": str(uuid.uuid4()),
            "scope": "refresh"
        }
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def verify_token(token: str, scope: str = None) -> Optional[Dict]:
        """验证令牌"""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            if scope and payload.get("scope") != scope:
                return None
            return payload
        except JWTError:
            return None

    @staticmethod
    def hash_token(token: str) -> str:
        """对令牌进行哈希"""
        return _hash_password(token)

    @staticmethod
    def verify_token_hash(plain_token: str, hashed_token: str) -> bool:
        """验证令牌哈希"""
        return _verify_password(plain_token, hashed_token)

from typing import Optional
from pydantic import EmailStr
from ..base import BaseSchema


class UserProfile(BaseSchema):
    id: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    phone_country_code: Optional[str] = None
    is_verified: bool = False
    email_verified_at: Optional[str] = None
    last_active_at: Optional[str] = None

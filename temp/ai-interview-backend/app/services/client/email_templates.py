"""
Client email template service
Send verification codes and other emails using SMTP
"""
from app.services.common.email_smtp import (
    send_verification_email,
    send_password_reset_email,
    send_welcome_email,
)


class ClientEmailService:
    @staticmethod
    async def send_registration_verification(email: str, verification_code: str, user_name: str = None):
        """Send registration verification code email"""
        await send_verification_email(
            email=email,
            verification_code=verification_code,
            first_name=user_name or "User",
            expires_minutes=10
        )

    @staticmethod
    async def send_password_reset_code(email: str, verification_code: str, user_name: str = None):
        """Send password reset verification code email"""
        await send_password_reset_email(
            email=email,
            verification_code=verification_code,
            first_name=user_name or "User",
            expires_minutes=10
        )

    @staticmethod
    async def send_welcome(email: str, user_name: str = None, dashboard_url: str = "https://example.com/dashboard"):
        """Send welcome email"""
        await send_welcome_email(
            email=email,
            first_name=user_name or "User",
            dashboard_url=dashboard_url
        )


client_email_service = ClientEmailService()

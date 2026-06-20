"""
SMTP邮件发送服务
支持使用自定义SMTP服务器发送邮件
"""
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, Any, List, Optional
from jinja2 import Template
from app.core.config import settings
from app.services.common.thread_pool import thread_pool_service


class EmailTemplateLoader:
    """邮件模板加载器"""

    TEMPLATE_DIR = Path(__file__).parent.parent.parent.parent / "resources" / "emails" / "auth"

    @classmethod
    def load_template(cls, template_name: str) -> Template:
        """加载邮件模板"""
        template_path = cls.TEMPLATE_DIR / f"{template_name}.html"

        if not template_path.exists():
            raise FileNotFoundError(f"邮件模板未找到: {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        return Template(template_content)

    @classmethod
    def render_template(cls, template_name: str, context: Dict[str, Any]) -> str:
        """渲染邮件模板"""
        template = cls.load_template(template_name)
        return template.render(**context)


def _send_email_sync(
    to_emails: List[str],
    subject: str,
    html_content: str,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None
) -> Dict[str, Any]:
    """同步发送邮件（在线程池中执行）"""
    sender_email = from_email or settings.MAIL_FROM_ADDRESS
    sender_name = from_name or settings.MAIL_FROM_NAME

    message = MIMEMultipart('alternative')
    message['Subject'] = subject
    message['From'] = f"{sender_name} <{sender_email}>"
    message['To'] = ', '.join(to_emails)

    html_part = MIMEText(html_content, 'html', 'utf-8')
    message.attach(html_part)

    try:
        if settings.MAIL_ENCRYPTION.lower() == 'ssl':
            server = smtplib.SMTP_SSL(settings.MAIL_HOST, settings.MAIL_PORT)
        else:
            server = smtplib.SMTP(settings.MAIL_HOST, settings.MAIL_PORT)
            if settings.MAIL_ENCRYPTION.lower() in ['tls', 'starttls']:
                server.starttls()

        server.set_debuglevel(1)

        if settings.MAIL_USERNAME and settings.MAIL_PASSWORD:
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)

        result = server.send_message(message)
        server.quit()

        return {
            "success": True,
            "message": "邮件发送成功",
            "to": to_emails
        }

    except smtplib.SMTPAuthenticationError as e:
        raise Exception(f"SMTP 认证失败: {str(e)}")

    except smtplib.SMTPException as e:
        raise Exception(f"SMTP 错误: {str(e)}")

    except Exception as e:
        raise Exception(f"邮件发送失败: {str(e)}")


async def send_email(
    to_emails: List[str],
    subject: str,
    html_content: str,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None
) -> Dict[str, Any]:
    """异步发送邮件"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        thread_pool_service.get_executor(),
        _send_email_sync,
        to_emails,
        subject,
        html_content,
        from_email,
        from_name
    )


async def send_template_email(
    to_emails: List[str],
    template_name: str,
    context: Dict[str, Any],
    subject: str,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None
) -> Dict[str, Any]:
    """使用模板发送邮件"""
    html_content = EmailTemplateLoader.render_template(template_name, context)

    return await send_email(
        to_emails=to_emails,
        subject=subject,
        html_content=html_content,
        from_email=from_email,
        from_name=from_name
    )


async def send_verification_email(
    email: str,
    verification_code: str,
    first_name: str = "User",
    expires_minutes: int = 10
) -> Dict[str, Any]:
    """发送注册验证码邮件"""
    return await send_template_email(
        to_emails=[email],
        template_name="registration_verification",
        context={
            "first_name": first_name,
            "verification_code": verification_code,
            "expires_minutes": expires_minutes
        },
        subject=f"Verify Your Email - {settings.PROJECT_NAME}"
    )


async def send_password_reset_email(
    email: str,
    verification_code: str,
    first_name: str = "User",
    expires_minutes: int = 10
) -> Dict[str, Any]:
    """发送密码重置验证码邮件"""
    return await send_template_email(
        to_emails=[email],
        template_name="password_reset",
        context={
            "first_name": first_name,
            "verification_code": verification_code,
            "expires_minutes": expires_minutes
        },
        subject=f"Password Reset Code - {settings.PROJECT_NAME}"
    )


async def send_welcome_email(
    email: str,
    first_name: str = "User",
    dashboard_url: str = "https://example.com/dashboard"
) -> Dict[str, Any]:
    """发送欢迎邮件"""
    return await send_template_email(
        to_emails=[email],
        template_name="welcome",
        context={
            "first_name": first_name,
            "dashboard_url": dashboard_url
        },
        subject=f"Welcome to {settings.PROJECT_NAME}!"
    )

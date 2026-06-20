"""
初始化默认 LLM 配置（从 .env 读取 DeepSeek 配置）
运行方式: cd ai-interview-backend && python -m app.scripts.seed_llm_config
"""
import asyncio
from sqlalchemy import select
from app.db.session import async_session
from app.core.config import settings
from app.models.llm_provider import LLMProvider, LLMModel


async def seed():
    async with async_session() as db:
        # 检查是否已有提供商
        result = await db.execute(select(LLMProvider))
        if result.scalars().first():
            print("LLM 提供商已存在，跳过创建。")
            return

        # 从 .env 读取 DeepSeek 配置创建默认提供商
        provider = LLMProvider(
            name="DeepSeek",
            base_url=settings.DEEPSEEK_BASE_URL,
            api_key=settings.DEEPSEEK_API_KEY,
            is_enabled=True
        )
        db.add(provider)
        await db.flush()

        # 创建默认模型并激活
        model = LLMModel(
            provider_id=provider.id,
            model_name=settings.DEEPSEEK_MODEL,
            display_name=settings.DEEPSEEK_MODEL,
            is_active=True
        )
        db.add(model)
        await db.commit()

        print(f"默认 LLM 配置已创建:")
        print(f"  提供商: DeepSeek ({settings.DEEPSEEK_BASE_URL})")
        print(f"  模型: {settings.DEEPSEEK_MODEL} (已激活)")


if __name__ == "__main__":
    asyncio.run(seed())

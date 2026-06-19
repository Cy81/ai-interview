import json
import time
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

# ---- 动态配置缓存 ----
_cached_client: Optional[AsyncOpenAI] = None
_cached_model: Optional[str] = None
_cache_loaded_at: float = 0
_CACHE_TTL = 60  # 秒
_cache_lock = asyncio.Lock()


class AIService:
    """AI 服务 - 支持动态配置加载 LLM 提供商和模型"""

    @staticmethod
    async def _get_client() -> Tuple[AsyncOpenAI, str]:
        """
        获取当前激活的 LLM 客户端和模型名称。
        带 60 秒 TTL 缓存，首次调用从数据库加载，
        如果没有激活配置则回退到 .env 中的 DeepSeek 配置。
        """
        global _cached_client, _cached_model, _cache_loaded_at

        now = time.monotonic()
        if _cached_client is not None and (now - _cache_loaded_at) < _CACHE_TTL:
            return _cached_client, _cached_model

        async with _cache_lock:
            # 双重检查
            now = time.monotonic()
            if _cached_client is not None and (now - _cache_loaded_at) < _CACHE_TTL:
                return _cached_client, _cached_model

            # 尝试从数据库加载
            try:
                from sqlalchemy import select
                from app.models.llm_provider import LLMProvider, LLMModel
                from app.db.session import async_session

                async with async_session() as db:
                    result = await db.execute(
                        select(LLMModel)
                        .join(LLMProvider)
                        .where(LLMModel.is_active == True, LLMProvider.is_enabled == True)
                    )
                    model = result.scalar_one_or_none()

                    if model is not None:
                        provider = await db.get(LLMProvider, model.provider_id)
                        _cached_client = AsyncOpenAI(
                            api_key=provider.api_key,
                            base_url=provider.base_url
                        )
                        _cached_model = model.model_name
                        logger.info(
                            f"AI 配置已从数据库加载: provider={provider.name}, "
                            f"model={model.model_name}"
                        )
                    else:
                        # 没有激活配置，回退到 .env
                        _cached_client = AsyncOpenAI(
                            api_key=settings.DEEPSEEK_API_KEY,
                            base_url=settings.DEEPSEEK_BASE_URL
                        )
                        _cached_model = settings.DEEPSEEK_MODEL
                        logger.warning("数据库中没有激活的 LLM 配置，使用 .env 默认配置")

            except Exception as e:
                logger.error(f"从数据库加载 LLM 配置失败: {e}，回退到 .env 默认配置")
                _cached_client = AsyncOpenAI(
                    api_key=settings.DEEPSEEK_API_KEY,
                    base_url=settings.DEEPSEEK_BASE_URL
                )
                _cached_model = settings.DEEPSEEK_MODEL

            _cache_loaded_at = time.monotonic()
            return _cached_client, _cached_model

    @staticmethod
    async def invalidate_config_cache():
        """清除配置缓存，下次调用时重新从数据库加载"""
        global _cached_client, _cached_model, _cache_loaded_at
        _cached_client = None
        _cached_model = None
        _cache_loaded_at = 0
        logger.info("AI 配置缓存已清除")

    @staticmethod
    async def _chat(messages: list, temperature: float = 0.7) -> str:
        """基础对话补全调用"""
        try:
            client, model_name = await AIService._get_client()
            response = await client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=2000
            )
            if not response.choices:
                logger.warning(f"LLM API 返回空 choices, model={model_name}")
                return ""
            content = response.choices[0].message.content
            return content.strip() if content else ""
        except Exception as e:
            logger.error(f"LLM API 调用失败: {e}")
            raise

    @staticmethod
    async def _chat_stream(messages: list, temperature: float = 0.7):
        """流式对话补全调用，逐块返回文本"""
        try:
            client, model_name = await AIService._get_client()
            stream = await client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=2000,
                stream=True
            )
            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content
        except Exception as e:
            logger.error(f"LLM 流式 API 调用失败: {e}")
            raise

    @staticmethod
    def _extract_json(text: str) -> dict:
        """从 AI 响应中提取 JSON，处理 markdown 代码块包裹的情况"""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        return json.loads(text)

    @staticmethod
    async def parse_resume(resume_text: str) -> dict:
        """解析简历文本，提取结构化信息"""
        messages = [
            {"role": "system", "content": (
                "你是一个专业的简历分析师。请解析简历内容，提取结构化信息。"
                "必须返回纯JSON格式（不要markdown代码块），包含以下字段：\n"
                '{"name": "姓名", "education": "学历信息", '
                '"skills": ["技能列表"], "experience": ["工作/实习经历"], '
                '"projects": ["项目经历"], "summary": "一句话总结候选人背景"}'
            )},
            {"role": "user", "content": f"请解析以下简历内容：\n\n{resume_text}"}
        ]
        result = await AIService._chat(messages, temperature=0.3)
        return AIService._extract_json(result)

    @staticmethod
    async def analyze_resume(parsed_resume: dict, target_position: str) -> dict:
        """分析简历质量，给出评分、优劣势和改进建议"""
        is_intern = any(kw in target_position.lower() for kw in ["实习", "intern"])
        if is_intern:
            level_hint = (
                "【重要】目标岗位是实习岗位，候选人是在校学生，请严格按实习生标准评价。\n"
                "禁止事项：\n"
                "- 禁止在weaknesses中提及'缺少实习经验'、'缺少工作经验'、'没有实际工作经验'等类似表述\n"
                "- 禁止因为项目是个人项目或校内项目而扣分，这对实习生来说是正常的\n"
                "- 禁止要求候选人具备线上生产环境经验\n"
                "评价重点：技术基础扎实度、项目完成度和技术深度、学习能力、编码能力。\n"
                "个人项目和校内项目同样能体现技术能力，请公正评价项目质量本身。\n"
            )
        else:
            level_hint = (
                "目标岗位是正式岗位，请按社招标准评价。\n"
                "重点关注：工作经验、项目深度、技术广度、解决复杂问题的能力。\n"
            )
        messages = [
            {"role": "system", "content": (
                f"你是一个资深HR和职业规划师，请针对{target_position}岗位分析这份简历。\n"
                f"{level_hint}"
                "必须返回纯JSON格式（不要markdown代码块），包含以下字段：\n"
                '{"overall_score": 7.5, '
                '"strengths": ["优势1", "优势2", "优势3"], '
                '"weaknesses": ["不足1", "不足2", "不足3"], '
                '"suggestions": ["具体改进建议1", "具体改进建议2", "具体改进建议3"], '
                '"keyword_match": ["匹配的关键技能1", "匹配的关键技能2"], '
                '"missing_keywords": ["缺少的关键技能1", "缺少的关键技能2"], '
                '"summary": "一段话总结简历质量和改进方向，100字以内"}'
                "\n评分标准：9-10优秀，7-8良好，5-6一般，3-4较差，1-2很差"
            )},
            {"role": "user", "content": (
                f"目标岗位：{target_position}\n"
                f"简历内容：{json.dumps(parsed_resume, ensure_ascii=False)}"
            )}
        ]
        result = await AIService._chat(messages, temperature=0.4)
        return AIService._extract_json(result)

    @staticmethod
    async def generate_questions(parsed_resume: dict, target_position: str, difficulty: str, count: int) -> list:
        """根据简历和目标岗位生成面试题目"""
        difficulty_map = {
            "easy": "初级，侧重基础知识和简单项目经验",
            "medium": "中级，涵盖技术深度和项目设计思路",
            "hard": "高级，深入系统设计、性能优化和技术原理"
        }
        difficulty_desc = difficulty_map.get(difficulty, difficulty_map["medium"])
        is_intern = any(kw in target_position for kw in ["实习", "intern", "Intern"])
        if is_intern:
            position_hint = (
                "\n注意：这是实习岗位面试，候选人可能是在校学生，请适当降低难度：\n"
                "- 侧重基础知识（语言基础、数据结构、常用框架）\n"
                "- 项目经验题以学习过程和思路为主，不要求生产级方案\n"
                "- 不要出过于深入的系统设计和高并发优化题\n"
                "- 可以考察学习能力和成长潜力\n"
            )
        else:
            position_hint = (
                "\n注意：这是正式岗位面试，请按正常标准出题：\n"
                "- 要求候选人有扎实的技术基础和实际项目经验\n"
                "- 可以涉及系统设计、性能优化、线上问题排查等\n"
                "- 考察解决实际问题的能力和技术深度\n"
            )
        messages = [
            {"role": "system", "content": (
                f"你是一个资深技术面试官，正在面试{target_position}岗位。\n"
                f"面试难度：{difficulty_desc}\n{position_hint}\n"
                "请根据候选人背景生成面试题。要求：\n"
                "1. 结合候选人的项目经验和技术栈提问\n"
                "2. 第一题是自我介绍\n"
                "3. 覆盖技术深度、项目经验、基础知识\n"
                "4. 返回纯JSON数组格式（不要markdown代码块）\n"
                '格式：[{"index": 0, "question": "题目内容", "category": "分类"}]\n'
                "分类包括：self-intro, project, technical, coding, system-design"
            )},
            {"role": "user", "content": (
                f"候选人简历信息：{json.dumps(parsed_resume, ensure_ascii=False)}\n"
                f"目标岗位：{target_position}\n请生成{count}道面试题。"
            )}
        ]
        result = await AIService._chat(messages, temperature=0.7)
        return AIService._extract_json(result)

    @staticmethod
    async def evaluate_answer(question, answer, resume_context, chat_history, next_question=None) -> dict:
        """评估候选人的回答，返回评分和反馈"""
        history_text = ""
        for msg in chat_history[-6:]:
            role = "面试官" if msg["role"] == "interviewer" else "候选人"
            history_text += f"{role}: {msg['content']}\n"
        messages = [
            {"role": "system", "content": (
                "你是一个资深技术面试官，正在评估候选人的回答。\n"
                "请返回纯JSON格式（不要markdown代码块）：\n"
                '{"score": 7.5, "feedback": "简短反馈50字以内", "follow_up": false}\n'
                "评分标准：\n"
                "- 9-10: 回答非常出色，有深度有见解\n"
                "- 7-8: 回答良好，基本正确\n"
                "- 5-6: 回答一般，有明显不足\n"
                "- 3-4: 回答较差，理解有误\n"
                "- 1-2: 基本没有回答到点上"
            )},
            {"role": "user", "content": (
                f"候选人背景：{json.dumps(resume_context, ensure_ascii=False)}\n"
                f"对话历史：\n{history_text}\n"
                f"当前问题：{question}\n候选人回答：{answer}\n请评估这个回答。"
            )}
        ]
        result = await AIService._chat(messages, temperature=0.5)
        return AIService._extract_json(result)

    @staticmethod
    async def evaluate_answer_stream(question, answer, resume_context, chat_history):
        """流式版本：评估回答并逐块输出评语，最后输出 JSON 评分"""
        history_text = ""
        for msg in chat_history[-6:]:
            role = "面试官" if msg["role"] == "interviewer" else "候选人"
            history_text += f"{role}: {msg['content']}\n"
        messages = [
            {"role": "system", "content": (
                "你是一个资深技术面试官，正在评估候选人的回答。\n"
                "请先用自然语言给出详细点评（100字左右），然后换行输出评分JSON。\n"
                "格式要求：\n先输出点评文字，然后另起一行输出：\n"
                '```json\n{"score": 7.5}\n```'
            )},
            {"role": "user", "content": (
                f"候选人背景：{json.dumps(resume_context, ensure_ascii=False)}\n"
                f"对话历史：\n{history_text}\n"
                f"当前问题：{question}\n候选人回答：{answer}\n请评估这个回答。"
            )}
        ]
        async for chunk in AIService._chat_stream(messages, temperature=0.5):
            yield chunk

    @staticmethod
    async def generate_report(parsed_resume, target_position, questions_and_scores) -> dict:
        """根据面试记录生成综合评估报告"""
        qa_text = ""
        for item in questions_and_scores:
            qa_text += (
                f"问题：{item['question']}\n"
                f"回答：{item.get('answer', '未回答')}\n"
                f"得分：{item.get('score', 'N/A')}\n\n"
            )
        messages = [
            {"role": "system", "content": (
                "你是一个资深技术面试官，请根据面试记录生成综合评估报告。\n"
                "返回纯JSON格式（不要markdown代码块）：\n"
                '{"summary": "总体评价100字以内", '
                '"strengths": ["优势1", "优势2"], '
                '"weaknesses": ["不足1", "不足2"], '
                '"suggestions": ["建议1", "建议2"], '
                '"hire_recommendation": "建议录用/待定/不建议录用"}'
            )},
            {"role": "user", "content": (
                f"候选人背景：{json.dumps(parsed_resume, ensure_ascii=False)}\n"
                f"目标岗位：{target_position}\n面试记录：\n{qa_text}\n请生成综合评估报告。"
            )}
        ]
        result = await AIService._chat(messages, temperature=0.5)
        return AIService._extract_json(result)

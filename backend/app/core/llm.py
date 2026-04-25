"""
LLM 调用封装 - 支持 OpenAI 兼容接口
"""
import json
from typing import Generator, AsyncGenerator, Optional
import logging
from openai import AsyncOpenAI

from ..core.config import Config

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM 客户端"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.client = AsyncOpenAI(
            api_key=api_key or Config.OPENAI_API_KEY,
            base_url=base_url or Config.OPENAI_BASE_URL,
        )
        self.default_model = model or Config.OPENAI_MODEL
    
    async def chat(
        self,
        messages: list,
        model: str = None,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> str:
        """同步聊天"""
        model = model or self.default_model
        
        try:
            if stream:
                return await self._stream_chat(messages, model, temperature)
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                stream=False,
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            raise
    
    async def _stream_chat(
        self,
        messages: list,
        model: str,
        temperature: float,
    ) -> str:
        """流式聊天"""
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=True,
        )
        
        full_content = ""
        async for chunk in response:
            if chunk.choices[0].delta.content:
                full_content += chunk.choices[0].delta.content
                yield chunk.choices[0].delta.content
        
        # 注意：async generator 不能有 return 语句
    
    async def chat_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = None,
        temperature: float = 0.7,
    ) -> str:
        """带系统提示的聊天"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return await self.chat(messages, model, temperature)


# 全局客户端实例
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """获取 LLM 客户端单例"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client

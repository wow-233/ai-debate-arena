"""
LLM 技能 - OpenAI 兼容接口
"""
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from openai import AsyncOpenAI

from .base import SkillBase, SkillConfig, RunnableSkill, SkillResult

logger = logging.getLogger(__name__)


class LLMSkill(RunnableSkill):
    """LLM 调用技能"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-chat",
        config: Optional[SkillConfig] = None
    ):
        super().__init__(config)
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._client: Optional[AsyncOpenAI] = None
    
    async def _on_initialize(self) -> None:
        """初始化 LLM 客户端"""
        self._client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )
        logger.info(f"LLMSkill initialized with model: {self.model}")
    
    async def run(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> str:
        """调用 LLM"""
        if not self._client:
            await self.initialize()
        
        model = model or self.model
        
        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            **kwargs
        )
        
        if stream:
            return self._stream_response(response)
        
        return response.choices[0].message.content
    
    async def _stream_response(self, response) -> AsyncGenerator[str, None]:
        """流式响应"""
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """简单对话"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return await self.run(messages, **kwargs)
    
    async def complete(
        self,
        prompt: str,
        **kwargs
    ) -> str:
        """补全提示"""
        return await self.chat(prompt, **kwargs)
    
    async def cleanup(self) -> None:
        """清理"""
        if self._client:
            await self._client.close()
            self._client = None


class MultiModelLLM(RunnableSkill):
    """多模型 LLM"""
    
    MODELS = {
        "fast": "gpt-4o-mini",
        "balanced": "gpt-4o",
        "deep": "gpt-4",
        "reasoning": "deepseek-reasoner",
    }
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com",
        default_tier: str = "balanced",
        config: Optional[SkillConfig] = None
    ):
        super().__init__(config)
        self.api_key = api_key
        self.base_url = base_url
        self.default_tier = default_tier
        self._skills: Dict[str, LLMSkill] = {}
    
    def get_model(self, tier: str) -> str:
        """获取模型"""
        return self.MODELS.get(tier, self.MODELS[self.default_tier])
    
    async def initialize(self) -> None:
        """初始化所有模型"""
        for tier, model in self.MODELS.items():
            skill = LLMSkill(
                api_key=self.api_key,
                base_url=self.base_url,
                model=model,
            )
            await skill.initialize()
            self._skills[tier] = skill
    
    async def run(
        self,
        prompt: str,
        tier: Optional[str] = None,
        **kwargs
    ) -> str:
        """运行指定层级"""
        tier = tier or self.default_tier
        skill = self._skills.get(tier)
        if not skill:
            raise ValueError(f"Unknown tier: {tier}")
        return await skill.chat(prompt, **kwargs)
    
    async def cleanup(self) -> None:
        """清理所有"""
        for skill in self._skills.values():
            await skill.cleanup()
        self._skills.clear()


# 别名
LLMRunner = LLMSkill
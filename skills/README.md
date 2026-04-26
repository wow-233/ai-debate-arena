# Skills Module

可复用的 AI 技能模块。

## 结构

```
skills/
├── __init__.py      # 模块入口
├── base.py         # 基础类 (SkillBase, RunnableSkill)
├── llm.py         # LLM 调用 (LLMSkill)
├── debate.py       # 辩论 (DebateSkill)
└── obsidian.py    # Obsidian (ObsidianSkill)
```

## 使用示例

```python
import asyncio
from skills import LLMSkill, DebateSkill, ObsidianSkill

async def main():
    # 1. LLM 技能
    llm = LLMSkill(
        api_key="sk-xxx",
        base_url="https://api.deepseek.com",
        model="deepseek-chat"
    )
    await llm.initialize()
    
    result = await llm.chat("你好")
    print(result)
    
    # 2. 辩论技能
    debate = DebateSkill(llm)
    state = await debate.run("电商商业模式可行性")
    print(state.final_summary)
    
    # 3. Obsidian 技能
    obsidian = ObsidianSkill(vault_path="D:\\Obsidian\\Vault")
    notes = await obsidian.run("list")
    for note in notes:
        print(note.title)

asyncio.run(main())
```

## 开发新技能

参考 `base.py` 中的 `RunnableSkill` 基类：

```python
from skills.base import RunnableSkill, SkillConfig

class MySkill(RunnableSkill):
    async def run(self, input_data, **kwargs) -> Any:
        # 实现逻辑
        return result
```
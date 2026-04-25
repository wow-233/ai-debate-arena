import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def get_base_path():
    """获取基础路径（支持 PyInstaller 打包）"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后
        return Path(sys._MEIPASS)
    return Path(__file__).parent

def get_app_path():
    """获取应用运行路径"""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent

# 尝试加载 .env
base_path = get_app_path()
env_files = [
    base_path / ".env",
    Path.cwd() / ".env",
]
for env_file in env_files:
    if env_file.exists():
        load_dotenv(env_file)
        break

class Config:
    """配置管理"""
    
    # LLM 配置
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.deepseek.com')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'deepseek-chat')
    
    # 模型层级配置
    MODEL_FAST = os.getenv('MODEL_FAST', 'gpt-4o-mini')
    MODEL_BALANCED = os.getenv('MODEL_BALANCED', 'gpt-4o')
    MODEL_DEEP = os.getenv('MODEL_DEEP', 'gpt-4')
    
    # Obsidian 配置
    OBSIDIAN_VAULT_PATH = os.getenv('OBSIDIAN_VAULT_PATH', '')
    
    # 服务器配置
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '8000'))
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    @classmethod
    def get_obsidian_path(cls) -> Path:
        """获取 Obsidian 路径"""
        if not cls.OBSIDIAN_VAULT_PATH:
            raise ValueError("OBSIDIAN_VAULT_PATH 未配置")
        path = Path(cls.OBSIDIAN_VAULT_PATH)
        if not path.exists():
            raise ValueError(f"Obsidian Vault 路径不存在: {path}")
        return path
    
    @classmethod
    def validate(cls):
        """验证配置"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 未配置")
        return True

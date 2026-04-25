"""
AI Debate Arena - Launcher entry
"""
import os
import sys
import logging
import io
from pathlib import Path

# 修复 Windows 控制台编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 添加项目路径
if getattr(sys, 'frozen', False):
    # PyInstaller 打包后，exe 同目录
    app_path = Path(sys.executable).parent
else:
    # 源码运行
    app_path = Path(__file__).parent

sys.path.insert(0, str(app_path))

from app.core.config import Config
import uvicorn


def main():
    """主入口"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    print("=" * 50)
    print("AI Debate Arena - Multi-Agent AI Debate System")
    print("=" * 50)
    
    # 检查配置
    if not Config.OPENAI_API_KEY:
        print("\n[WARNING] OPENAI_API_KEY not configured")
        print("Please create .env file or set environment variable")
        print("See .env.example for reference\n")
    
    if not Config.OBSIDIAN_VAULT_PATH:
        print("[WARNING] OBSIDIAN_VAULT_PATH not configured")
        print("Obsidian integration will be disabled\n")
    
    print(f"API docs: http://localhost:{Config.PORT}/docs")
    print(f"Health check: http://localhost:{Config.PORT}/health")
    print("-" * 50)
    print("Press Ctrl+C to stop")
    print("=" * 50 + "\n")
    
    # 检查必需配置
    if not Config.OPENAI_API_KEY:
        print("[ERROR] OPENAI_API_KEY is required. Exiting.")
        sys.exit(1)
    
    # 启动服务
    import app.main
    uvicorn.run(
        app.main.app,  # 直接传入 app 对象
        host=Config.HOST,
        port=Config.PORT,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
"""
AI Debate Arena - 打包入口
"""
import os
import sys
import logging

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import Config
import uvicorn


def main():
    """主入口"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    print("=" * 50)
    print("AI Debate Arena - 多智能体 AI 辩论系统")
    print("=" * 50)
    
    # 检查配置
    if not Config.OPENAI_API_KEY:
        print("\n⚠️  警告: OPENAI_API_KEY 未配置")
        print("请创建 .env 文件或设置环境变量")
        print("示例配置见 .env.example\n")
    
    if not Config.OBSIDIAN_VAULT_PATH:
        print("⚠️  警告: OBSIDIAN_VAULT_PATH 未配置")
        print("Obsidian 集成功能将不可用\n")
    
    print(f"API 文档: http://localhost:{Config.PORT}/docs")
    print(f"健康检查: http://localhost:{Config.PORT}/health")
    print("-" * 50)
    print("按 Ctrl+C 停止服务")
    print("=" * 50 + "\n")
    
    # 启动服务
    uvicorn.run(
        "app.main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=False,  # 打包后禁用 reload
        log_level="info",
    )


if __name__ == "__main__":
    main()
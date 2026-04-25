"""
FastAPI 入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .core.config import Config
from .api.debate import router as debate_router, obsidian_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title="AI Debate Arena",
        description="多智能体 AI 辩论系统 - 支持三方专业角色进行结构化辩论",
        version="1.0.0",
    )
    
    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应限制
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    app.include_router(debate_router)
    app.include_router(obsidian_router)
    
    @app.get("/")
    async def root():
        return {
            "name": "AI Debate Arena",
            "version": "1.0.0",
            "description": "多智能体 AI 辩论系统",
        }
    
    @app.get("/health")
    async def health():
        return {"status": "ok"}
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    try:
        Config.validate()
        uvicorn.run(
            "app.main:app",
            host=Config.HOST,
            port=Config.PORT,
            reload=True,
        )
    except ValueError as e:
        logger.error(f"配置验证失败: {e}")
        print(f"错误: {e}")
        print("请确保 .env 文件配置正确")
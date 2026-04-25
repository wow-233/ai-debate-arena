# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 项目根目录
PROJECT_ROOT = r"D:\vscodeing\ai-debate-arena\backend"

a = Analysis(
    ['run.py'],  # 入口文件
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=[
        ('.env.example', '.'),  # 包含示例配置
    ],
    hiddenimports=[
        'pydantic',
        'openai',
        'frontmatter',
        'sse_starlette',
        'uvicorn',
        'dotenv',
        'app',
        'app.core',
        'app.core.config',
        'app.core.llm',
        'app.core.router',
        'app.models',
        'app.models.debate',
        'app.models.agent',
        'app.services',
        'app.services.debate_engine',
        'app.services.obsidian_writer',
        'app.services.obsidian_reader',
        'app.api',
        'app.api.debate',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,  # 恢复正常打包
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AI-Debate-Arena',
    debug=False,  # 恢复正常
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AI-Debate-Arena',
    strip=False,
    upx=True,
    upx_exclude=[],
    recursive=True,
)
"""
配置文件

包含 API 配置和默认参数

设置 API key 的方法：
1. 方法 1：创建 .env 文件，写入 DASHSCOPE_API_KEY=你的 key
2. 方法 2：在终端设置环境变量
   - Windows CMD: set DASHSCOPE_API_KEY=你的 key
   - PowerShell: $env:DASHSCOPE_API_KEY="你的 key"
   - Linux/Mac: export DASHSCOPE_API_KEY=你的 key
3. 方法 3：在系统环境变量中永久设置
"""

import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# API 配置
API_URL = "https://dashscope.aliyuncs.com/apps/anthropic/v1/messages"
API_KEY: str = os.environ.get("DASHSCOPE_API_KEY") or ""
DEFAULT_MODEL = "qwen3.5-plus"

# 验证配置
DEFAULT_TOLERANCE = 1e-6

# 文件转换配置
PDF_DPI = 1  # PDF 转图片的缩放倍数，2 表示 2 倍清晰度

# 重试配置
DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT = 600  # 增加超时时间到 600 秒，以处理多张图片
DEFAULT_MAX_TOKENS = 2048


def check_api_key():
    """检查 API key 是否已设置"""
    if not API_KEY:
        raise ValueError("未设置环境变量 DASHSCOPE_API_KEY，请设置后再运行")
    return API_KEY
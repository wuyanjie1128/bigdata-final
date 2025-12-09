import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------
# DashScope (Qwen) 配置
# ---------------------------
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = os.getenv(
    "DASHSCOPE_BASE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1",
)
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen3-vl-plus")

# ---------------------------
# 可选 OSS 配置（当前版本不强制使用）
# 如果你未来要恢复 OSS 上传功能，可以再加依赖与代码
# ---------------------------
OSS_ACCESS_KEY_ID = os.getenv("OSS_ACCESS_KEY_ID", "")
OSS_ACCESS_KEY_SECRET = os.getenv("OSS_ACCESS_KEY_SECRET", "")
OSS_REGION = os.getenv("OSS_REGION", "cn-shanghai")
OSS_ENDPOINT = os.getenv("OSS_ENDPOINT", "")
OSS_BUCKET = os.getenv("OSS_BUCKET", "")

# ---------------------------
# Flask 上传配置
# ---------------------------
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "temp_uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

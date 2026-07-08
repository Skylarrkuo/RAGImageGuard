"""通用工具函数：图片格式检测、MIME 映射、尺寸计算、图片缩放"""

import io
from PIL import Image


def get_image_dimensions(image_bytes: bytes) -> tuple[int, int]:
    """从图片字节流中获取宽高"""
    img = Image.open(io.BytesIO(image_bytes))
    return img.size  # (width, height)


def resize_for_api(image_bytes: bytes, max_dim: int = 2048) -> bytes:
    """缩放大图至 API 可接受尺寸，长边不超过 max_dim 像素。
    小图不处理直接返回原字节。返回 JPEG 字节以减少传输体积。"""
    img = Image.open(io.BytesIO(image_bytes))
    w, h = img.size
    if max(w, h) <= max_dim:
        return image_bytes
    img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)
    return buf.getvalue()


def create_thumbnail(image_bytes: bytes, max_size: int = 400) -> bytes:
    """生成缩略图，保持比例，长边不超过 max_size 像素，返回 JPEG 字节"""
    img = Image.open(io.BytesIO(image_bytes))
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=75, optimize=True)
    return buf.getvalue()


def pick_gpt_image_size(width: int, height: int) -> str:
    """根据图片宽高比选择 GPT-image-2 支持的最接近尺寸

    GPT-image-2 支持的尺寸:
      - 1024x1024  (1:1)
      - 1536x1024  (3:2 横屏)
      - 1024x1536  (2:3 竖屏)
      - auto       (自动)
    """
    ratio = width / height

    if ratio < 0.8:          # 竖屏: 比例 < 4:5
        return "1024x1536"
    elif ratio > 1.25:       # 横屏: 比例 > 5:4
        return "1536x1024"
    else:                    # 接近正方形
        return "1024x1024"


def detect_image_format(filename: str, content_type: str = "") -> str:
    """从文件名或 content_type 检测图片格式"""
    if filename and "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext in ("jpg", "jpeg", "png", "webp", "gif"):
            return ext
    if "jpeg" in content_type or "jpg" in content_type:
        return "jpg"
    if "png" in content_type:
        return "png"
    if "webp" in content_type:
        return "webp"
    return "png"


def get_mime(format: str) -> str:
    """根据图片格式返回 MIME 类型"""
    mapping = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif",
    }
    return mapping.get(format, "image/png")

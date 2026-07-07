"""通用工具函数：图片格式检测、MIME 映射"""


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

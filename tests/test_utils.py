"""core/utils.py 工具函数测试"""

import io
import pytest
from PIL import Image

from core.utils import (
    get_image_dimensions,
    create_thumbnail,
    resize_for_api,
    detect_image_format,
    get_mime,
    pick_gpt_image_size,
)


class TestGetImageDimensions:
    def test_returns_width_height(self, sample_image_bytes):
        w, h = get_image_dimensions(sample_image_bytes)
        assert w == 100
        assert h == 100

    def test_large_image(self, large_image_bytes):
        w, h = get_image_dimensions(large_image_bytes)
        assert w == 4000
        assert h == 3000


class TestCreateThumbnail:
    def test_thumbnail_size(self, sample_image_bytes):
        thumb = create_thumbnail(sample_image_bytes, max_size=50)
        img = Image.open(io.BytesIO(thumb))
        assert max(img.size) <= 50
        assert img.format == "JPEG"

    def test_rgba_converted(self, sample_rgba_image_bytes):
        thumb = create_thumbnail(sample_rgba_image_bytes)
        img = Image.open(io.BytesIO(thumb))
        assert img.mode == "RGB"

    def test_small_image_unchanged_size(self, sample_image_bytes):
        """小图缩略图不应放大"""
        thumb = create_thumbnail(sample_image_bytes, max_size=200)
        img = Image.open(io.BytesIO(thumb))
        assert max(img.size) <= 200


class TestResizeForApi:
    def test_small_image_no_resize(self, sample_image_bytes):
        """小图不缩放，返回原字节"""
        result = resize_for_api(sample_image_bytes, max_dim=2048)
        assert result == sample_image_bytes

    def test_large_image_resized(self, large_image_bytes):
        """大图缩放到 max_dim"""
        result = resize_for_api(large_image_bytes, max_dim=2048)
        img = Image.open(io.BytesIO(result))
        assert max(img.size) <= 2048

    def test_output_is_jpeg(self, large_image_bytes):
        """缩放后输出 JPEG 格式"""
        result = resize_for_api(large_image_bytes, max_dim=1024)
        img = Image.open(io.BytesIO(result))
        assert img.format == "JPEG"

    def test_rgba_to_rgb(self, sample_rgba_image_bytes):
        """RGBA 图片转为 RGB"""
        result = resize_for_api(sample_rgba_image_bytes, max_dim=50)
        img = Image.open(io.BytesIO(result))
        assert img.mode == "RGB"

    def test_custom_max_dim(self, large_image_bytes):
        result = resize_for_api(large_image_bytes, max_dim=800)
        img = Image.open(io.BytesIO(result))
        assert max(img.size) <= 800


class TestDetectImageFormat:
    def test_jpg_extension(self):
        assert detect_image_format("photo.jpg") == "jpg"

    def test_jpeg_extension(self):
        assert detect_image_format("photo.jpeg") == "jpeg"

    def test_png_extension(self):
        assert detect_image_format("photo.png") == "png"

    def test_webp_extension(self):
        assert detect_image_format("photo.webp") == "webp"

    def test_content_type_fallback(self):
        assert detect_image_format("", "image/jpeg") == "jpg"
        assert detect_image_format("", "image/png") == "png"

    def test_default_to_png(self):
        assert detect_image_format("photo.bmp") == "png"


class TestGetMime:
    def test_jpg(self):
        assert get_mime("jpg") == "image/jpeg"

    def test_png(self):
        assert get_mime("png") == "image/png"

    def test_webp(self):
        assert get_mime("webp") == "image/webp"

    def test_unknown_defaults_to_png(self):
        assert get_mime("bmp") == "image/png"


class TestPickGptImageSize:
    def test_portrait(self):
        assert pick_gpt_image_size(1000, 2000) == "1024x1536"

    def test_landscape(self):
        assert pick_gpt_image_size(2000, 1000) == "1536x1024"

    def test_square(self):
        assert pick_gpt_image_size(1000, 1000) == "1024x1024"

    def test_near_square(self):
        assert pick_gpt_image_size(1000, 1100) == "1024x1024"

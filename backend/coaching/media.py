import base64
import io
import math
import re
import subprocess
import warnings

import imageio_ffmpeg
from PIL import Image, ImageOps, UnidentifiedImageError

from .provider import ProviderError

MAX_SIZE = 100 * 1024 * 1024
MAX_PIXELS = 20_000_000


def clean_image(data):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as source:
                if (
                    source.format not in {"JPEG", "PNG", "WEBP"}
                    or source.width * source.height > MAX_PIXELS
                ):
                    raise ValueError("图片格式或尺寸不受支持。")
                source.load()
                img = ImageOps.exif_transpose(source).convert("RGB")
                img.thumbnail((1600, 1600))
                target = io.BytesIO()
                img.save(target, format="JPEG", quality=85)
                return target.getvalue()
    except (
        OSError,
        ValueError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise ProviderError("图片无效；仅支持不超过 2000 万像素的 JPEG、PNG、WebP。") from None


def video_duration(path):
    command = [
        imageio_ffmpeg.get_ffmpeg_exe(),
        "-nostdin",
        "-hide_banner",
        "-protocol_whitelist",
        "file,pipe",
        "-i",
        str(path),
    ]
    try:
        result = subprocess.run(command, capture_output=True, timeout=12, check=False)
        metadata = result.stderr.decode(errors="replace")
        match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", metadata)
        if not match or "Video:" not in metadata:
            raise ProviderError("视频无法读取。")
        duration = int(match[1]) * 3600 + int(match[2]) * 60 + float(match[3])
        if not math.isfinite(duration) or not 0 < duration <= 60:
            raise ProviderError("视频时长必须在 0–60 秒之间。")
        # Prevent unexpectedly huge decode surfaces.
        for width, height in re.findall(r"(?<!\d)(\d{2,5})x(\d{2,5})(?!\d)", metadata):
            if int(width) * int(height) > MAX_PIXELS:
                raise ProviderError("视频画面分辨率过大。")
        return duration
    except (OSError, subprocess.TimeoutExpired):
        raise ProviderError("视频读取超时或 FFmpeg 不可用。") from None


def extract_frames(path):
    duration = video_duration(path)
    count = min(8, max(1, math.ceil(duration / 8)))
    result = []
    for index in range(count):
        timestamp = round(duration * index / count, 2)
        try:
            process = subprocess.run(
                [
                    imageio_ffmpeg.get_ffmpeg_exe(),
                    "-nostdin",
                    "-v",
                    "error",
                    "-protocol_whitelist",
                    "file,pipe",
                    "-ss",
                    str(timestamp),
                    "-i",
                    str(path),
                    "-frames:v",
                    "1",
                    "-vf",
                    "scale=1024:1024:force_original_aspect_ratio=decrease",
                    "-f",
                    "image2pipe",
                    "-vcodec",
                    "mjpeg",
                    "-threads",
                    "1",
                    "pipe:1",
                ],
                capture_output=True,
                timeout=12,
                check=True,
            )
        except (OSError, subprocess.SubprocessError):
            raise ProviderError("视频抽帧失败，请尝试标准 MP4 文件。") from None
        result.append({"frame": index, "seconds": timestamp, "image": clean_image(process.stdout)})
    return result


def image_url(data):
    return "data:image/jpeg;base64," + base64.b64encode(data).decode("ascii")

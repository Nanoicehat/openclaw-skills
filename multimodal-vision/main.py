"""
多模态图片理解与生成工具

用法：
    uv run python main.py <command> [options]

命令：
    understand      理解/描述图片内容
    generate        根据文本描述生成图片

示例：
    uv run python main.py understand --image ./photo.jpg --prompt "描述这张图片"
    uv run python main.py understand --image-url https://example.com/img.jpg
    uv run python main.py generate --prompt "一只穿着宇航服的猫，卡通风格" --output ./cat.png
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from typing import Optional

import httpx

# ============ 配置 ============
BASE_URL = "https://api.vectorengine.ai/v1"
API_KEY = "sk-6bFxUxRh9Xc8TZFwj30JyRTIL0CWwjoJPDEKSnfuOCEJZrI6"
CHAT_ENDPOINT = f"{BASE_URL}/chat/completions"

VISION_MODEL = "gemini-3.1-flash-lite-preview"
GENERATION_MODEL = "gemini-3.1-flash-image-preview"

DEFAULT_TIMEOUT = 120.0


# ============ 工具函数 ============

def encode_image_to_base64(image_path: str) -> str:
    """将本地图片文件编码为 base64 data URL"""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"图片文件不存在: {image_path}")

    suffix = path.suffix.lower()
    mime_map = {".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png", ".webp": "webp", ".gif": "gif"}
    mime_type = mime_map.get(suffix, "jpeg")

    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    return f"data:image/{mime_type};base64,{encoded}"


def save_base64_image(data: str, output_path: str) -> None:
    """保存 base64 编码的图片到本地"""
    # 处理可能带 data URI scheme 的情况
    if "," in data:
        data = data.split(",", 1)[1]

    image_bytes = base64.b64decode(data)
    with open(output_path, "wb") as f:
        f.write(image_bytes)
    print(f"图片已保存至: {output_path}")


def get_auth_headers() -> dict:
    """获取认证请求头"""
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


# ============ API 客户端 ============

class VisionClient:
    """多模态视觉 API 客户端"""

    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        self.client = httpx.Client(timeout=timeout, headers=get_auth_headers())

    def understand_image(
        self,
        image_source: str,
        prompt: str = "请详细描述这张图片的内容",
        is_url: bool = False,
        max_tokens: int = 4096,
        temperature: float = 0.5,
    ) -> str:
        """
        理解图片内容

        Args:
            image_source: 图片路径或 URL
            prompt: 对图片的提问/指令
            is_url: 是否为网络 URL
            max_tokens: 最大输出 token 数
            temperature: 采样温度
        """
        if is_url:
            image_url = image_source
        else:
            image_url = encode_image_to_base64(image_source)

        payload = {
            "model": VISION_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        response = self.client.post(CHAT_ENDPOINT, json=payload)
        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"]

    def understand_multiple_images(
        self,
        image_sources: list[str],
        prompt: str = "请描述这些图片",
        are_urls: bool = False,
        max_tokens: int = 4096,
        temperature: float = 0.5,
    ) -> str:
        """
        同时理解多张图片

        Args:
            image_sources: 图片路径列表或 URL 列表
            prompt: 对图片的提问/指令
            are_urls: 是否为网络 URL
            max_tokens: 最大输出 token 数
            temperature: 采样温度
        """
        content: list[dict] = [{"type": "text", "text": prompt}]

        for src in image_sources:
            image_url = src if are_urls else encode_image_to_base64(src)
            content.append({"type": "image_url", "image_url": {"url": image_url}})

        payload = {
            "model": VISION_MODEL,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        response = self.client.post(CHAT_ENDPOINT, json=payload)
        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"]

    def generate_image(
        self,
        prompt: str,
        output_path: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.9,
    ) -> str:
        """
        根据文本提示生成图片

        Args:
            prompt: 图片描述文本
            output_path: 输出文件路径（如提供则保存图片）
            max_tokens: 最大输出 token 数
            temperature: 采样温度

        Returns:
            生成的图片 URL、base64 数据或文本描述
        """
        payload = {
            "model": GENERATION_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        response = self.client.post(CHAT_ENDPOINT, json=payload)
        response.raise_for_status()
        data = response.json()

        content = data["choices"][0]["message"]["content"]

        # 尝试提取图片
        image_data = self._extract_image_from_response(content)
        if image_data and output_path:
            save_base64_image(image_data, output_path)

        return content

    @staticmethod
    def _extract_image_from_response(content: str) -> Optional[str]:
        """从响应内容中提取 base64 图片数据"""
        # 尝试匹配 markdown 图片中的 base64
        import re

        # 匹配 ![...](data:image/...;base64,...)
        md_pattern = r"!\[.*?\]\((data:image/[^;]+;base64,[^)]+)\)"
        match = re.search(md_pattern, content)
        if match:
            return match.group(1)

        # 匹配裸 base64 data URL
        raw_pattern = r"(data:image/[^;]+;base64,[A-Za-z0-9+/=]+)"
        match = re.search(raw_pattern, content)
        if match:
            return match.group(1)

        return None

    def close(self):
        """关闭 HTTP 客户端"""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ============ CLI 命令 ============

def cmd_understand(args: argparse.Namespace) -> int:
    """执行图片理解命令"""
    client = VisionClient()

    try:
        if args.image and args.image_url:
            print("错误: 不能同时指定 --image 和 --image-url")
            return 1

        if args.image_url:
            result = client.understand_image(
                image_source=args.image_url,
                prompt=args.prompt,
                is_url=True,
                max_tokens=args.max_tokens,
                temperature=args.temperature,
            )
        elif args.image:
            result = client.understand_image(
                image_source=args.image,
                prompt=args.prompt,
                is_url=False,
                max_tokens=args.max_tokens,
                temperature=args.temperature,
            )
        else:
            print("错误: 必须指定 --image 或 --image-url")
            return 1

        print(result)
        return 0

    except Exception as e:
        print(f"请求失败: {e}")
        return 1
    finally:
        client.close()


def cmd_generate(args: argparse.Namespace) -> int:
    """执行图片生成命令"""
    client = VisionClient()

    try:
        result = client.generate_image(
            prompt=args.prompt,
            output_path=args.output,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
        )
        print(result)
        return 0

    except Exception as e:
        print(f"请求失败: {e}")
        return 1
    finally:
        client.close()


# ============ 主入口 ============

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="multimodal-vision",
        description="多模态图片理解与生成工具",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # understand 子命令
    understand_parser = subparsers.add_parser("understand", help="理解/描述图片内容")
    understand_parser.add_argument("--image", "-i", type=str, help="本地图片路径")
    understand_parser.add_argument("--image-url", "-u", type=str, help="图片 URL")
    understand_parser.add_argument(
        "--prompt", "-p", type=str, default="请详细描述这张图片的内容", help="提示词"
    )
    understand_parser.add_argument(
        "--max-tokens", type=int, default=4096, help="最大输出 token 数"
    )
    understand_parser.add_argument(
        "--temperature", type=float, default=0.5, help="采样温度"
    )
    understand_parser.set_defaults(func=cmd_understand)

    # generate 子命令
    generate_parser = subparsers.add_parser("generate", help="根据文本生成图片")
    generate_parser.add_argument("--prompt", "-p", type=str, required=True, help="图片描述")
    generate_parser.add_argument(
        "--output", "-o", type=str, help="输出图片路径（如指定则保存）"
    )
    generate_parser.add_argument(
        "--max-tokens", type=int, default=2048, help="最大输出 token 数"
    )
    generate_parser.add_argument(
        "--temperature", type=float, default=0.9, help="采样温度"
    )
    generate_parser.set_defaults(func=cmd_generate)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

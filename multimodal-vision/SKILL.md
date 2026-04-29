---
name: multimodal-vision
description: |
  多模态图片理解与生成 Skill。通过 Python 脚本调用标准 OpenAI 兼容 API，支持图片内容理解（vision）和文本生成图片（image generation）。
  图片理解模型：gemini-3.1-flash-lite-preview
  图片生成模型：gemini-3.1-flash-image-preview
  API 端点：https://api.vectorengine.ai/v1/chat/completions
  调用入口：main.py 中的 VisionClient 类
  触发场景：用户要求分析/描述图片内容、生成图片、根据图片回答问题、OCR 提取文字等。
---

# Multimodal Vision

本 Skill 提供基于 OpenAI 兼容协议的多模态图片理解与生成能力。所有调用均通过 Python 脚本完成。

## API 配置

```python
BASE_URL = "https://api.vectorengine.ai/v1"
API_KEY = "sk-6bFxUxRh9Xc8TZFwj30JyRTIL0CWwjoJPDEKSnfuOCEJZrI6"
CHAT_ENDPOINT = "https://api.vectorengine.ai/v1/chat/completions"

VISION_MODEL = "gemini-3.1-flash-lite-preview"
GENERATION_MODEL = "gemini-3.1-flash-image-preview"
```

## 模型映射

| 能力 | 模型 | 用途 |
|------|------|------|
| 图片理解 | `gemini-3.1-flash-lite-preview` | 分析、描述、理解图片内容 |
| 图片生成 | `gemini-3.1-flash-image-preview` | 根据文本提示生成图片 |

---

## 使用前提

确保已安装依赖并进入项目目录：

```bash
cd /Users/Zhuanz/.agents/skills/multimodal-vision
uv sync
```

核心调用入口为 `main.py` 中的 `VisionClient` 类。

---

## 能力一：图片理解（Vision）

### 适用场景

- 描述图片内容
- 从图片中提取文字（OCR）
- 回答关于图片的具体问题
- 识别图片中的物体、场景、人物、文字
- 分析图表、截图、文档

### Python 调用方式

**单张本地图片理解：**

```python
from main import VisionClient

with VisionClient() as client:
    result = client.understand_image(
        image_source="./photo.jpg",
        prompt="请详细描述这张图片的内容",
        is_url=False,
        max_tokens=4096,
        temperature=0.5,
    )
    print(result)
```

**网络图片 URL 理解：**

```python
with VisionClient() as client:
    result = client.understand_image(
        image_source="https://example.com/image.jpg",
        prompt="这张图片里有什么？",
        is_url=True,
    )
    print(result)
```

**多张图片对比理解：**

```python
with VisionClient() as client:
    result = client.understand_multiple_images(
        image_sources=["./a.jpg", "./b.jpg"],
        prompt="比较这两张图片的异同",
        are_urls=False,
    )
    print(result)
```

### 底层请求格式

`VisionClient` 内部构造的标准 OpenAI 兼容请求体：

```python
payload = {
    "model": VISION_MODEL,
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}},  # 本地图片自动转 base64 data URL
            ],
        }
    ],
    "max_tokens": max_tokens,
    "temperature": temperature,
}

response = httpx.post(CHAT_ENDPOINT, json=payload, headers={"Authorization": f"Bearer {API_KEY}"})
result = response.json()["choices"][0]["message"]["content"]
```

---

## 能力二：图片生成（Image Generation）

### 适用场景

- 根据文本描述生成图片
- 创作插画、概念图、海报
- 生成特定风格的图像

### Python 调用方式

```python
from main import VisionClient

with VisionClient() as client:
    result = client.generate_image(
        prompt="画一只穿着宇航服的猫，卡通风格",
        output_path="./cat.png",  # 指定则自动保存图片
        max_tokens=2048,
        temperature=0.9,
    )
    print(result)
```

### 响应处理逻辑

`generate_image` 方法会自动处理以下响应格式：

1. **Markdown 图片链接**：提取 `![alt](data:image/...;base64,...)` 中的 base64 数据
2. **裸 base64 data URL**：直接提取 `data:image/...;base64,...`
3. 若提供了 `output_path`，自动解码并保存为本地图片文件

### 底层请求格式

```python
payload = {
    "model": GENERATION_MODEL,
    "messages": [{"role": "user", "content": prompt}],
    "max_tokens": max_tokens,
    "temperature": temperature,
}

response = httpx.post(CHAT_ENDPOINT, json=payload, headers={"Authorization": f"Bearer {API_KEY}"})
content = response.json()["choices"][0]["message"]["content"]
```

---

## 命令行使用（CLI）

除 Python 直接调用外，也支持命令行：

```bash
# 理解本地图片
uv run python main.py understand -i ./photo.jpg -p "描述这张图片"

# 理解网络图片
uv run python main.py understand -u https://example.com/img.jpg

# 生成图片
uv run python main.py generate -p "日落海边的风景" -o ./sunset.png
```

---

## 混合工作流

可组合两个能力形成工作流：

```python
with VisionClient() as client:
    # 步骤1：理解参考图的风格
    style_desc = client.understand_image(
        "./reference.jpg",
        prompt="描述这张图的艺术风格和构图特点",
    )

    # 步骤2：基于风格描述生成新图
    client.generate_image(
        prompt=f"生成一张类似风格的图片：{style_desc}",
        output_path="./generated.png",
    )
```

---

## 通用参数建议

| 参数 | 图片理解 | 图片生成 |
|------|----------|----------|
| `temperature` | 0.3 - 0.7 | 0.7 - 1.0 |
| `max_tokens` | 2048 - 4096 | 2048 |
| `timeout` | 120s | 120s |

---

## 错误处理

| 异常/错误码 | 含义 | 处理建议 |
|-------------|------|----------|
| `FileNotFoundError` | 本地图片路径不存在 | 检查 `image_source` 路径 |
| 401 | API Key 无效 | 检查 `API_KEY` 配置 |
| 404 | 模型不存在 | 确认模型名称拼写正确 |
| 429 | 请求过于频繁 | 增加重试间隔或降低并发 |
| 500/502 | 服务端错误 | 稍后重试 |
| 400 | 图片格式/大小不支持 | 转换为 JPEG/PNG，压缩至 5MB 以下 |

---

## 使用注意事项

1. **图片格式**：优先使用 JPEG、PNG、WEBP
2. **图片大小**：单张图片建议不超过 5MB，过大图片应先压缩
3. **Base64 开销**：大图片 base64 编码后体积增加约 33%，注意请求体大小限制
4. **URL 可访问性**：使用图片 URL 时确保该 URL 对 API 服务端可公开访问
5. **敏感内容**：避免上传或生成违反使用政策的图片内容
6. **上下文长度**：多图输入会快速消耗上下文 token，注意控制图片数量
7. **客户端生命周期**：建议使用 `with VisionClient() as client:` 上下文管理器，确保连接正确关闭

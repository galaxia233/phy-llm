"""
API 客户端模块

提供调用 AI API 的函数
"""

import base64
import time
from pathlib import Path
from typing import Union, List, Tuple

import requests

from config import (
    API_URL,
    API_KEY,
    DEFAULT_MODEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    check_api_key,
)
from datagroup.file_converter import (
    convert_pdf_to_images,
    convert_word_to_images,
    IMAGE_MEDIA_MAP,
    is_supported_image,
    get_media_type,
)


def read_md_file(path: str) -> str:
    """
    读取 Markdown 文件内容

    Args:
        path: md 文件路径

    Returns:
        md 文件的文本内容

    Raises:
        FileNotFoundError: 文件不存在
        IOError: 读取失败
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"md 文件不存在：{path}")
    except UnicodeDecodeError:
        # 尝试其他编码
        with open(path, "r", encoding="gbk") as f:
            return f.read()
    except IOError as e:
        raise IOError(f"读取 md 文件失败：{path}, 错误：{e}")


def ask_ai(
    prompt: str,
    files: Union[str, List[str], None] = None,
    system: str = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> str:
    """
    调用 AI API 回答问题

    Args:
        prompt: 问题文本
        files: 文件路径，可以是单个路径 (str) 或多个路径的列表 (list[str])
               支持的文件类型：
               - 图片：.jpg, .jpeg, .png, .gif, .webp
               - PDF: .pdf（转换为图片，每页一张）
               - Word: .docx, .doc（转换为图片，每页一张）
               - Markdown: .md（直接读取文本内容）
               文件会按顺序添加到消息中，可以用 [文件 1], [文件 2] 等方式在 prompt 中指代
               注意：PDF/Word/MD 文件整体使用一个编号，只有第一页/开头会显示文件标记
        system: 系统提示
        model: 模型名称
        max_tokens: 最大生成 token 数
        max_retries: 最大重试次数

    Returns:
        AI 回答文本

    Raises:
        ValueError: 不支持的文件类型
        FileNotFoundError: 文件不存在
        IOError: 读取文件失败
        RuntimeError: 请求失败
    """
    # 检查 API key
    check_api_key()
    
    # 构建 content
    content = []
    
    # 标准化 files 为列表
    if files is None:
        file_paths = []
    elif isinstance(files, str):
        file_paths = [files]
    else:
        file_paths = list(files)

    # 收集所有要处理的图片（包括从 PDF/Word 转换来的）
    # all_files: List[Tuple[bytes, str, str, bool]] = [(image_bytes, media_type, display_name, add_marker), ...]
    # add_marker 表示是否需要添加文件标记
    all_files: List[Tuple[bytes, str, str, bool]] = []

    # 收集所有 md 文件的文本内容
    md_contents: List[str] = []

    file_counter = 0  # 文件编号计数器

    for path in file_paths:
        suffix = Path(path).suffix.lower()

        # 判断文件类型并处理
        if is_supported_image(suffix):
            # 图片文件 - 每个图片独立计数
            file_counter += 1
            media_type = get_media_type(suffix)
            try:
                with open(path, "rb") as f:
                    image_data = f.read()
            except FileNotFoundError:
                raise FileNotFoundError(f"图片文件不存在：{path}")
            except IOError as e:
                raise IOError(f"读取图片文件失败：{path}, 错误：{e}")
            all_files.append((image_data, media_type, Path(path).name, True))

        elif suffix == ".pdf":
            # PDF 文件 - 整个文件计为一个编号，发送所有页
            file_counter += 1
            pdf_images = convert_pdf_to_images(path)
            for i, (img_bytes, name) in enumerate(pdf_images):
                all_files.append((img_bytes, "image/png", f"{Path(path).stem}.pdf", i == 0))

        elif suffix in [".docx", ".doc"]:
            # Word 文件 - 整个文件计为一个编号，发送所有页
            file_counter += 1
            word_images = convert_word_to_images(path)
            for i, (img_bytes, name) in enumerate(word_images):
                all_files.append((img_bytes, "image/png", f"{Path(path).stem}.{suffix[1:]}", i == 0))

        elif suffix == ".md":
            # Markdown 文件 - 读取文本内容
            file_counter += 1
            md_content = read_md_file(path)
            md_contents.append(f"[文件 {file_counter}: {Path(path).name}]\n\n{md_content}")

        else:
            raise ValueError(f"不支持的文件类型：{suffix}, 文件：{path}")
    
    # 将所有图片添加到 content
    for idx, (img_bytes, media_type, name, add_marker) in enumerate(all_files, start=1):
        image_data = base64.b64encode(img_bytes).decode("utf-8")
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": image_data}
        })
        if add_marker:
            content.append({
                "type": "text",
                "text": f"[文件 {idx}: {name}]"
            })

    # 将 md 文件内容添加到 content
    for md_content in md_contents:
        content.append({
            "type": "text",
            "text": md_content
        })

    content.append({"type": "text", "text": prompt})
    
    body = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": content}],
    }
    if system:
        body["system"] = system

    # 重试逻辑
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(
                API_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {API_KEY}",
                    "anthropic-version": "2023-06-01",
                },
                json=body,
                timeout=DEFAULT_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            # 找 type == "text" 的块
            text_block = next(block for block in data["content"] if block["type"] == "text")
            return text_block["text"]

        except requests.exceptions.Timeout as e:
            last_error = e
            print(f"[attempt {attempt+1}] 超时，重试中...")

        except requests.exceptions.HTTPError as e:
            # 4xx 错误不重试（请求本身有问题，重试也没用）
            if response.status_code < 500:
                raise
            last_error = e
            print(f"[attempt {attempt+1}] 服务器错误 {response.status_code}，重试中...")

        except Exception as e:
            last_error = e
            print(f"[attempt {attempt+1}] 未知错误：{e}，重试中...")

        # 指数退避：1s, 2s, 4s
        if attempt < max_retries:
            wait = 2 ** attempt
            print(f"等待 {wait}s 后重试...")
            time.sleep(wait)

    raise RuntimeError(f"请求失败，已重试 {max_retries} 次，最后错误：{last_error}")
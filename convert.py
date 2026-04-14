# Copyright (c) Opendatalab. All rights reserved.
import asyncio
import os
import tempfile
from pathlib import Path

import httpx

from mineru.cli import api_client as _api_client
from mineru.cli.common import image_suffixes, office_suffixes, pdf_suffixes
from mineru.utils.guess_suffix_or_lang import guess_suffix_by_path

SUPPORTED_INPUT_SUFFIXES = set(pdf_suffixes + image_suffixes + office_suffixes)


def collect_input_files(input_path: str | Path) -> list[Path]:
    path = Path(input_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Input path does not exist: {path}")

    if path.is_file():
        file_suffix = guess_suffix_by_path(path)
        if file_suffix not in SUPPORTED_INPUT_SUFFIXES:
            raise ValueError(f"Unsupported input file type: {path.name}")
        return [path]

    if not path.is_dir():
        raise ValueError(f"Input path must be a file or directory: {path}")

    input_files = sorted(
        (
            candidate.resolve()
            for candidate in path.iterdir()
            if candidate.is_file()
            and guess_suffix_by_path(candidate) in SUPPORTED_INPUT_SUFFIXES
        ),
        key=lambda item: item.name,
    )
    if not input_files:
        raise ValueError(f"No supported files found in directory: {path}")
    return input_files


def build_form_data(
    language: str,
    backend: str,
    parse_method: str,
    formula_enable: bool,
    table_enable: bool,
    server_url: str | None,
    start_page_id: int,
    end_page_id: int | None,
) -> dict[str, str | list[str]]:
    return _api_client.build_parse_request_form_data(
        lang_list=[language],
        backend=backend,
        parse_method=parse_method,
        formula_enable=formula_enable,
        table_enable=table_enable,
        server_url=server_url,
        start_page_id=start_page_id,
        end_page_id=end_page_id,
        return_md=True,
        return_middle_json=False,
        return_model_output=False,
        return_content_list=False,
        return_images=False,#True,
        response_format_zip=True,
        return_original_file=False,
    )


def format_status_message(status_snapshot: _api_client.TaskStatusSnapshot) -> str:
    if status_snapshot.queued_ahead is None:
        return status_snapshot.status
    return f"{status_snapshot.status} (queued_ahead={status_snapshot.queued_ahead})"


def prepare_local_api_temp_dir() -> None:
    current_temp_dir = Path(tempfile.gettempdir())
    if os.name == "nt" or not Path("/tmp").exists():
        return
    if not str(current_temp_dir).startswith("/mnt/"):
        return

    # vLLM/ZeroMQ IPC sockets fail on drvfs-backed temp directories under WSL.
    os.environ["TMPDIR"] = "/tmp"
    tempfile.tempdir = None


async def run_demo(
    input_path: str | Path,
    output_dir: str | Path,
    *,
    api_url: str | None = None,
    backend: str = "hybrid-auto-engine",
    parse_method: str = "auto",
    language: str = "ch",
    formula_enable: bool = True,
    table_enable: bool = True,
    server_url: str | None = None,
    start_page_id: int = 0,
    end_page_id: int | None = None,
) -> None:
    api_url = api_url or None
    server_url = server_url or None
    if backend.endswith("http-client") and not server_url:
        raise ValueError(f"backend={backend} requires server_url")

    input_files = collect_input_files(input_path)
    output_path = Path(output_dir).expanduser().resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    form_data = build_form_data(
        language=language,
        backend=backend,
        parse_method=parse_method,
        formula_enable=formula_enable,
        table_enable=table_enable,
        server_url=server_url,
        start_page_id=start_page_id,
        end_page_id=end_page_id,
    )
    upload_assets = [
        _api_client.UploadAsset(path=file_path, upload_name=file_path.name)
        for file_path in input_files
    ]

    local_server: _api_client.LocalAPIServer | None = None
    result_zip_path: Path | None = None
    task_label = f"{len(input_files)} file(s)"

    async with httpx.AsyncClient(
        timeout=_api_client.build_http_timeout(),
        follow_redirects=True,
    ) as http_client:
        try:
            if api_url is None:
                prepare_local_api_temp_dir()
                local_server = _api_client.LocalAPIServer()
                base_url = local_server.start()
                print(f"Started local mineru-api: {base_url}")
                server_health = await _api_client.wait_for_local_api_ready(
                    http_client,
                    local_server,
                )
            else:
                server_health = await _api_client.fetch_server_health(
                    http_client,
                    _api_client.normalize_base_url(api_url),
                )

            print(f"Using API: {server_health.base_url}")
            print(f"Submitting {len(upload_assets)} file(s)")
            submit_response = await _api_client.submit_parse_task(
                base_url=server_health.base_url,
                upload_assets=upload_assets,
                form_data=form_data,
            )
            print(f"task_id: {submit_response.task_id}")
            if submit_response.queued_ahead is not None:
                print(f"status: pending (queued_ahead={submit_response.queued_ahead})")

            last_status_message = None

            def on_status_update(status_snapshot: _api_client.TaskStatusSnapshot) -> None:
                nonlocal last_status_message
                message = format_status_message(status_snapshot)
                if message == last_status_message:
                    return
                last_status_message = message
                print(f"status: {message}")

            await _api_client.wait_for_task_result(
                client=http_client,
                submit_response=submit_response,
                task_label=task_label,
                status_snapshot_callback=on_status_update,
            )
            print("status: completed")
            result_zip_path = await _api_client.download_result_zip(
                client=http_client,
                submit_response=submit_response,
                task_label=task_label,
            )
        finally:
            if local_server is not None:
                local_server.stop()

    assert result_zip_path is not None
    try:
        _api_client.safe_extract_zip(result_zip_path, output_path)
    finally:
        result_zip_path.unlink(missing_ok=True)
    print(f"Extracted result to: {output_path}")


import json
import re


def split_question(
    input_md_path: str | Path,
    output_dir: str | Path | None = None,
    category: str = "phy",
    write_metadata: bool = True,
) -> list[Path]:
    """
    将 md 格式的试卷文件按题目切分成多个 md 文件。

    支持识别的题目开头格式：
    - 题一、题二、...
    - 一、二、三、...（中文数字 + 顿号）
    - 第一题、第二题、...

    Args:
        input_md_path: 输入的 md 文件路径
        output_dir: 输出目录，默认为输入文件所在目录下的以原文件名命名的文件夹
        category: 题目类别代码，用于 metadata.jsonl 中的 category 字段
        write_metadata: 是否写入 metadata.jsonl 文件

    Returns:
        生成的题目文件路径列表
    """
    input_path = Path(input_md_path).expanduser().resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")
    if not input_path.suffix.lower() == ".md":
        raise ValueError(f"Input file must be a .md file: {input_path}")

    # 确定输出目录
    if output_dir is None:
        output_dir = input_path.parent / input_path.stem
    else:
        output_dir = Path(output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # 读取文件内容
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 题目开头匹配模式
    # 1. 题一、题二、...
    # 2. 一、二、三、...（中文数字 + 顿号/点）
    # 3. 第一题、第二题、...
    # 使用负向前瞻排除 (1) (1.1) (2.1) 这种带括号的格式
    question_pattern = re.compile(
        r"(?m)^(\s*)"  # 前导空白
        r"(?![(\uff08])"  # 负向前瞻：行首不能紧跟括号
        r"(?:"
        r"(题 [零一二三四五六七八九十百千万]+[、.．])|"  # 题一、题二、...
        r"([零一二三四五六七八九十百千万]+[、.．])|"  # 一、二、三、...
        r"(第 [零一二三四五六七八九十百千万]+ 题[、.．]?)"  # 第一题、第二题、...
        r")"
    )

    # 找到所有匹配位置
    matches = list(question_pattern.finditer(content))
    if not matches:
        # 没有找到题目分割符，整个文件作为一题
        output_file = output_dir / f"{input_path.stem}_1.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        return [output_file]

    # 中文数字映射
    chinese_num_map = {
        "零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
        "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
        "百": 100, "千": 1000, "万": 10000
    }

    def parse_chinese_num(text: str) -> int:
        """解析中文数字为阿拉伯数字"""
        text = text.strip("、.．")
        if not text:
            return 0
        # 中文数字
        result = 0
        temp = 0
        for char in text:
            if char in chinese_num_map:
                val = chinese_num_map[char]
                if val >= 100:
                    result += temp * val
                    temp = 0
                else:
                    temp += val
        return result + temp

    def extract_question_number(match_text: str) -> int:
        """从匹配文本中提取题号"""
        match_text = match_text.strip()
        # 第一题、题一
        match_obj = re.search(r"[第 题]?([零一二三四五六七八九十百千万]+)", match_text)
        if match_obj:
            num_str = match_obj.group(1)
            return parse_chinese_num(num_str)
        return 1

    # 切分题目并收集 metadata
    output_files = []
    metadata_entries = []
    base_name = input_path.stem

    for i, match in enumerate(matches):
        start_pos = match.start()
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(content)

        question_content = content[start_pos:end_pos].strip()
        question_num = extract_question_number(match.group())

        # 生成 id：使用 原文件名_题号 作为 id
        question_id = f"{base_name}_{question_num}"

        output_file = output_dir / f"problems/{question_id}.md"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(question_content)
        output_files.append(output_file)

        # 创建 metadata 条目
        metadata_entries.append({
            "id": question_id,
            "problem": f"problems/{question_id}.md",
            "solution": f"solutions/{question_id}.md",
            "category": category,
        })

    # 写入 metadata.jsonl
    if write_metadata and metadata_entries:
        metadata_file = output_dir / "metadata.jsonl"
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_file, "a", encoding="utf-8") as f:
            for entry in metadata_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"Wrote {len(metadata_entries)} metadata entries to: {metadata_file}")

    print(f"Split {len(output_files)} question(s) to: {output_dir}")
    return output_files


def main() -> None:
    demo_dir = Path(__file__).resolve().parent

    # Input can be a single supported file or a directory containing supported files.
    input_path = demo_dir / "input"
    # Parsed outputs will be extracted into this directory.
    output_dir = demo_dir / "output" / "raw"
    # Set this to an existing MinerU FastAPI base URL, for example:
    # "http://127.0.0.1:8000"
    # Leave it as None to start a temporary local mineru-api automatically.
    api_url = None

    # Available examples:
    # "hybrid-auto-engine"   -> local hybrid parsing, recommended default
    # "pipeline"             -> more general OCR/text pipeline
    # "vlm-auto-engine"      -> local VLM parsing
    # "vlm-http-client"      -> remote OpenAI-compatible VLM server
    # "hybrid-http-client"   -> remote OpenAI-compatible hybrid server
    backend = "hybrid-auto-engine"
    # Available options:
    # "auto" -> let MinerU choose between text extraction and OCR
    # "txt"  -> force text extraction
    # "ocr"  -> force OCR
    parse_method = "auto"
    # OCR language hint. This is mainly used by pipeline and hybrid backends.
    language = "ch"
    # Enable formula parsing in the output.
    formula_enable = True
    # Enable table parsing in the output.
    table_enable = True
    # Required only for "*-http-client" backends, for example:
    # "http://127.0.0.1:30000"
    server_url = None
    # Zero-based page range. Set end_page_id to None to parse to the last page.
    start_page_id = 0
    end_page_id = None

    """如果您由于网络问题无法下载模型，可以设置环境变量MINERU_MODEL_SOURCE为modelscope使用免代理仓库下载模型"""
    os.environ['MINERU_MODEL_SOURCE'] = "modelscope"

    asyncio.run(
        run_demo(
            input_path=input_path,
            output_dir=output_dir,
            api_url=api_url,
            backend=backend,
            parse_method=parse_method,
            language=language,
            formula_enable=formula_enable,
            table_enable=table_enable,
            server_url=server_url,
            start_page_id=start_page_id,
            end_page_id=end_page_id,
        )
    )
    print(f"已转换{input_path}内容到{output_dir}")

main()

raw=Path(__file__).resolve().parent / "output" / "raw"
for file_path in raw.rglob("*"):
    if file_path.is_file() and file_path.suffix == ".md":
        print(f"切分文件: {file_path.relative_to(raw)}")
        split_question(
            input_md_path=file_path,
            output_dir=Path(__file__).resolve().parent / "output" / "problem",
            category="test",
            write_metadata=True,
        )

#输出
import os
import magnus
secret = magnus.custody_file(os.path.join(Path(__file__).resolve().parent, "output"))
with open(os.environ["MAGNUS_ACTION"],"w") as f:
    f.write(f"magnus receive {secret} --output output\n")

print("处理完成")
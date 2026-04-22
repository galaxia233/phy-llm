"""
完整的题目处理 Pipeline

流程：
1. 按一级标题 (#) 切分大文件
2. 切分过长的章节（保持重叠）
3. 并行处理每个小文件，提取 QA 到 JSONL
"""

import json
import re
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from api_client import ask_ai
from system_prompts import SystemPrompts


# ==================== 第一阶段：按标题切分 ====================

def split_by_heading(md_content: str, min_lines: int = 5) -> list[tuple[str, str]]:
    """按一级标题切分内容"""
    heading_pattern = r'^(#\s+.+)$'
    lines = md_content.split('\n')

    sections = []
    current_heading = None
    current_content = []

    for line in lines:
        match = re.match(heading_pattern, line)
        if match:
            if current_heading is not None and current_content:
                content_str = '\n'.join(current_content).strip()
                if len(current_content) >= min_lines:
                    sections.append((current_heading, content_str))
                else:
                    if sections:
                        prev_heading, prev_content = sections.pop()
                        merged_content = prev_content + '\n\n' + content_str
                        sections.append((prev_heading, merged_content))
                    else:
                        sections.append((current_heading, content_str))

            current_heading = match.group(1).strip()
            current_content = []
        else:
            current_content.append(line)

    if current_heading is not None and current_content:
        content_str = '\n'.join(current_content).strip()
        sections.append((current_heading, content_str))

    return sections


def sanitize_filename(heading: str) -> str:
    """将标题转换为安全的文件名"""
    name = heading.lstrip('#').strip()
    name = name.replace('/', '_').replace('\\', '_')
    name = name.replace(':', '_').replace('*', '_')
    name = name.replace('?', '_').replace('"', '_')
    name = name.replace('<', '_').replace('>', '_').replace('|', '_')
    if len(name) > 100:
        name = name[:100]
    return name


def stage1_split(input_file: str, output_dir: str = None) -> Path:
    """第一阶段：按一级标题切分"""
    input_path = Path(input_file)

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    sections = split_by_heading(content)

    if not sections:
        print("未找到任何一级标题，无法切分")
        return None

    if output_dir is None:
        output_dir = input_path.parent / f"{input_path.stem}_split"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[阶段 1] 找到 {len(sections)} 个章节，开始切分...")
    for i, (heading, section_content) in enumerate(sections, 1):
        safe_name = sanitize_filename(heading)
        output_file = output_dir / f"{i:03d}_{safe_name}.md"

        full_content = f"{heading}\n\n{section_content}"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_content)

        print(f"  [{i:03d}] {heading[:50]}... -> {output_file.name}")

    print(f"[阶段 1] 完成，输出目录：{output_dir}\n")
    return output_dir


# ==================== 第二阶段：切分过长章节 ====================

def estimate_tokens(text: str) -> int:
    """估算文本的 token 数"""
    return len(text) // 2


def find_cut_position(content_lines: list[str], target_lines: int,
                      max_tokens: int, overlap_lines: int = 0) -> int:
    """找到合适的切分位置"""
    if len(content_lines) <= target_lines:
        return len(content_lines)

    token_limit_idx = len(content_lines)
    cumulative_chars = 0
    for i, line in enumerate(content_lines):
        cumulative_chars += len(line)
        if estimate_tokens('\n'.join(content_lines[:i+1])) > max_tokens:
            token_limit_idx = i
            break

    cut_range_end = min(target_lines, token_limit_idx)
    cut_range_start = cut_range_end // 2

    # 策略 1：找题目编号【数字】
    for i in range(cut_range_end - 1, cut_range_start - 1, -1):
        if re.match(r'^\s*【\d+】', content_lines[i]):
            return i

    # 策略 2：找空行
    for i in range(cut_range_end - 1, cut_range_start - 1, -1):
        if content_lines[i].strip() == '':
            before = '\n'.join(content_lines[:i])
            dollar_count = before.count('$$')
            if dollar_count % 2 == 0:
                return i

    # 策略 3：找公式块结束
    in_equation = False
    for i in range(cut_range_end - 1, cut_range_start - 1, -1):
        line = content_lines[i]
        if '$$' in line:
            in_equation = not in_equation
        if not in_equation and '$$' in line and line.strip().endswith('$$'):
            return i + 1

    return cut_range_end


def chunk_section(heading: str, content: str,
                  max_lines: int = 80,
                  max_tokens: int = 6000,
                  overlap_lines: int = 15) -> list[tuple[str, str]]:
    """将过长的章节切分成多个小块"""
    lines = content.split('\n')

    if len(lines) <= max_lines and estimate_tokens(content) <= max_tokens:
        return [(heading, content)]

    chunks = []
    start_idx = 0
    chunk_num = 0

    while start_idx < len(lines):
        chunk_num += 1

        if start_idx == 0:
            actual_start = 0
        else:
            actual_start = max(0, start_idx - overlap_lines)

        remaining_lines = lines[actual_start:]
        cut_pos = find_cut_position(
            remaining_lines,
            max_lines,
            max_tokens,
            overlap_lines
        )

        if cut_pos <= 0:
            cut_pos = min(max_lines, len(remaining_lines))

        chunk_lines = remaining_lines[:cut_pos]
        chunk_content = '\n'.join(chunk_lines).strip()

        if chunk_num == 1:
            chunk_heading = heading
        else:
            chunk_heading = f"{heading} (续{chunk_num - 1})"

        chunks.append((chunk_heading, chunk_content))
        start_idx += cut_pos

        if start_idx >= len(lines):
            break

    return chunks


def stage2_chunk(input_dir: str, output_dir: str = None,
                 max_lines: int = 80,
                 max_tokens: int = 6000,
                 overlap_lines: int = 15) -> Path:
    """第二阶段：切分过长章节"""
    input_path = Path(input_dir)

    if input_path.is_file():
        input_files = [input_path]
    elif input_path.is_dir():
        input_files = list(input_path.glob("*.md"))
    else:
        raise FileNotFoundError(f"文件/目录不存在：{input_path}")

    if output_dir is None:
        output_dir = input_path.parent / f"{input_path.name}_chunked"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    total_chunks = 0
    global_idx = 0

    print(f"[阶段 2] 找到 {len(input_files)} 个文件，开始切分过长章节...")

    for input_file in sorted(input_files):
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')
        heading = lines[0].strip() if lines else input_file.stem
        body = '\n'.join(lines[1:]).strip()

        chunks = chunk_section(
            heading, body,
            max_lines=max_lines,
            max_tokens=max_tokens,
            overlap_lines=overlap_lines
        )

        for chunk_heading, chunk_content in chunks:
            global_idx += 1
            total_chunks += 1

            safe_name = f"{global_idx:04d}_{chunk_heading[:50]}.md"
            safe_name = safe_name.replace('/', '_').replace('\\', '_')
            safe_name = safe_name.replace(':', '_').replace('*', '_')

            output_file = output_dir / safe_name

            full_content = f"{chunk_heading}\n\n{chunk_content}"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_content)

            chunk_lines = chunk_content.split('\n')
            print(f"  [{global_idx:04d}] {len(chunk_lines)}行，"
                  f"{estimate_tokens(chunk_content)}tokens -> {output_file.name[:35]}...")

    print(f"[阶段 2] 完成！")
    print(f"  输入文件：{len(input_files)} 个")
    print(f"  输出文件：{total_chunks} 个")
    print(f"  输出目录：{output_dir}\n")
    return output_dir


# ==================== 第三阶段：提取 QA 到 JSONL ====================

file_lock = threading.Lock()


def process_file(file_path: Path, output_file: Path) -> bool:
    """处理单个文件，提取 QA"""
    print(f"Processing: {file_path.name}")
    try:
        result = ask_ai(
            prompt="请从这个 md 文件中提取题目和答案，转换为 JSONL 格式。",
            files=str(file_path),
            system=SystemPrompts.QA_EXTRACT_TO_JSON.value
        )

        # 线程安全地写入文件
        with file_lock:
            with open(output_file, "a", encoding="utf-8") as f:
                lines = result.strip().split('\n')
                valid_count = 0
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # 跳过空数组和空对象
                    if line in ['[]', '{}']:
                        continue

                    try:
                        data = json.loads(line)
                        # 跳过空数组或没有 question 字段的记录
                        if isinstance(data, list) and len(data) == 0:
                            continue
                        if isinstance(data, dict) and 'question' not in data:
                            continue
                        f.write(line + '\n')
                        valid_count += 1
                    except json.JSONDecodeError as e:
                        last_brace = line.rfind('}')
                        if last_brace != -1:
                            fixed_line = line[:last_brace + 1]
                            try:
                                data = json.loads(fixed_line)
                                if isinstance(data, dict) and 'question' in data:
                                    f.write(fixed_line + '\n')
                                    valid_count += 1
                            except:
                                pass

            # 提取完成后删除源文件
            if valid_count > 0:
                try:
                    file_path.unlink()
                    print(f"  [{file_path.name}] 已删除")
                except Exception as e:
                    print(f"  [{file_path.name}] 删除失败：{e}")

            print(f"  [{file_path.name}] 提取 {valid_count} 条 QA")
        return True
    except Exception as e:
        print(f"  [{file_path.name}] 失败：{e}")
        return False


def stage3_extract(input_dir: str, output_file: str = None, max_workers: int = 4) -> Path:
    """第三阶段：并行提取 QA 到 JSONL"""
    input_path = Path(input_dir)

    if output_file is None:
        output_file = input_path.parent / "qa_output.jsonl"
    else:
        output_file = Path(output_file)

    # 清空之前的内容
    with open(output_file, "w", encoding="utf-8") as f:
        pass

    files = list(input_path.glob("*.md"))
    print(f"[阶段 3] 找到 {len(files)} 个文件，开始并行提取 QA (并发数：{max_workers})...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_file, f, output_file): f for f in files}
        success_count = 0
        for future in as_completed(futures):
            if future.result():
                success_count += 1

    print(f"[阶段 3] 完成！")
    print(f"  成功：{success_count}/{len(files)}")
    print(f"  输出文件：{output_file}\n")
    return output_file


# ==================== 主 Pipeline ====================

def run_pipeline(input_file: str,
                 stage1_output: str = None,
                 stage2_output: str = None,
                 final_output: str = None,
                 max_workers: int = 4,
                 skip_stage1: bool = False,
                 skip_stage2: bool = False) -> Path:
    """
    运行完整的 Pipeline

    Args:
        input_file: 输入文件路径
        stage1_output: 阶段 1 输出目录（可选）
        stage2_output: 阶段 2 输出目录（可选）
        final_output: 最终输出文件（可选）
        max_workers: 阶段 3 并发数
        skip_stage1: 跳过阶段 1（如果已经切分好）
        skip_stage2: 跳过阶段 2（如果不需要进一步切分）

    Returns:
        最终输出文件路径
    """
    input_path = Path(input_file)

    print("=" * 60)
    print("题目处理 Pipeline")
    print("=" * 60)
    print(f"输入文件：{input_file}")
    print(f"并发数：{max_workers}")
    print("=" * 60 + "\n")

    # 阶段 1：按标题切分
    if skip_stage1:
        print("[跳过阶段 1]")
        if stage1_output is None:
            raise ValueError("跳过阶段 1 时，必须指定 stage1_output")
        stage1_dir = Path(stage1_output)
    else:
        stage1_dir = stage1_split(input_file, stage1_output)
        if stage1_dir is None:
            raise RuntimeError("阶段 1 失败")

    # 阶段 2：切分过长章节
    if skip_stage2:
        print("[跳过阶段 2]")
        if stage2_output is None:
            raise ValueError("跳过阶段 2 时，必须指定 stage2_output")
        stage2_dir = Path(stage2_output)
    else:
        stage2_dir = stage2_chunk(stage1_dir, stage2_output)

    # 阶段 3：提取 QA
    final_path = stage3_extract(stage2_dir, final_output, max_workers)

    print("=" * 60)
    print("Pipeline 完成！")
    print(f"最终输出：{final_path}")
    print("=" * 60)

    return final_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="题目处理 Pipeline")
    parser.add_argument("input_file", nargs="?", default="testdata/test.md",
                        help="输入文件路径")
    parser.add_argument("-o", "--output", type=str, help="最终输出文件路径")
    parser.add_argument("-w", "--workers", type=int, default=4,
                        help="并行处理的并发数")
    parser.add_argument("--skip-stage1", action="store_true",
                        help="跳过阶段 1（按标题切分）")
    parser.add_argument("--skip-stage2", action="store_true",
                        help="跳过阶段 2（切分过长章节）")
    parser.add_argument("--stage1-output", type=str, help="阶段 1 输出目录")
    parser.add_argument("--stage2-output", type=str, help="阶段 2 输出目录")

    args = parser.parse_args()

    run_pipeline(
        input_file=args.input_file,
        final_output=args.output,
        max_workers=args.workers,
        skip_stage1=args.skip_stage1,
        skip_stage2=args.skip_stage2,
        stage1_output=args.stage1_output,
        stage2_output=args.stage2_output,
    )

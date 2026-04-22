"""
切分过长的 Markdown 章节

按行数和 token 数双重限制切分，支持重叠窗口保持上下文
"""

import re
from pathlib import Path
from typing import List, Tuple


def estimate_tokens(text: str) -> int:
    """
    估算文本的 token 数

    中文/英文混合文本：大约 1 token = 1.5 字符
    """
    return len(text) // 2


def find_cut_position(content_lines: List[str], target_lines: int,
                      max_tokens: int, overlap_lines: int = 0) -> int:
    """
    找到合适的切分位置

    优先在以下位置切分：
    1. 公式块之间（$$ ... $$ 之外）
    2. 题目编号处（【数字】）
    3. 空行处

    Args:
        content_lines: 内容行列表
        target_lines: 目标行数
        max_tokens: 最大 token 数
        overlap_lines: 重叠行数

    Returns:
        切分位置的索引
    """
    if len(content_lines) <= target_lines:
        return len(content_lines)

    # 计算 token 限制的位置
    token_limit_idx = len(content_lines)
    cumulative_chars = 0
    for i, line in enumerate(content_lines):
        cumulative_chars += len(line)
        if estimate_tokens('\n'.join(content_lines[:i+1])) > max_tokens:
            token_limit_idx = i
            break

    # 在目标行数和 token 限制之间取较小值
    cut_range_end = min(target_lines, token_limit_idx)
    cut_range_start = cut_range_end // 2  # 从中间位置开始找

    # 策略 1：找题目编号【数字】
    for i in range(cut_range_end - 1, cut_range_start - 1, -1):
        if re.match(r'^\s*【\d+】', content_lines[i]):
            return i

    # 策略 2：找空行
    for i in range(cut_range_end - 1, cut_range_start - 1, -1):
        if content_lines[i].strip() == '':
            # 确保不在公式块中间
            before = '\n'.join(content_lines[:i])
            dollar_count = before.count('$$')
            if dollar_count % 2 == 0:  # 在公式块外
                return i

    # 策略 3：找公式块结束
    in_equation = False
    for i in range(cut_range_end - 1, cut_range_start - 1, -1):
        line = content_lines[i]
        if '$$' in line:
            in_equation = not in_equation
        if not in_equation and '$$' in line and line.strip().endswith('$$'):
            return i + 1

    # 默认：直接返回目标位置
    return cut_range_end


def chunk_section(heading: str, content: str,
                  max_lines: int = 100,
                  max_tokens: int = 8000,
                  overlap_lines: int = 10) -> List[Tuple[str, str]]:
    """
    将过长的章节切分成多个小块

    Args:
        heading: 章节标题
        content: 章节内容
        max_lines: 每块最大行数
        max_tokens: 每块最大 token 数
        overlap_lines: 重叠行数（保持上下文）

    Returns:
        [(heading, content), ...] 列表
    """
    lines = content.split('\n')

    # 如果不超过限制，直接返回
    if len(lines) <= max_lines and estimate_tokens(content) <= max_tokens:
        return [(heading, content)]

    chunks = []
    start_idx = 0
    chunk_num = 0

    while start_idx < len(lines):
        chunk_num += 1

        # 计算本次切片的起始位置（考虑重叠）
        if start_idx == 0:
            actual_start = 0
        else:
            # 重叠部分从前一块的末尾往前数
            actual_start = max(0, start_idx - overlap_lines)

        # 找合适的切分位置
        remaining_lines = lines[actual_start:]
        cut_pos = find_cut_position(
            remaining_lines,
            max_lines,
            max_tokens,
            overlap_lines
        )

        # 确保至少切分一些内容
        if cut_pos <= 0:
            cut_pos = min(max_lines, len(remaining_lines))

        # 提取当前块
        chunk_lines = remaining_lines[:cut_pos]
        chunk_content = '\n'.join(chunk_lines).strip()

        # 生成带子编号的标题
        if chunk_num == 1:
            chunk_heading = heading
        else:
            chunk_heading = f"{heading} (续{chunk_num - 1})"

        chunks.append((chunk_heading, chunk_content))

        # 更新起始位置
        start_idx += cut_pos

        # 如果已经处理完所有内容，退出
        if start_idx >= len(lines):
            break

    return chunks


def chunk_file(input_path: str, output_dir: str = None,
               max_lines: int = 100,
               max_tokens: int = 8000,
               overlap_lines: int = 10):
    """
    读取切分后的文件，进一步切分过长的章节

    Args:
        input_path: 输入文件或目录
        output_dir: 输出目录
        max_lines: 每块最大行数
        max_tokens: 每块最大 token 数
        overlap_lines: 重叠行数
    """
    input_path = Path(input_path)

    # 确定输入文件列表
    if input_path.is_file():
        input_files = [input_path]
    elif input_path.is_dir():
        input_files = list(input_path.glob("*.md"))
    else:
        raise FileNotFoundError(f"文件/目录不存在：{input_path}")

    # 确定输出目录
    if output_dir is None:
        output_dir = input_path.parent / f"{input_path.stem}_chunked"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    total_chunks = 0
    global_idx = 0

    print(f"找到 {len(input_files)} 个文件，开始切分过长章节...")

    for input_file in sorted(input_files):
        print(f"\n处理：{input_file.name}")

        # 读取文件
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取标题（第一行）
        lines = content.split('\n')
        heading = lines[0].strip() if lines else input_file.stem
        body = '\n'.join(lines[1:]).strip()

        # 切分过长章节
        chunks = chunk_section(
            heading, body,
            max_lines=max_lines,
            max_tokens=max_tokens,
            overlap_lines=overlap_lines
        )

        # 写入文件
        for chunk_heading, chunk_content in chunks:
            global_idx += 1
            total_chunks += 1

            # 生成文件名
            safe_name = f"{global_idx:04d}_{chunk_heading[:50]}.md"
            safe_name = safe_name.replace('/', '_').replace('\\', '_')
            safe_name = safe_name.replace(':', '_').replace('*', '_')
            safe_name = safe_name.replace('?', '_').replace('"', '_')

            output_file = output_dir / safe_name

            # 写入
            full_content = f"{chunk_heading}\n\n{chunk_content}"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_content)

            chunk_lines = chunk_content.split('\n')
            print(f"  [{global_idx:04d}] {len(chunk_lines)}行，"
                  f"{estimate_tokens(chunk_content)}tokens -> {output_file.name[:40]}...")

    print(f"\n切分完成！")
    print(f"输入文件：{len(input_files)} 个")
    print(f"输出文件：{total_chunks} 个")
    print(f"输出目录：{output_dir}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    else:
        # 默认处理 split_output 目录
        input_path = Path(__file__).parent / "testdata" / "split_output"

    # 可调节的参数
    chunk_file(
        input_path,
        max_lines=80,          # 每块最多 80 行
        max_tokens=6000,       # 每块最多 6000 tokens
        overlap_lines=15       # 重叠 15 行保持上下文
    )

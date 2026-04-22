"""
按一级标题 (#) 切分 Markdown 文件

将大文件按 # 标题分割成多个小文件
"""

import re
from pathlib import Path


def split_by_heading(md_content: str, min_lines: int = 5) -> list[tuple[str, str]]:
    """
    按一级标题切分内容

    Args:
        md_content: Markdown 文件内容
        min_lines: 最小行数，少于这个行数的章节会被合并到前一章

    Returns:
        [(heading_title, content), ...] 列表
    """
    # 匹配一级标题：行首的 # 后跟空格和内容
    heading_pattern = r'^(#\s+.+)$'
    lines = md_content.split('\n')

    sections = []
    current_heading = None
    current_content = []

    for line in lines:
        match = re.match(heading_pattern, line)
        if match:
            # 保存之前的章节
            if current_heading is not None and current_content:
                content_str = '\n'.join(current_content).strip()
                if len(current_content) >= min_lines:
                    sections.append((current_heading, content_str))
                else:
                    # 内容太少，合并到前一章
                    if sections:
                        prev_heading, prev_content = sections.pop()
                        merged_content = prev_content + '\n\n' + content_str
                        sections.append((prev_heading, merged_content))
                    else:
                        sections.append((current_heading, content_str))

            # 开始新章节
            current_heading = match.group(1).strip()
            current_content = []
        else:
            current_content.append(line)

    # 处理最后一章
    if current_heading is not None and current_content:
        content_str = '\n'.join(current_content).strip()
        sections.append((current_heading, content_str))

    return sections


def sanitize_filename(heading: str) -> str:
    """
    将标题转换为安全的文件名

    移除或替换不允许的字符
    """
    # 移除 # 符号和前后空格
    name = heading.lstrip('#').strip()
    # 替换不允许的字符
    name = name.replace('/', '_').replace('\\', '_')
    name = name.replace(':', '_').replace('*', '_')
    name = name.replace('?', '_').replace('"', '_')
    name = name.replace('<', '_').replace('>', '_').replace('|', '_')
    # 限制长度
    if len(name) > 100:
        name = name[:100]
    return name


def split_file(input_path: str, output_dir: str = None):
    """
    切分 Markdown 文件

    Args:
        input_path: 输入文件路径
        output_dir: 输出目录，默认为输入文件的同级目录
    """
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"文件不存在：{input_path}")

    # 读取内容
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 切分
    sections = split_by_heading(content)

    if not sections:
        print("未找到任何一级标题，无法切分")
        return

    # 确定输出目录
    if output_dir is None:
        output_dir = input_path.parent / f"{input_path.stem}_split"
        output_dir.mkdir(exist_ok=True)
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    # 写入文件
    print(f"找到 {len(sections)} 个章节，开始切分...")
    for i, (heading, section_content) in enumerate(sections, 1):
        safe_name = sanitize_filename(heading)
        output_file = output_dir / f"{i:03d}_{safe_name}.md"

        # 写入文件，添加原始标题
        full_content = f"{heading}\n\n{section_content}"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_content)

        print(f"  [{i:03d}] {heading} -> {output_file.name}")

    print(f"\n切分完成，输出目录：{output_dir}")
    print(f"共生成 {len(sections)} 个文件")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        # 默认处理 testdata/test.md
        input_file = Path(__file__).parent / "testdata" / "test.md"

    split_file(input_file)


if __name__ == "__main__":
    split_file("testdata/test.md","testdata/split_output")
"""
转换器模块

将题目和答案文件转换为 Markdown 格式（使用 LaTeX 公式）
"""

import os
import re
import time
from pathlib import Path
from typing import List, Optional, Tuple

from api_client import ask_ai
from system_prompts import SYSTEM_PROMPTS


def split_pdf_by_pages(
    pdf_path: str,
    start_page: int,
    end_page: int,
    output_path: str
) -> str:
    """
    从 PDF 中提取指定页码范围，生成新的 PDF
    
    Args:
        pdf_path: 原 PDF 文件路径
        start_page: 起始页码（从 0 开始）
        end_page: 结束页码（从 0 开始，包含）
        output_path: 输出 PDF 文件路径
    
    Returns:
        输出 PDF 文件路径
    """
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        new_doc = fitz.open()
        
        for page_num in range(start_page, min(end_page + 1, len(doc))):
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
        
        new_doc.save(output_path)
        new_doc.close()
        doc.close()
        return output_path
    except ImportError:
        raise ImportError("需要安装 PyMuPDF: pip install PyMuPDF")
    except Exception as e:
        raise IOError(f"分割 PDF 失败：{e}")


def is_content_duplicate(content1: str, content2: str) -> bool:
    """
    检测两段内容是否重复（重叠区重复）
    
    Args:
        content1: 前一批的内容
        content2: 当前批的内容
    
    Returns:
        True 表示重复，False 表示不重复
    """
    check_length = min(200, len(content1), len(content2))
    if check_length < 50:
        return False
    
    content1_tail = content1[-check_length:].strip()
    content2_head = content2[:check_length].strip()
    
    if content2_head in content1_tail:
        return True
    
    if check_length >= 100:
        compare_len = min(len(content1_tail), len(content2_head))
        if compare_len > 0:
            matches = sum(c1 == c2 for c1, c2 in zip(content1_tail[:compare_len], content2_head[:compare_len]))
            if matches / compare_len > 0.7:
                return True
    
    return False


def merge_questions(prev_questions: List[Tuple[str, str]], curr_questions: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """
    合并两批题目，处理跨页重复
    
    Args:
        prev_questions: 前一批的题目列表 [(题号，内容), ...]
        curr_questions: 当前批的题目列表 [(题号，内容), ...]
    
    Returns:
        合并后的题目列表
    """
    if not prev_questions:
        return curr_questions
    
    merged: List[Tuple[str, str]] = list(prev_questions)
    prev_nums = {q[0]: idx for idx, q in enumerate(prev_questions)}
    
    for q_num, content in curr_questions:
        if q_num in prev_nums:
            idx = prev_nums[q_num]
            prev_content = merged[idx][1]
            
            if is_content_duplicate(prev_content, content):
                if len(content) > len(prev_content):
                    merged[idx] = (q_num, content)
            else:
                merged[idx] = (q_num, prev_content + "\n" + content)
        else:
            merged.append((q_num, content))
    
    return merged


def split_questions_by_number(text: str) -> List[Tuple[str, str]]:
    """
    根据题号分割题目文本
    
    Args:
        text: Markdown 格式的题目文本
    
    Returns:
        [(题号，题目内容), ...] 列表
    """
    questions: List[Tuple[str, str]] = []
    
    patterns = [
        r'^(?:第？)?([一二三四五六七八九十\d]+)[.、,]',
        r'^(?:第？)?([一二三四五六七八九十\d]+) 题',
        r'^([A-Z])\.',
        r'^(\d+)\.',
    ]
    
    lines = text.split('\n')
    current_question_num: Optional[str] = None
    current_content: List[str] = []
    in_question = False
    in_answer = False  # 标记是否进入答案部分
    
    for line in lines:
        stripped = line.strip()
        
        # 检测答案部分开始，遇到答案部分则停止处理题目
        if stripped.startswith('## 答案') or stripped.startswith('# 答案'):
            in_answer = True
            # 保存当前题目
            if in_question and current_content and current_question_num:
                questions.append((current_question_num, '\n'.join(current_content)))
            break  # 遇到答案部分则停止处理
        
        if stripped.startswith('## 题目') or stripped.startswith('# 题目'):
            continue
        
        matched = False
        for pattern in patterns:
            match = re.match(pattern, stripped)
            if match:
                q_num = match.group(1)
                if q_num in "一二三四五六七八九十":
                    q_num = str("一二三四五六七八九十".index(q_num) + 1)
                
                if in_question and current_content and current_question_num:
                    questions.append((current_question_num, '\n'.join(current_content)))
                
                current_question_num = q_num
                current_content = [line]
                in_question = True
                matched = True
                break
        
        if not matched:
            if in_question and not in_answer:
                current_content.append(line)
    
    # 保存最后一个题目
    if in_question and current_content and current_question_num:
        questions.append((current_question_num, '\n'.join(current_content)))
    
    return questions


def doc2latex(
    question_file: str,
    answer_file: Optional[str] = None,
    output_dir: str = ".",
    exam_name: Optional[str] = None,
    pages_per_batch: int = 5,
    overlap_pages: int = 1,
) -> List[str]:
    """
    分批处理长文件，将题目和答案转换为 Markdown 格式并分割成多个文件
    
    使用重叠批次和题号去重合并来处理跨页题目
    题目和答案分别处理，答案文件命名为：试卷名 - 题号 -ans.md
    
    Args:
        question_file: 题目文件路径（PDF、Word 或图片）
        answer_file: 答案文件路径（PDF、Word 或图片）
        output_dir: 输出目录，默认为当前目录
        exam_name: 试卷名称，如果为 None 则从题目文件名提取
        pages_per_batch: 每批处理的页数
        overlap_pages: 重叠页数（用于处理跨页题目）
    
    Returns:
        生成的 .md 文件路径列表
    
    输出文件命名规则：
        - 题目：试卷名 - 题号.md
        - 答案：试卷名 - 题号 -ans.md
    """
    import tempfile
    import shutil
    
    if exam_name is None:
        exam_name = Path(question_file).stem
    
    os.makedirs(output_dir, exist_ok=True)
    
    start_time = time.time()
    
    print(f"正在分批处理 {question_file}...")
    
    try:
        import fitz
        doc = fitz.open(question_file)
        total_pages = len(doc)
        doc.close()
    except Exception as e:
        raise IOError(f"无法获取 PDF 页数：{e}")
    
    # 计算批次列表，避免多余的批次
    batches: List[Tuple[int, int]] = []
    current_start = 0
    while current_start < total_pages:
        batch_end = min(current_start + pages_per_batch, total_pages)
        batches.append((current_start, batch_end))
        
        next_start = batch_end - overlap_pages
        if next_start <= current_start or batch_end >= total_pages:
            break
        current_start = next_start
    
    print(f"文件共 {total_pages} 页，每批 {pages_per_batch} 页，重叠 {overlap_pages} 页，共 {len(batches)} 个批次")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 分批处理题目
        all_questions: List[Tuple[str, str]] = []
        for batch_idx, (batch_start, batch_end) in enumerate(batches):
            batch_num = batch_idx + 1
            print(f"处理题目批次 {batch_num}: 页码 {batch_start + 1}-{batch_end}")
            
            temp_question_pdf = os.path.join(temp_dir, f"q_batch_{batch_num}.pdf")
            split_pdf_by_pages(question_file, batch_start, batch_end - 1, temp_question_pdf)
            
            result = ask_ai(
                prompt="请将题目转换为 Markdown 格式，公式使用 LaTeX 语法。请保持原文的题号和结构。",
                files=[temp_question_pdf],
                system=SYSTEM_PROMPTS["question_to_latex"],
            )
            
            batch_questions = split_questions_by_number(result)
            all_questions = merge_questions(all_questions, batch_questions)
        
        # 分批处理答案
        all_answers: List[Tuple[str, str]] = []
        if answer_file is not None and answer_file:
            for batch_idx, (batch_start, batch_end) in enumerate(batches):
                batch_num = batch_idx + 1
                print(f"处理答案批次 {batch_num}: 页码 {batch_start + 1}-{batch_end}")
                
                temp_answer_pdf = os.path.join(temp_dir, f"a_batch_{batch_num}.pdf")
                split_pdf_by_pages(answer_file, batch_start, batch_end - 1, temp_answer_pdf)
                
                result = ask_ai(
                    prompt="请将答案转换为 Markdown 格式，公式使用 LaTeX 语法。请保持原文的题号和结构。不要包含评分标准。",
                    files=[temp_answer_pdf],
                    system=SYSTEM_PROMPTS["answer_to_latex"],
                )
                
                batch_answers = split_questions_by_number(result)
                all_answers = merge_questions(all_answers, batch_answers)
        
        # 写入文件
        output_files = []
        
        for q_num, content in all_questions:
            md_filename = f"{exam_name}-{q_num}.md"
            md_path = os.path.join(output_dir, md_filename)
            
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            output_files.append(md_path)
        
        if answer_file is not None and answer_file:
            for q_num, content in all_answers:
                md_filename = f"{exam_name}-{q_num}-ans.md"
                md_path = os.path.join(output_dir, md_filename)
                
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                output_files.append(md_path)
        
        elapsed_time = time.time() - start_time
        
        print(f"成功转化 {question_file}，用时 {elapsed_time:.2f} 秒，共 {len(output_files)} 个文件")
        
        return output_files
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    doc2latex(
        question_file="testdata/question_test.pdf",
        answer_file="",
        output_dir="output",
    )
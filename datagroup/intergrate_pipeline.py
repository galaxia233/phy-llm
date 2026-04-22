from api_client import ask_ai
from pathlib import Path
from system_prompts import SystemPrompts
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import threading

# 线程安全的文件写入
file_lock = threading.Lock()

def process_file(file_path, output_file):
    """处理单个文件"""
    print(f"Processing file: {file_path}")
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
                for line in lines:
                    line = line.strip()
                    if line:
                        try:
                            json.loads(line)
                            f.write(line + '\n')
                        except json.JSONDecodeError as e:
                            last_brace = line.rfind('}')
                            if last_brace != -1:
                                fixed_line = line[:last_brace + 1]
                                try:
                                    json.loads(fixed_line)
                                    f.write(fixed_line + '\n')
                                    print(f"  [{file_path.name}] 修复了一条截断的 JSON")
                                except:
                                    pass
            print(f"[{file_path.name}] 完成")
        return True
    except Exception as e:
        print(f"[{file_path.name}] 失败：{e}")
        return False


input_dir = Path(__file__).resolve().parent / "testdata"
output_dir = Path(__file__).resolve().parent / "json_output"

if input_dir.exists():
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "test.jsonl"

    # 收集所有要处理的文件
    files = list(input_dir.glob("*.md"))
    print(f"找到 {len(files)} 个文件，开始并行处理...")

    # 并行处理（最多 4 个并发）
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(process_file, f, output_file): f for f in files}
        for future in as_completed(futures):
            pass  # 已经在 process_file 中处理了输出

    print(f"\n所有文件处理完成，结果保存在 {output_file}")
else:
    raise FileNotFoundError(f"Input directory {input_dir} does not exist.")
import subprocess
from pathlib import Path

input_dir = Path(__file__).resolve().parent / "input"
output_dir = Path(__file__).resolve().parent / "output"

for pdf in sorted(input_dir.glob("*.pdf")):
    command = [
        "mineru",
        "-p", str(pdf),
        "-o", str(output_dir / pdf.stem)
    ]

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"转换成功：{pdf.name}")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"转换失败 {pdf.name}，错误信息：{e.stderr}")

import os
import magnus
secret = magnus.custody_file(str(output_dir))
with open(os.environ["MAGNUS_ACTION"], "w") as f:
    f.write(f"magnus receive {secret} --output output\n")

print(f"处理完成，secret={secret}")
print(f"请使用以下命令下载输出文件：magnus login + magnus receive secret")
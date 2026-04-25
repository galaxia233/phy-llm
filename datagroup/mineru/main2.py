import subprocess
from pathlib import Path

import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

input_dir = Path(__file__).resolve().parent / "input"
output_dir = Path(__file__).resolve().parent / "output"

command = [
     "mineru",
     "-p", str(input_dir),
     "-o", str(output_dir),
     "-m", "txt"
]

try:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    print("转换成功")
    print(result.stdout)
except subprocess.CalledProcessError as e:
    print(f"转换失败，错误信息：{e.stderr}")

import magnus
secret = magnus.custody_file(str(output_dir))
with open(os.environ["MAGNUS_ACTION"], "w") as f:
    f.write(f"magnus receive {secret} --output output\n")

print(f"处理完成，secret={secret}")
print(f"请使用以下命令下载输出文件：magnus login + magnus receive {secret}")
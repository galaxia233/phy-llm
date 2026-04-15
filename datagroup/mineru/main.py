from convert import main
from pathlib import Path

main()

#输出
import os
import magnus
secret = magnus.custody_file(os.path.join(Path(__file__).resolve().parent, "output"))
with open(os.environ["MAGNUS_ACTION"],"w") as f:
    f.write(f"magnus receive {secret} --output output\n")

print(f"处理完成，secret={secret}")
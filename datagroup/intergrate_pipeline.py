from api_client import ask_ai
from pathlib import Path


input_dir=None
output_dir=Path(__file__).resolve().parent / "output"

if input_dir:
    pass
else:
    input_dir = Path(__file__).resolve().parent / "input"
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory {input_dir} does not exist.")
    print(f"Using input directory: {input_dir}")
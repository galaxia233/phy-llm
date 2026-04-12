from pathlib import Path
import json
import re

from convert import split_question

if __name__ == "__main__":
    split_question(
        input_md_path=Path(__file__).resolve().parent / "output" / "question" / "1.md",
        output_dir=Path(__file__).resolve().parent / "output",
        category="test",
    )
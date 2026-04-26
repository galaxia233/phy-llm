import fitz # PyMuPDF
import os
from pathlib import Path

def split_pdf(input_path, chunk_size=200):
    doc = fitz.open(input_path)
    total = len(doc)
    base_name = os.path.basename(input_path).replace(".pdf", "")
    
    for i in range(0, total, chunk_size):
        start = i
        end = min(i + chunk_size - 1, total - 1)
        output_path = f"{base_name}_part_{start+1}_{end+1}.pdf"
        
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=start, to_page=end)
        new_doc.save(output_path)
        new_doc.close()
        print(f"已生成: {output_path}")

# 使用方法
for pdf in Path("./input").glob("*.pdf"):
    split_pdf(pdf, chunk_size=100)
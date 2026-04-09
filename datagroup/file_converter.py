"""
文件转换器模块

将 PDF 和 Word 文件转换为图片，以便 AI 模型处理
"""

import os
import tempfile
from pathlib import Path
from typing import List, Tuple

from config import PDF_DPI


def convert_pdf_to_images(path: str) -> List[Tuple[bytes, str]]:
    """
    将 PDF 文件转换为图片列表（每页一张图片）
    
    Args:
        path: PDF 文件路径
    
    Returns:
        [(image_bytes, page_name), ...] 列表
    
    Raises:
        ImportError: 未安装 PyMuPDF
        FileNotFoundError: PDF 文件不存在
        IOError: 转换失败
    """
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(path)
        images = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            # 渲染为 PNG 图片，zoom=PDF_DPI 提高清晰度
            mat = fitz.Matrix(PDF_DPI, PDF_DPI)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            images.append((img_bytes, f"{Path(path).stem}_p{page_num + 1}"))
        doc.close()
        return images
    except ImportError:
        raise ImportError("读取 PDF 需要安装 PyMuPDF 和 PyMuPDFb: pip install PyMuPDF PyMuPDFb")
    except FileNotFoundError:
        raise FileNotFoundError(f"PDF 文件不存在：{path}")
    except Exception as e:
        raise IOError(f"转换 PDF 文件失败：{path}, 错误：{e}")


def convert_word_to_images(path: str) -> List[Tuple[bytes, str]]:
    """
    将 Word 文件转换为图片列表（每页一张图片）
    
    支持两种方式：
    1. Windows: 使用 COM 接口调用 Word（需要安装 Microsoft Word）
    2. 跨平台：使用 docx2pdf（需要安装额外依赖）
    
    Args:
        path: Word 文件路径 (.docx 或 .doc)
    
    Returns:
        [(image_bytes, page_name), ...] 列表
    
    Raises:
        ImportError: 未安装必要的依赖
        IOError: 转换失败
    """
    try:
        # 方法 1：使用 comtypes 调用 Word COM（Windows only）
        import comtypes.client
        word = comtypes.client.CreateObject("Word.Application")
        word.Visible = False
        
        # 打开文档
        doc_path = os.path.abspath(path)
        doc = word.Documents.Open(doc_path)
        
        # 导出为 PDF 到临时文件
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # 保存为 PDF (17 = wdFormatPDF)
            doc.SaveAs2(tmp_path, FileFormat=17)
            doc.Close()
            word.Quit()
            
            # 然后用 PyMuPDF 转换 PDF 为图片
            return convert_pdf_to_images(tmp_path)
        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except (ImportError, OSError, AttributeError):
        # 方法 2：如果 COM 不可用，尝试使用 docx2pdf + PyMuPDF
        try:
            from docx2pdf import convert
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp_path = tmp.name
            try:
                convert(path, tmp_path)
                return convert_pdf_to_images(tmp_path)
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        except ImportError:
            raise ImportError(
                "读取 Word 文件需要以下依赖之一：\n"
                "  Windows: 需要安装 Microsoft Word（使用 COM 接口）\n"
                "  跨平台：pip install docx2pdf PyMuPDF PyMuPDFb"
            )
        except Exception as e:
            raise IOError(f"转换 Word 文件失败：{path}, 错误：{e}")
    except Exception as e:
        raise IOError(f"转换 Word 文件失败：{path}, 错误：{e}")


# 图片格式的 media type 映射
IMAGE_MEDIA_MAP = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


def is_supported_image(suffix: str) -> bool:
    """判断是否是支持的图片格式"""
    return suffix.lower() in IMAGE_MEDIA_MAP


def get_media_type(suffix: str) -> str:
    """获取文件后缀对应的 media type"""
    return IMAGE_MEDIA_MAP.get(suffix.lower(), "image/jpeg")
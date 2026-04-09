"""
测试脚本

演示各模块的使用方法和测试用例
"""

# ==========================================
# 导入模块
# ==========================================
from database.api import DB, open_db, quick_query

from pathlib import Path

from system_prompts import SystemPrompts, get_system, list_prompts
from api_client import ask_ai
from answer_verifier import verify_answer, verify_answer_numeric, verify_answer_formula
script_dir = Path(__file__).parent

# ==========================================
# API 调用测试
# ==========================================

def test_ask_ai_basic():
    """测试基本的 ask_ai 调用"""
    # 单张图片
    ans = ask_ai(
        "请描述一下这张图片的内容",
        files=[script_dir / "testdata" / "test.png"],
        max_retries=0
    )
    print("单张图片测试:", ans)


def test_ask_ai_multiple_files():
    """测试多文件调用"""
    ans = ask_ai(
        "请比较 [文件 1] 和 [文件 2] 的不同",
        files=[script_dir / "testdata" / "test.png", script_dir / "testdata" / "test copy.png"],
        max_retries=0
    )
    print("多文件测试:", ans)


def test_ask_ai_with_system():
    """测试带 system prompt 的调用"""
    # 方法 1：使用枚举
    ans = ask_ai(
        "请比较这两个答案是否等价：答案 1: 9.8 m/s², 答案 2: 980 cm/s²",
        system=SystemPrompts.ANSWER_COMPARATOR,
        max_retries=0
    )
    print("使用枚举方式:", ans)
    
    # 方法 2：使用字符串键
    ans = ask_ai(
        "请比较这两个公式：答案 1: 0.5*m*v^2, 答案 2: \\frac{1}{2}mv^2",
        system=get_system("answer_comparator"),
        max_retries=0
    )
    print("使用字符串方式:", ans)


def test_ask_ai_mixed_files():
    """测试混合文件类型（图片 + PDF + Word）"""
    ans = ask_ai(
        "[文件 1][文件 2][文件 3] 这三个文件分别是图片、PDF 和 Word，你能看到吗",
        files=[
            str(script_dir / "testdata" / "test.png"),
            str(script_dir / "testdata" / "document.pdf"),
            str(script_dir / "testdata" / "report.docx")
        ],
        system=get_system("data_analyst"),
        max_retries=0
    )
    print("混合文件测试:", ans)


# ==========================================
# 答案验证测试
# ==========================================

def test_verify_numeric():
    """测试数值答案验证"""
    ans1 = {"value": "9", "unit": ""}
    ans2 = {"value": "9.0", "unit": ""}
    result = verify_answer(ans1, ans2)
    print(f"数值验证 {ans1} vs {ans2}: {result}")


def test_verify_formula():
    """测试公式答案验证"""
    ans1 = {"value": "0.5*m*v*v", "unit": ""}
    ans2 = {"value": "\\frac{1}{2}mv^2", "unit": ""}
    result = verify_answer(ans1, ans2)
    print(f"公式验证 {ans1} vs {ans2}: {result}")


def test_verify_with_unit():
    """测试带单位的答案验证"""
    ans1 = {"value": "10", "unit": "J"}
    ans2 = {"value": "10", "unit": "焦耳"}
    result = verify_answer(ans1, ans2)
    print(f"带单位验证 {ans1} vs {ans2}: {result}")


# ==========================================
# 主函数
# ==========================================

if __name__ == "__main__":
    print("=" * 50)
    print("可用 system prompts:", list_prompts())
    print("=" * 50)
    
    # 运行测试（取消注释以运行）
    
    # 基础测试
    #test_ask_ai_basic()
    
    # 多文件测试
    # test_ask_ai_multiple_files()
    
    # system prompt 测试
    # test_ask_ai_with_system()
    
    # 混合文件测试
    # test_ask_ai_mixed_files()
    
    # 验证测试
    # test_verify_numeric()
    # test_verify_formula()
    # test_verify_with_unit()
    
    #test_ask_ai_mixed_files()
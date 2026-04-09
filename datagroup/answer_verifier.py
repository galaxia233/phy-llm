"""
答案验证模块

验证 AI 回答的答案是否正确，支持数值、公式等多种验证方式
"""

from typing import Dict, Optional

from sympy.parsing.latex import parse_latex
from sympy import simplify, N

from config import DEFAULT_TOLERANCE
from api_client import ask_ai


def verify_answer_numeric(
    student_latex: str,
    reference_latex: str,
    tolerance: float = DEFAULT_TOLERANCE
) -> Optional[bool]:
    """
    验证数值答案是否在误差范围内
    
    Args:
        student_latex: 学生答案的 LaTeX 表达式
        reference_latex: 参考答案的 LaTeX 表达式
        tolerance: 相对误差容忍度
    
    Returns:
        bool: 是否正确，None 表示需要人工复核
    """
    try:
        student = N(parse_latex(student_latex))
        reference = N(parse_latex(reference_latex))
        return abs(student - reference) < tolerance * abs(reference)
    except Exception as e:
        print(f"解析失败：{e}")
        return None


def verify_answer_formula(
    student_latex: str,
    reference_latex: str
) -> Optional[bool]:
    """
    验证两个公式是否等价
    
    Args:
        student_latex: 学生答案的 LaTeX 表达式
        reference_latex: 参考答案的 LaTeX 表达式
    
    Returns:
        bool: 是否等价，None 表示需要人工复核
    """
    try:
        student = parse_latex(student_latex)
        reference = parse_latex(reference_latex)
        # simplify 如果结果为 0 说明两式等价
        return simplify(student - reference) == 0
    except Exception as e:
        print(f"解析失败：{e}")
        return None


def verify_answer(
    ai_answer: Dict,
    ref_answer: Dict,
    tolerance: float = DEFAULT_TOLERANCE,
) -> Dict:
    """
    验证 AI 回答的答案是否正确
    
    Args:
        ai_answer: AI 答案 {"value": "9", "unit": "J"} 或 {"value": "1/2*m*v^2", "unit": ""}
        ref_answer: 参考答案 {"value": "9", "unit": "J"} 或 {"value": "1/2*m*v^2", "unit": ""}
        tolerance: 数值验证的误差容忍度
    
    Returns:
        {
            "is_correct": bool 或 None（需要人工复核）,
            "method": "numeric" | "sympy" | "ai" | "need_review"
        }
    """
    ai_value = ai_answer.get("value", "")
    ai_unit = ai_answer.get("unit", "")
    ref_value = ref_answer.get("value", "")
    ref_unit = ref_answer.get("unit", "")

    # 判断是否是纯数值（能转成 float）
    def is_numeric(s: str) -> bool:
        try:
            float(s)
            return True
        except:
            return False

    # 分支 1：纯数值，无单位 → 直接数值比对
    if is_numeric(ai_value) and is_numeric(ref_value) and not ai_unit and not ref_unit:
        return {
            "is_correct": abs(float(ai_value) - float(ref_value)) < tolerance,
            "method": "numeric"
        }

    # 分支 2：数值 + 有单位 → LLM 验证
    if is_numeric(ai_value) and is_numeric(ref_value) and (ai_unit or ref_unit):
        ans = ask_ai(
            f"{ai_value}{ai_unit}和{ref_value}{ref_unit}是否等价？请只回答是或否。",
            system="你是一个物理助教，负责判断两个带单位的数值是否等价。"
        )
        is_correct = "是" in ans.strip()
        return {
            "is_correct": is_correct,
            "method": "ai"
        }

    # 分支 3：表达式 → sympy 验证
    try:
        ai_expr = parse_latex(ai_value)
        ref_expr = parse_latex(ref_value)
        return {
            "is_correct": simplify(ai_expr - ref_expr) == 0,
            "method": "sympy"
        }
    except:
        pass

    return {
        "is_correct": None,
        "method": "need_review"
    }
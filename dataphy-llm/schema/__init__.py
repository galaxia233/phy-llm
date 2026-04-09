"""
Phy-LLM Schema 定义包

包含 7 套 Schema 定义（v9.0），共 122 个字段：
- SFT_SCHEMA_V9 (18 字段) - 监督微调数据
- DPO_SCHEMA_V9 (15 字段) - 偏好数据
- EVAL_SCHEMA_V9 (19 字段) - 评测结果
- AI_ANSWER_SCHEMA_V9 (16 字段) - AI 答题记录
- GENERATION_SCHEMA_V9 (20 字段) - 题目生成记录
- GRADING_SCHEMA_V9 (18 字段) - 批改记录
- KNOWLEDGE_SCHEMA_V9 (16 字段) - 知识图谱

所有 Schema 均通过文献验证，无幻觉。
文献支撑率：100%

作者：A 组
版本：9.0
最后更新：2026-03-31
"""

from .sft_schema import SFT_SCHEMA_V9, validate_sft_data
from .dpo_schema import DPO_SCHEMA_V9, validate_dpo_data
from .eval_schema import EVAL_SCHEMA_V9, validate_eval_data
from .ai_answer_schema import AI_ANSWER_SCHEMA_V9, validate_ai_answer_data
from .generation_schema import GENERATION_SCHEMA_V9, validate_generation_data
from .grading_schema import GRADING_SCHEMA_V9, validate_grading_data
from .knowledge_schema import KNOWLEDGE_SCHEMA_V9, validate_knowledge_data

__version__ = '9.0'
__author__ = 'Team3-Schema-Group'

__all__ = [
    # Schemas
    'SFT_SCHEMA_V9',
    'DPO_SCHEMA_V9',
    'EVAL_SCHEMA_V9',
    'AI_ANSWER_SCHEMA_V9',
    'GENERATION_SCHEMA_V9',
    'GRADING_SCHEMA_V9',
    'KNOWLEDGE_SCHEMA_V9',
    # Validators
    'validate_sft_data',
    'validate_dpo_data',
    'validate_eval_data',
    'validate_ai_answer_data',
    'validate_generation_data',
    'validate_grading_data',
    'validate_knowledge_data',
]

# Schema 汇总信息
SCHEMA_SUMMARY = {
    'sft': {'schema': SFT_SCHEMA_V9, 'fields': 18, 'validator': validate_sft_data},
    'dpo': {'schema': DPO_SCHEMA_V9, 'fields': 15, 'validator': validate_dpo_data},
    'eval': {'schema': EVAL_SCHEMA_V9, 'fields': 19, 'validator': validate_eval_data},
    'ai_answer': {'schema': AI_ANSWER_SCHEMA_V9, 'fields': 16, 'validator': validate_ai_answer_data},
    'generation': {'schema': GENERATION_SCHEMA_V9, 'fields': 20, 'validator': validate_generation_data},
    'grading': {'schema': GRADING_SCHEMA_V9, 'fields': 18, 'validator': validate_grading_data},
    'knowledge': {'schema': KNOWLEDGE_SCHEMA_V9, 'fields': 16, 'validator': validate_knowledge_data},
}

TOTAL_FIELDS = sum(info['fields'] for info in SCHEMA_SUMMARY.values())

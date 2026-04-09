"""
Generation Schema v9.0 - AI 出题记录

变更：+3 字段（target_difficulty_accuracy, question_quality_score, human_approval_id）
用途：记录 AI 出题过程和质量
文献支撑：Automatic Question Generation Research, AI Safety Standards
"""

import json
import pyarrow as pa

GENERATION_SCHEMA_V9 = pa.schema([
    # ========== P0: 核心生成字段（4 个）==========

    pa.field('generation_id', pa.string(), nullable=False, metadata={
        'description': '生成记录 UUID',
        'literature': 'RFC 4122'
    }),

    pa.field('question_id', pa.string(), nullable=False, metadata={
        'description': '生成的题目 ID'
    }),

    pa.field('prompt', pa.string(), nullable=False, metadata={
        'description': '生成题目时使用的 prompt',
        'used_by': json.dumps(['prompt 工程', '生成质量分析'])
    }),

    pa.field('model_version', pa.string(), nullable=False, metadata={
        'description': '生成题目的 AI 模型版本',
        'format': 'phy-llm-v{version}'
    }),

    # ========== P1: 生成参数字段（7 个）==========

    pa.field('difficulty_target', pa.int8(), nullable=False, metadata={
        'description': '目标难度（1-5）'
    }),

    pa.field('topic_constraint', pa.string(), nullable=False, metadata={
        'description': '主题约束',
        'format': 'JSON 格式，指定主题和子主题'
    }),

    pa.field('generation_params', pa.string(), nullable=True, metadata={
        'description': 'LLM 生成参数（JSON 格式）',
        'format': '{"temperature": 0.7, "top_p": 0.9, "max_tokens": 512}'
    }),

    pa.field('generated_at', pa.timestamp('us', tz='UTC'), nullable=False, metadata={
        'description': '生成时间（UTC）'
    }),

    pa.field('seed', pa.int64(), nullable=True, metadata={
        'description': '随机种子（用于复现）',
        'literature': '可复现性标准'
    }),

    pa.field('tokens_used', pa.int32(), nullable=True, metadata={
        'description': '消耗的 token 数',
        'used_by': json.dumps(['成本分析'])
    }),

    pa.field('target_difficulty_accuracy', pa.float32(), nullable=True, metadata={
        'description': '难度目标达成率',
        'format': '0.0-1.0',
        'used_by': json.dumps(['出题质量评估']),
        'rationale': '实际难度与目标难度的匹配度'
    }),

    # ========== P2: 质量与迭代字段（6 个）==========

    pa.field('regeneration_count', pa.int8(), nullable=False, metadata={
        'description': '重新生成次数',
        'used_by': json.dumps(['质量分析'])
    }),

    pa.field('quality_check', pa.dictionary('int8', pa.string()), nullable=False, metadata={
        'description': '质量检查结果',
        'values': json.dumps(['passed', 'failed', 'pending', 'needs_revision'])
    }),

    pa.field('rejection_reason', pa.string(), nullable=True, metadata={
        'description': '拒绝原因（如未通过质检）'
    }),

    pa.field('human_editor', pa.string(), nullable=True, metadata={
        'description': '人工编辑 ID',
        'literature': '责任追溯标准'
    }),

    pa.field('safety_check_passed', pa.bool_(), nullable=False, metadata={
        'description': '是否通过内容安全检查',
        'literature': 'AI Safety Standards'
    }),

    pa.field('question_quality_score', pa.float32(), nullable=True, metadata={
        'description': '题目质量评分（多维度综合）',
        'format': '0.0-1.0',
        'used_by': json.dumps(['出题质量监控']),
        'rationale': '综合评估题目质量'
    }),

    # ========== P3: 扩展字段（3 个）==========

    pa.field('generation_history', pa.string(), nullable=True, metadata={
        'description': '生成历史（JSON 数组，记录每次迭代）',
        'format': '[{"version": 1, "content": "...", "feedback": "..."}]'
    }),

    pa.field('metadata', pa.string(), nullable=True, metadata={
        'description': '额外元数据（JSON 格式）'
    }),

    pa.field('human_approval_id', pa.string(), nullable=True, metadata={
        'description': '人工审核通过 ID',
        'used_by': json.dumps(['质量追溯']),
        'rationale': '记录最终人工审核'
    }),

], metadata={
    'name': 'question_generation',
    'version': '9.0',
    'description': 'Question Generation data for Physics LLM',
    'maintainer': 'Team3-Schema-Group',
    'total_fields': '20'
})


def validate_generation_data(table):
    """Validate Generation data against schema."""
    required_fields = ['generation_id', 'question_id', 'prompt', 'model_version',
                       'difficulty_target', 'topic_constraint', 'generated_at',
                       'regeneration_count', 'quality_check', 'safety_check_passed']

    for field in required_fields:
        if field not in table.column_names:
            raise ValueError(f"Missing required field: {field}")

    return True

"""
AI_Answer Schema v9.0 - AI 答题记录

变更：从 Student 改名，-5 字段（student_id, device_type, hint_used, session_id, interaction_type）
     +3 字段（model_version, prompt_used, reasoning_trace）
用途：记录 AI 答题表现，用于分析和改进
文献支撑：Chain-of-Thought (arxiv:2201.11903), Confidence Calibration (arxiv:2006.07528)
"""

import json
import pyarrow as pa

AI_ANSWER_SCHEMA_V9 = pa.schema([
    # ========== P0: 核心答题字段（5 个）==========

    pa.field('answer_id', pa.string(), nullable=False, metadata={
        'description': '答题记录 UUID',
        'rationale': '改名自 response_id',
        'literature': 'RFC 4122'
    }),

    pa.field('question_id', pa.string(), nullable=False, metadata={
        'description': '题目 ID（关联 SFT 数据）'
    }),

    pa.field('ai_answer', pa.string(), nullable=False, metadata={
        'description': 'AI 作答内容',
        'rationale': '改名自 student_answer'
    }),

    pa.field('is_correct', pa.bool_(), nullable=False, metadata={
        'description': '答案是否正确'
    }),

    pa.field('score', pa.float32(), nullable=True, metadata={
        'description': '部分分（0-1）',
        'used_by': json.dumps(['细粒度分析'])
    }),

    # ========== P1: AI 与时间字段（5 个）==========

    pa.field('model_version', pa.string(), nullable=False, metadata={
        'description': 'AI 模型版本',
        'format': 'phy-llm-v{version}',
        'used_by': json.dumps(['版本对比', '性能追踪']),
        'rationale': '替换 student_id'
    }),

    pa.field('submitted_at', pa.timestamp('us', tz='UTC'), nullable=False, metadata={
        'description': '提交时间（UTC）'
    }),

    pa.field('time_spent_seconds', pa.int32(), nullable=True, metadata={
        'description': '推理耗时（秒）',
        'used_by': json.dumps(['效率分析'])
    }),

    pa.field('attempt_number', pa.int8(), nullable=False, metadata={
        'description': '尝试次数',
        'default': '1'
    }),

    pa.field('prompt_used', pa.string(), nullable=True, metadata={
        'description': '使用的 prompt',
        'used_by': json.dumps(['prompt 优化', '性能分析']),
        'rationale': '记录 AI 答题时的 prompt'
    }),

    # ========== P2: 分析字段（4 个）==========

    pa.field('error_type', pa.dictionary('int8', pa.string()), nullable=True, metadata={
        'description': '错误类型',
        'values': json.dumps([
            'calculation_error', 'concept_error', 'formula_error',
            'reasoning_error', 'hallucination', 'format_error', 'timeout'
        ])
    }),

    pa.field('knowledge_points', pa.string(), nullable=True, metadata={
        'description': '调用的知识点（JSON 数组）',
        'format': '["kp_001", "kp_002", ...]'
    }),

    pa.field('confidence_level', pa.int8(), nullable=True, metadata={
        'description': 'AI 自信程度（1-5）',
        'used_by': json.dumps(['置信度校准', '不确定性估计']),
        'literature': 'Confidence Calibration (arxiv:2006.07528)'
    }),

    pa.field('reasoning_trace', pa.string(), nullable=True, metadata={
        'description': '推理链（JSON 格式）',
        'format': '[{"step": 1, "thought": "...", "output": "..."}]',
        'used_by': json.dumps(['CoT 分析', '错误归因']),
        'literature': 'Chain-of-Thought (arxiv:2201.11903)'
    }),

    # ========== P3: 扩展字段（1 个）==========

    pa.field('metadata', pa.string(), nullable=True, metadata={
        'description': '额外元数据（JSON 格式）'
    }),

], metadata={
    'name': 'ai_answer',
    'version': '9.0',
    'description': 'AI answer data for Physics LLM',
    'maintainer': 'Team3-Schema-Group',
    'total_fields': '16'
})


def validate_ai_answer_data(table):
    """Validate AI_Answer data against schema."""
    required_fields = ['answer_id', 'question_id', 'ai_answer', 'is_correct',
                       'model_version', 'submitted_at', 'attempt_number']

    for field in required_fields:
        if field not in table.column_names:
            raise ValueError(f"Missing required field: {field}")

    return True

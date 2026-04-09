"""
Grading Schema v9.0 - AI 批改记录

变更：+3 字段（rubric_adherence_score, feedback_quality_score, human_agreement_rate, reviewed_by）
用途：记录 AI 评判过程和质量
文献支撑：LLM-as-Judge (arxiv:2306.05685), 形成性评价标准
"""

import json
import pyarrow as pa

GRADING_SCHEMA_V9 = pa.schema([
    # ========== P0: 核心批改字段（4 个）==========

    pa.field('grading_id', pa.string(), nullable=False, metadata={
        'description': '批改记录 UUID',
        'literature': 'RFC 4122'
    }),

    pa.field('answer_id', pa.string(), nullable=False, metadata={
        'description': '被批改的答案 ID（关联 AI_Answer）'
    }),

    pa.field('grader_type', pa.dictionary('int8', pa.string()), nullable=False, metadata={
        'description': '批改者类型',
        'values': json.dumps(['ai_grader', 'human_grader', 'hybrid'])
    }),

    pa.field('grader_id', pa.string(), nullable=False, metadata={
        'description': '批改者 ID',
        'used_by': json.dumps(['责任追溯'])
    }),

    # ========== P1: 评分细节字段（6 个）==========

    pa.field('score', pa.float32(), nullable=False, metadata={
        'description': '评分',
        'used_by': json.dumps(['成绩统计', '表现分析'])
    }),

    pa.field('max_score', pa.float32(), nullable=False, metadata={
        'description': '满分'
    }),

    pa.field('rubric', pa.string(), nullable=True, metadata={
        'description': '评分标准（JSON 格式）',
        'format': '{"criteria": [...], "weights": [...]}'
    }),

    pa.field('graded_at', pa.timestamp('us', tz='UTC'), nullable=False, metadata={
        'description': '批改时间（UTC）'
    }),

    pa.field('grading_time_seconds', pa.int32(), nullable=True, metadata={
        'description': '批改耗时（秒）',
        'used_by': json.dumps(['效率分析'])
    }),

    pa.field('rubric_adherence_score', pa.float32(), nullable=True, metadata={
        'description': '评分标准遵循度',
        'format': '0.0-1.0',
        'used_by': json.dumps(['批改质量监控']),
        'rationale': '评估 AI 是否严格按照评分标准'
    }),

    # ========== P2: 反馈字段（5 个）==========

    pa.field('feedback', pa.string(), nullable=True, metadata={
        'description': '批改反馈',
        'used_by': json.dumps(['形成性评价', '学习改进'])
    }),

    pa.field('error_categories', pa.list_(pa.string()), nullable=True, metadata={
        'description': '错误分类列表',
        'values': json.dumps(['calculation', 'concept', 'formula', 'reasoning', 'format'])
    }),

    pa.field('suggestions', pa.string(), nullable=True, metadata={
        'description': '改进建议（JSON 格式）',
        'format': '[{"area": "...", "suggestion": "..."}]'
    }),

    pa.field('feedback_quality_score', pa.float32(), nullable=True, metadata={
        'description': '反馈质量评分',
        'format': '0.0-1.0',
        'used_by': json.dumps(['反馈优化']),
        'rationale': '评估反馈的建设性和准确性'
    }),

    pa.field('human_agreement_rate', pa.float32(), nullable=True, metadata={
        'description': '与人工批改一致性',
        'format': '0.0-1.0',
        'used_by': json.dumps(['AI 批改质量评估']),
        'literature': 'LLM-as-Judge (arxiv:2306.05685)'
    }),

    # ========== P3: 扩展字段（3 个）==========

    pa.field('consistency_check', pa.string(), nullable=True, metadata={
        'description': '一致性检查结果（JSON 格式）',
        'format': '{"agreement_with_other_ais": 0.8, "variance": 0.1}'
    }),

    pa.field('requires_review', pa.bool_(), nullable=True, metadata={
        'description': '是否需要复核',
        'used_by': json.dumps(['质量管控'])
    }),

    pa.field('reviewed_by', pa.string(), nullable=True, metadata={
        'description': '复核者 ID',
        'used_by': json.dumps(['质量追溯']),
        'rationale': '记录复核责任'
    }),

], metadata={
    'name': 'grading',
    'version': '9.0',
    'description': 'Grading data for Physics LLM',
    'maintainer': 'Team3-Schema-Group',
    'total_fields': '18'
})


def validate_grading_data(table):
    """Validate Grading data against schema."""
    required_fields = ['grading_id', 'answer_id', 'grader_type', 'grader_id',
                       'score', 'max_score', 'graded_at']

    for field in required_fields:
        if field not in table.column_names:
            raise ValueError(f"Missing required field: {field}")

    return True

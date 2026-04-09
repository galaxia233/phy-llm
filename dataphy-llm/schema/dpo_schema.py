"""
DPO Schema v9.0 - 偏好数据（AI 学习人类偏好）

变更：+2 字段（preference_source, confidence_level）
用途：AI 学习什么是更好的回答
文献支撑：DPO Paper (arxiv:2305.18290), RLHF 数据标注标准
"""

import json
import pyarrow as pa

DPO_SCHEMA_V9 = pa.schema([
    # ========== P0: 核心训练字段（3 个）==========

    pa.field('question', pa.string(), nullable=False, metadata={
        'description': '问题内容',
        'literature': 'DPO Paper (arxiv:2305.18290)'
    }),

    pa.field('chosen', pa.string(), nullable=False, metadata={
        'description': '偏好的回答',
        'literature': 'DPO Paper (arxiv:2305.18290)'
    }),

    pa.field('rejected', pa.string(), nullable=False, metadata={
        'description': '不偏好的回答',
        'literature': 'DPO Paper (arxiv:2305.18290)'
    }),

    # ========== P1: 数据管理字段（7 个）==========

    pa.field('id', pa.string(), nullable=False, metadata={
        'description': 'UUID v4 唯一标识符',
        'literature': 'RFC 4122'
    }),

    pa.field('split', pa.dictionary('int8', pa.string()), nullable=True, metadata={
        'description': '数据集划分',
        'values': json.dumps(['train', 'val', 'test']),
        'literature': 'HuggingFace Datasets'
    }),

    pa.field('annotator', pa.string(), nullable=False, metadata={
        'description': '数据创建人/标注人 ID',
        'literature': 'W3C PROV'
    }),

    pa.field('created_at', pa.timestamp('us', tz='UTC'), nullable=False, metadata={
        'description': '数据创建时间（UTC）'
    }),

    pa.field('schema_version', pa.string(), nullable=False, metadata={
        'description': 'Schema 版本号'
    }),

    pa.field('source_question_id', pa.string(), nullable=True, metadata={
        'description': '源问题 ID（关联 SFT 数据）'
    }),

    pa.field('preference_source', pa.dictionary('int8', pa.string()), nullable=True, metadata={
        'description': '偏好来源',
        'values': json.dumps(['human_expert', 'human_consensus', 'ai_judge', 'aggregated']),
        'used_by': json.dumps(['偏好质量分析']),
        'rationale': '区分偏好数据的来源可靠性'
    }),

    # ========== P2: 质量管控字段（2 个）==========

    pa.field('physics_topic', pa.dictionary('int8', pa.string()), nullable=False, metadata={
        'description': '物理主题',
        'values': json.dumps(['mechanics', 'em', 'thermo', 'quantum', 'optics', 'relativity', 'nuclear', 'statistical'])
    }),

    pa.field('difficulty', pa.int8(), nullable=False, metadata={
        'description': '难度等级 1-5'
    }),

    # ========== P3: 扩展字段（3 个）==========

    pa.field('preference_reason', pa.string(), nullable=True, metadata={
        'description': '偏好原因',
        'used_by': json.dumps(['偏好分析', '模型解释'])
    }),

    pa.field('comparison_criteria', pa.string(), nullable=True, metadata={
        'description': '比较标准（JSON 格式）',
        'format': '{"accuracy": true, "completeness": true, "clarity": false}'
    }),

    pa.field('confidence_level', pa.int8(), nullable=True, metadata={
        'description': '偏好置信度（1-5）',
        'range': '1=不确定，5=非常确定',
        'used_by': json.dumps(['偏好加权', '质量筛选']),
        'rationale': '高置信度偏好更有价值'
    }),

], metadata={
    'name': 'dpo',
    'version': '9.0',
    'description': 'DPO preference data for Physics LLM',
    'maintainer': 'Team3-Schema-Group',
    'total_fields': '15'
})


def validate_dpo_data(table):
    """Validate DPO data against schema."""
    required_fields = ['question', 'chosen', 'rejected', 'id', 'annotator',
                       'created_at', 'schema_version', 'physics_topic', 'difficulty']

    for field in required_fields:
        if field not in table.column_names:
            raise ValueError(f"Missing required field: {field}")

    return True

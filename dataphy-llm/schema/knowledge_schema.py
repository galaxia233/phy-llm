"""
Knowledge Schema v9.0 - 知识图谱

变更：+3 字段（typical_ai_errors, question_generation_templates, reasoning_patterns）
用途：AI 理解物理知识结构
文献支撑：W3C Knowledge Graph Standards, Bloom's Taxonomy, Physics Education Research
"""

import json
import pyarrow as pa

KNOWLEDGE_SCHEMA_V9 = pa.schema([
    # ========== P0: 核心知识字段（4 个）==========

    pa.field('knowledge_point_id', pa.string(), nullable=False, metadata={
        'description': '知识点唯一标识符',
        'format': 'kp_{topic}_{number}'
    }),

    pa.field('name', pa.string(), nullable=False, metadata={
        'description': '知识点名称',
        'used_by': json.dumps(['知识图谱构建', '题目关联'])
    }),

    pa.field('description', pa.string(), nullable=True, metadata={
        'description': '知识点描述'
    }),

    pa.field('physics_topic', pa.dictionary('int8', pa.string()), nullable=False, metadata={
        'description': '所属物理主题',
        'values': json.dumps(['mechanics', 'em', 'thermo', 'quantum', 'optics', 'relativity', 'nuclear', 'statistical'])
    }),

    # ========== P1: 关联字段（6 个）==========

    pa.field('prerequisite_ids', pa.list_(pa.string()), nullable=True, metadata={
        'description': '前置知识点 ID 列表',
        'used_by': json.dumps(['学习路径规划', '知识图谱遍历'])
    }),

    pa.field('question_ids', pa.list_(pa.string()), nullable=True, metadata={
        'description': '关联题目 ID 列表',
        'used_by': json.dumps(['题目检索', '知识点练习'])
    }),

    pa.field('difficulty_level', pa.int8(), nullable=False, metadata={
        'description': '难度等级（1-5）',
        'used_by': json.dumps(['难度控制', '学习进阶'])
    }),

    pa.field('related_kp_ids', pa.list_(pa.string()), nullable=True, metadata={
        'description': '相关知识 ID 列表',
        'used_by': json.dumps(['知识图谱遍历', '关联推荐'])
    }),

    pa.field('learning_objectives', pa.string(), nullable=True, metadata={
        'description': '学习目标（JSON 格式，基于 Bloom 分类学）',
        'format': '[{"level": "remember/understand/apply/analyze/evaluate/create", "objective": "..."}]',
        'literature': "Bloom's Taxonomy"
    }),

    pa.field('typical_ai_errors', pa.string(), nullable=True, metadata={
        'description': 'AI 在该知识点常见错误（JSON）',
        'format': '[{"error_type": "...", "frequency": 0.0, "example": "..."}]',
        'used_by': json.dumps(['针对性训练', '错误预防']),
        'rationale': '记录 AI 在特定知识点的错误模式'
    }),

    # ========== P2: 统计字段（3 个）==========

    pa.field('mastery_threshold', pa.float32(), nullable=True, metadata={
        'description': '掌握度阈值（0-1）',
        'used_by': json.dumps(['掌握度判断'])
    }),

    pa.field('common_misconceptions', pa.string(), nullable=True, metadata={
        'description': '常见误解（JSON 格式）',
        'format': '[{"misconception": "...", "correction": "..."}]',
        'literature': 'Physics Education Research'
    }),

    pa.field('question_generation_templates', pa.string(), nullable=True, metadata={
        'description': '该知识点的出题模板（JSON）',
        'format': '[{"template": "...", "difficulty": 1-5, "example": "..."}]',
        'used_by': json.dumps(['AI 出题', '题目生成']),
        'rationale': '支持 AI 学习如何出该知识点的题目'
    }),

    # ========== P3: 扩展字段（3 个）==========

    pa.field('estimated_study_time_minutes', pa.int32(), nullable=True, metadata={
        'description': '预估学习时间（分钟）',
        'used_by': json.dumps(['学习规划'])
    }),

    pa.field('metadata', pa.string(), nullable=True, metadata={
        'description': '额外元数据（JSON 格式）'
    }),

    pa.field('reasoning_patterns', pa.string(), nullable=True, metadata={
        'description': '该知识点的推理模式（JSON）',
        'format': '[{"pattern": "...", "steps": [...], "example": "..."}]',
        'used_by': json.dumps(['AI 推理训练', 'CoT 学习']),
        'rationale': 'AI 学习该知识点的标准推理方式'
    }),

], metadata={
    'name': 'knowledge_graph',
    'version': '9.0',
    'description': 'Knowledge Graph for Physics LLM',
    'maintainer': 'Team3-Schema-Group',
    'total_fields': '16'
})


def validate_knowledge_data(table):
    """Validate Knowledge data against schema."""
    required_fields = ['knowledge_point_id', 'name', 'physics_topic', 'difficulty_level']

    for field in required_fields:
        if field not in table.column_names:
            raise ValueError(f"Missing required field: {field}")

    return True

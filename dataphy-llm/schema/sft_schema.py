"""
SFT Schema v9.0 - 监督微调数据（AI 学习的标准答案）

变更：+2 字段（ai_generated, gold_standard）
用途：AI 学习什么是高质量的题目 - 答案对
文献支撑：MMLU (arxiv:2009.03300), SFT 训练最佳实践
"""

import json
import pyarrow as pa

SFT_SCHEMA_V9 = pa.schema([
    # ========== P0: 核心训练字段（3 个）==========

    pa.field('question', pa.string(), nullable=False, metadata={
        'description': '题目内容，支持 LaTeX 公式',
        'latex_format': '行内公式用 $...$，独立公式用 $$...$$',
        'used_by': json.dumps(['训练脚本']),
        'literature': 'MMLU (arxiv:2009.03300)'
    }),

    pa.field('solution', pa.string(), nullable=False, metadata={
        'description': '完整解题过程，支持 LaTeX 公式',
        'used_by': json.dumps(['训练脚本']),
        'literature': 'SFT 训练最佳实践'
    }),

    pa.field('answer', pa.string(), nullable=False, metadata={
        'description': '最终答案（标准化格式）',
        'used_by': json.dumps(['训练脚本', '评测脚本']),
        'literature': 'MMLU (arxiv:2009.03300)'
    }),

    # ========== P1: 数据管理字段（8 个）==========

    pa.field('id', pa.string(), nullable=False, metadata={
        'description': 'UUID v4 唯一标识符',
        'literature': 'RFC 4122'
    }),

    pa.field('split', pa.dictionary('int8', pa.string()), nullable=True, metadata={
        'description': '数据集划分',
        'values': json.dumps(['train', 'val', 'test']),
        'literature': 'HuggingFace Datasets'
    }),

    pa.field('source', pa.dictionary('int8', pa.string()), nullable=False, metadata={
        'description': '数据来源类型',
        'values': json.dumps(['textbook', 'arxiv', 'competition', 'synthetic', 'manual']),
        'literature': '数据溯源最佳实践'
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

    pa.field('language', pa.dictionary('int8', pa.string()), nullable=True, metadata={
        'description': '题目语言',
        'values': json.dumps(['zh', 'en', 'zh_en_bilingual']),
        'default': 'zh'
    }),

    pa.field('ai_generated', pa.bool_(), nullable=False, metadata={
        'description': '是否为 AI 生成',
        'default': 'False',
        'used_by': json.dumps(['数据筛选', '质量分析']),
        'rationale': '区分 AI 生成和人工标注数据'
    }),

    pa.field('gold_standard', pa.bool_(), nullable=False, metadata={
        'description': '是否为金标准答案',
        'default': 'False',
        'used_by': json.dumps(['训练权重', '评测基准']),
        'rationale': '标记高质量标准答案'
    }),

    # ========== P2: 质量管控字段（4 个）==========

    pa.field('physics_topic', pa.dictionary('int8', pa.string()), nullable=False, metadata={
        'description': '物理主题',
        'values': json.dumps(['mechanics', 'em', 'thermo', 'quantum', 'optics', 'relativity', 'nuclear', 'statistical'])
    }),

    pa.field('difficulty', pa.int8(), nullable=False, metadata={
        'description': '难度等级 1-5'
    }),

    pa.field('quality_score', pa.float32(), nullable=False, metadata={
        'description': '整体质量评分 0-1'
    }),

    pa.field('answer_unit', pa.string(), nullable=True, metadata={
        'description': '答案单位（SI 标准）'
    }),

    # ========== P3: 扩展字段（3 个）==========

    pa.field('question_type', pa.dictionary('int8', pa.string()), nullable=True, metadata={
        'description': '题目类型',
        'values': json.dumps(['calculation', 'derivation', 'conceptual', 'multiple_choice', 'true_false', 'proof'])
    }),

    pa.field('provenance', pa.string(), nullable=True, metadata={
        'description': '数据处理历史（JSON 格式）',
        'literature': 'W3C PROV'
    }),

    pa.field('solution_steps', pa.string(), nullable=True, metadata={
        'description': '解题步骤（JSON 数组）',
        'format': '[{"step": 1, "desc": "...", "formula": "..."}]',
        'used_by': json.dumps(['CoT 训练']),
        'rationale': '支持思维链训练'
    }),

], metadata={
    'name': 'sft',
    'version': '9.0',
    'description': 'SFT training data for Physics LLM',
    'maintainer': 'Team3-Schema-Group',
    'total_fields': '18'
})


def validate_sft_data(table):
    """Validate SFT data against schema."""
    required_fields = ['question', 'solution', 'answer', 'id', 'source',
                       'annotator', 'created_at', 'schema_version',
                       'physics_topic', 'difficulty', 'quality_score',
                       'ai_generated', 'gold_standard']

    for field in required_fields:
        if field not in table.column_names:
            raise ValueError(f"Missing required field: {field}")

    return True

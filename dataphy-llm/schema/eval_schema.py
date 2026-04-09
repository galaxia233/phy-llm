"""
Eval Schema v9.0 - AI 评测结果

变更：+3 字段（prompt_template, reasoning_trace, calibration_score）
用途：评估 AI 在标准基准上的表现
文献支撑：MMLU, GPQA (arxiv:2308.11963), SciBench (arxiv:2306.09973),
         Chain-of-Thought (arxiv:2201.11903), Confidence Calibration (arxiv:2006.07528)
"""

import json
import pyarrow as pa

EVAL_SCHEMA_V9 = pa.schema([
    # ========== P0: 核心评测字段（5 个）==========

    pa.field('question_id', pa.string(), nullable=False, metadata={
        'description': '问题唯一标识符'
    }),

    pa.field('question', pa.string(), nullable=False, metadata={
        'description': '问题内容',
        'literature': 'MMLU (arxiv:2009.03300)'
    }),

    pa.field('model_output', pa.string(), nullable=False, metadata={
        'description': 'AI 模型输出',
        'used_by': json.dumps(['评测脚本', '错误分析'])
    }),

    pa.field('reference_answer', pa.string(), nullable=False, metadata={
        'description': '参考答案',
        'literature': 'MMLU, GPQA'
    }),

    pa.field('is_correct', pa.bool_(), nullable=False, metadata={
        'description': '是否正确',
        'used_by': json.dumps(['评测统计', '性能分析'])
    }),

    # ========== P1: 数据管理字段（7 个）==========

    pa.field('eval_id', pa.string(), nullable=False, metadata={
        'description': '评测记录 UUID'
    }),

    pa.field('model_checkpoint', pa.string(), nullable=False, metadata={
        'description': '模型检查点版本',
        'used_by': json.dumps(['版本对比', '性能追踪'])
    }),

    pa.field('benchmark', pa.string(), nullable=False, metadata={
        'description': '评测基准名称',
        'values': json.dumps(['MMLU', 'GPQA', 'SciBench', 'BigBench']),
        'literature': '评测基准标准'
    }),

    pa.field('eval_timestamp', pa.timestamp('us', tz='UTC'), nullable=False, metadata={
        'description': '评测时间戳（UTC）'
    }),

    pa.field('schema_version', pa.string(), nullable=False, metadata={
        'description': 'Schema 版本号'
    }),

    pa.field('prompt_template', pa.string(), nullable=True, metadata={
        'description': '使用的 prompt 模板',
        'used_by': json.dumps(['prompt 工程']),
        'rationale': '记录评测时使用的 prompt 模板'
    }),

    pa.field('calibration_score', pa.float32(), nullable=True, metadata={
        'description': '置信度校准分数',
        'format': '0.0-1.0',
        'used_by': json.dumps(['不确定性校准']),
        'rationale': '评估 AI 置信度与准确率的匹配度',
        'literature': 'Confidence Calibration (arxiv:2006.07528)'
    }),

    # ========== P2: 质量管控字段（2 个）==========

    pa.field('score', pa.float32(), nullable=True, metadata={
        'description': '部分分（0-1）',
        'used_by': json.dumps(['细粒度评测'])
    }),

    pa.field('physics_topic', pa.dictionary('int8', pa.string()), nullable=False, metadata={
        'description': '物理主题',
        'values': json.dumps(['mechanics', 'em', 'thermo', 'quantum', 'optics', 'relativity', 'nuclear', 'statistical'])
    }),

    # ========== P3: 扩展字段（5 个）==========

    pa.field('eval_metadata', pa.string(), nullable=True, metadata={
        'description': '评测元数据（JSON 格式）'
    }),

    pa.field('error_type', pa.dictionary('int8', pa.string()), nullable=True, metadata={
        'description': '错误类型',
        'values': json.dumps(['calculation_error', 'concept_error', 'formula_error', 'reasoning_error', 'hallucination', 'format_error', 'timeout'])
    }),

    pa.field('latency_ms', pa.int32(), nullable=True, metadata={
        'description': '推理延迟（毫秒）',
        'used_by': json.dumps(['性能分析', '效率优化'])
    }),

    pa.field('reasoning_trace', pa.string(), nullable=True, metadata={
        'description': '推理过程（CoT）',
        'format': 'JSON 数组，记录每步推理',
        'used_by': json.dumps(['错误分析', 'CoT 研究']),
        'literature': 'Chain-of-Thought (arxiv:2201.11903)'
    }),

    pa.field('adversarial_info', pa.string(), nullable=True, metadata={
        'description': '对抗样本信息（如有）',
        'format': '{"perturbation_type": "...", "robustness_score": 0.0}',
        'used_by': json.dumps(['鲁棒性分析'])
    }),

], metadata={
    'name': 'eval',
    'version': '9.0',
    'description': 'Eval results for Physics LLM',
    'maintainer': 'Team3-Schema-Group',
    'total_fields': '19'
})


def validate_eval_data(table):
    """Validate Eval data against schema."""
    required_fields = ['question_id', 'question', 'model_output',
                       'reference_answer', 'is_correct', 'eval_id',
                       'model_checkpoint', 'benchmark', 'eval_timestamp',
                       'schema_version', 'physics_topic']

    for field in required_fields:
        if field not in table.column_names:
            raise ValueError(f"Missing required field: {field}")

    return True

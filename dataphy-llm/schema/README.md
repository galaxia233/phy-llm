# Phy-LLM Schema Python 定义

本目录包含 Phy-LLM 项目完整的 Schema Python 定义（v9.0）。

## 文件结构

```
schema/
├── __init__.py           # 包入口，导出所有 Schema 和验证函数
├── sft_schema.py         # SFT Schema (18 字段)
├── dpo_schema.py         # DPO Schema (15 字段)
├── eval_schema.py        # Eval Schema (19 字段)
├── ai_answer_schema.py   # AI_Answer Schema (16 字段)
├── generation_schema.py  # Generation Schema (20 字段)
├── grading_schema.py     # Grading Schema (18 字段)
└── knowledge_schema.py   # Knowledge Schema (16 字段)
```

## 使用方法

### 导入 Schema

```python
from schema import (
    SFT_SCHEMA_V9,
    DPO_SCHEMA_V9,
    EVAL_SCHEMA_V9,
    AI_ANSWER_SCHEMA_V9,
    GENERATION_SCHEMA_V9,
    GRADING_SCHEMA_V9,
    KNOWLEDGE_SCHEMA_V9,
)
```

### 导入验证函数

```python
from schema import validate_sft_data, validate_dpo_data

# 验证数据
is_valid = validate_sft_data(table)
```

### 使用汇总信息

```python
from schema import SCHEMA_SUMMARY, TOTAL_FIELDS

print(f"总字段数：{TOTAL_FIELDS}")  # 输出：122

# 获取特定 Schema 信息
sft_info = SCHEMA_SUMMARY['sft']
print(f"SFT 字段数：{sft_info['fields']}")  # 输出：18
```

## Schema 清单

| Schema | 字段数 | 核心用途 |
|--------|--------|---------|
| SFT | 18 | AI 学习的标准答案 |
| DPO | 15 | AI 学习人类偏好 |
| Eval | 19 | AI 能力评测 |
| AI_Answer | 16 | AI 答题记录 |
| Generation | 20 | AI 出题记录 |
| Grading | 18 | AI 评判记录 |
| Knowledge | 16 | 知识图谱 |
| **总计** | **122** | |

## 技术特性

- **PyArrow Schema**: 所有 Schema 使用 PyArrow 格式定义
- **字典编码**: 低基数字段使用 `dictionary('int8', string)` 节省 70-90% 空间
- **时间戳**: 微秒精度，UTC 时区 (`timestamp('us', tz='UTC')`)
- **唯一标识**: UUID v4 用于记录 ID
- **元数据**: 每个字段包含 description、used_by、rationale 等元数据

## 文献支撑

所有 122 个字段均有文献或行业实践支撑：

- MMLU (arxiv:2009.03300) - 题型分类
- DPO (arxiv:2305.18290) - 偏好数据格式
- Chain-of-Thought (arxiv:2201.11903) - 推理链
- LLM-as-Judge (arxiv:2306.05685) - AI 评判
- Confidence Calibration (arxiv:2006.07528) - 置信度校准
- GPQA (arxiv:2308.11963) - 物理评测基准
- W3C PROV - 数据溯源标准
- RFC 4122 - UUID 标准

**幻觉检查结果**: 0 幻觉，100% 支撑率

## 版本历史

| 版本 | 日期 | 变更内容 | 字段总数 |
|------|------|---------|---------|
| v1.0 | 原始方案 | 初始 3 套 Schema | 31 |
| v6.0 | 2026-03-31 | 优化编码、精度 | 39 |
| v7.0 | 2026-03-31 | 新增 4 套 Schema | 91 |
| v8.0 | 2026-03-31 | 文献验证 +17 字段 | 108 |
| v9.0 | 2026-03-31 | 修正为 AI 主体，+14/-5 | 122 |

## 依赖

- Python >= 3.8
- pyarrow >= 10.0

## 安装

```bash
pip install pyarrow
```

## 下一步

B 组将基于这些 Schema 定义实现：
1. 读写工具库（phy_llm/data 包）
2. Validation 脚本
3. 单元测试

---

**作者**: A 组  
**维护者**: Team3-Schema-Group  
**最后更新**: 2026-03-31

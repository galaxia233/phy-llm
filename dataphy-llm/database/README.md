# DuckDB API - Phy-LLM

Phy-LLM 项目的 DuckDB 数据库操作接口，支持 7 套 Schema 表的 CRUD 操作。

## 快速开始

```python
from database.api import DB, open_db, quick_query

# 方式 1：上下文管理（推荐）
with DB() as db:
    db.add_sft(
        question="什么是牛顿第二定律？",
        solution="F=ma",
        answer="F=ma",
        source="textbook",
        annotator="user1",
        physics_topic="mechanics",
        difficulty=1,
        quality_score=0.9
    )
    result = db.get_sft("xxx-uuid-xxx")

# 方式 2：快速查询（自动开关连接）
results = quick_query("SELECT * FROM sft LIMIT 10")
```

## API 参考

### 核心类 `DB`

#### 初始化
```python
db = DB("physics_llm.duckdb")  # 指定数据库文件
db = DB()  # 默认 physics_llm.duckdb
```

#### 通用 CRUD 方法

| 方法 | 说明 |
|------|------|
| `execute(sql, params)` | 执行 SQL，返回结果列表 |
| `insert_dict(table, data)` | 插入单条记录（dict） |
| `insert_many(table, data_list)` | 批量插入 |
| `get(table, id)` | 根据 ID 获取单条记录 |
| `delete(table, id)` | 删除记录 |
| `count(table)` | 统计记录数 |
| `list_all(table, limit)` | 列出记录（带限制） |
| `find_by(table, field, value)` | 按字段查询 |

#### 按表划分的方法

每套 Schema 都有对应的 `add_xxx()` 和 `get_xxx()` 方法：

- `add_sft()` / `get_sft()`
- `add_dpo()` / `get_dpo()`
- `add_eval()` / `get_eval()`
- `add_ai_answer()` / `get_ai_answer()`
- `add_generation()` / `get_generation()`
- `add_grading()` / `get_grading()`
- `add_knowledge()` / `get_knowledge()`

以及常用查询方法：
- `find_sft_by_topic(topic)`
- `find_sft_by_split(split)`
- `find_answers_by_question(question_id)`
- `find_gradings_by_answer(answer_id)`
- `find_knowledge_by_topic(topic)`

#### SQLite/DuckDB 原生语法支持

```python
with DB() as db:
    # 执行脚本
    db.executescript("""
        UPDATE sft SET quality_score = 0.8 WHERE difficulty > 3;
        DELETE FROM eval WHERE score < 0.5;
    """)
    
    # 返回 pandas DataFrame
    df = db.fetchdf("SELECT * FROM sft WHERE physics_topic = ?", ("mechanics",))
    
    # 返回 PyArrow Table
    table = db.fetcharrow("SELECT * FROM sft")
    
    # 导出 Parquet
    db.to_parquet("SELECT * FROM sft", "output.parquet")
    
    # 从 Parquet 导入
    db.from_parquet("data.parquet", "my_table")
    
    # 事务控制
    db.begin()
    try:
        db.add_sft(...)
        db.add_dpo(...)
        db.commit()
    except:
        db.rollback()
```

### 便捷函数

```python
from duckdb.api import open_db, quick_query

# open_db - 打开数据库
db = open_db("my_db.duckdb")

# quick_query - 快速查询
results = quick_query("SELECT COUNT(*) FROM sft")
```

## 使用示例

### 添加 SFT 数据
```python
with DB() as db:
    db.add_sft(
        question="一个质量为 2kg 的物体，在 10N 的力作用下，加速度是多少？",
        solution="根据牛顿第二定律 F=ma，a = F/m = 10N/2kg = 5m/s²",
        answer="5m/s²",
        source="textbook",
        annotator="teacher_wang",
        physics_topic="mechanics",
        difficulty=2,
        quality_score=0.95,
        split="train",
        language="zh"
    )
```

### 查询数据
```python
with DB() as db:
    # 按主题查询
    mechanics_data = db.find_sft_by_topic("mechanics")
    
    # 按数据集划分查询
    train_data = db.find_sft_by_split("train")
    
    # 获取单条记录
    record = db.get_sft("some-uuid-here")
    
    # 自定义 SQL
    results = db.execute("""
        SELECT physics_topic, AVG(quality_score) as avg_score
        FROM sft
        GROUP BY physics_topic
    """)
```

### 批量导入
```python
data_list = [
    {
        "question": "题目 1",
        "solution": "解答 1",
        "answer": "答案 1",
        "source": "textbook",
        "annotator": "user1",
        "physics_topic": "mechanics",
        "difficulty": 1,
        "quality_score": 0.9
    },
    # ... 更多数据
]

with DB() as db:
    db.insert_many("sft", data_list)
```

## 支持的表

| 表名 | 说明 | 字段数 |
|------|------|--------|
| sft | 监督微调数据 | 19 |
| dpo | 偏好优化数据 | 15 |
| eval | 评测数据 | 19 |
| ai_answer | AI 答题记录 | 15 |
| generation | 题目生成记录 | 20 |
| grading | 批改记录 | 18 |
| knowledge | 知识点数据 | 16 |

## 依赖

- Python >= 3.14
- duckdb >= 0.9.0
- pyarrow >= 10.0
- pytz

## 安装

```bash
cd dataphy-llm
pip install -e .
```

---

**维护者**: Team3-Schema-Group  
**最后更新**: 2026-04-01

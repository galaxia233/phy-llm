"""
DuckDB API - Phy-LLM 数据库操作接口

简洁包装 DuckDB，支持 7 套 Schema 表的 CRUD 操作。
支持 DuckDB 原生语法和 SQLite 兼容语法。
"""

import duckdb
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from datetime import datetime


TABLES = [
    'sft', 'dpo', 'eval', 'ai_answer',
    'generation', 'grading', 'knowledge'
]


class DB:
    """DuckDB 数据库操作类"""

    def __init__(self, db_path: str = "physics_llm.duckdb"):
        self.conn = duckdb.connect(db_path)

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ========== 通用方法 ==========

    def execute(self, sql: str, params: tuple = None) -> List[Dict]:
        """执行 SQL，返回结果列表"""
        result = self.conn.execute(sql, params) if params else self.conn.execute(sql)
        cols = [d[0] for d in result.description]
        return [dict(zip(cols, row)) for row in result.fetchall()]

    def insert_dict(self, table: str, data: Dict[str, Any]) -> bool:
        """插入单条记录（dict 格式）"""
        if not data:
            return False
        cols = list(data.keys())
        vals = list(data.values())
        placeholders = ','.join(['?' for _ in cols])
        sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
        self.conn.execute(sql, vals)
        return True

    def insert_many(self, table: str, data_list: List[Dict[str, Any]]) -> int:
        """批量插入"""
        count = 0
        for data in data_list:
            if self.insert_dict(table, data):
                count += 1
        return count

    def get(self, table: str, id: str) -> Optional[Dict]:
        """根据 ID 获取单条记录"""
        results = self.execute(f"SELECT * FROM {table} WHERE id = ?", (id,))
        return results[0] if results else None

    def delete(self, table: str, id: str) -> bool:
        """删除记录"""
        result = self.conn.execute(f"DELETE FROM {table} WHERE id = ?", (id,))
        return result.rowcount > 0

    def count(self, table: str) -> int:
        """统计记录数"""
        result = self.execute(f"SELECT COUNT(*) as cnt FROM {table}")
        return result[0]['cnt'] if result else 0

    def list_all(self, table: str, limit: int = 100) -> List[Dict]:
        """列出记录（带限制）"""
        return self.execute(f"SELECT * FROM {table} LIMIT ?", (limit,))

    def find_by(self, table: str, field: str, value: Any) -> List[Dict]:
        """按字段查询"""
        return self.execute(f"SELECT * FROM {table} WHERE {field} = ?", (value,))

    # ========== SQLite 原生语法支持 ==========

    def executescript(self, sql_script: str) -> None:
        """执行 SQL 脚本（支持多条语句）"""
        self.conn.executescript(sql_script)

    def fetchdf(self, sql: str, params: tuple = None):
        """执行 SQL 并返回 pandas DataFrame"""
        return self.conn.execute(sql, params).fetchdf() if params else self.conn.execute(sql).fetchdf()

    def fetcharrow(self, sql: str, params: tuple = None):
        """执行 SQL 并返回 PyArrow Table"""
        return self.conn.execute(sql, params).fetch_arrow_table() if params else self.conn.execute(sql).fetch_arrow_table()

    def pl(self, sql: str, params: tuple = None):
        """执行 SQL 并返回 DuckDB PyArrow 结果（便捷别名）"""
        return self.conn.execute(sql, params).fetch_arrow_table() if params else self.conn.execute(sql).fetch_arrow_table()

    def insert_arrow(self, table: str, arrow_table) -> int:
        """插入 PyArrow Table 到指定表"""
        result = self.conn.execute(f"INSERT INTO {table} SELECT * FROM arrow_table", [arrow_table])
        return result.rowcount

    def from_parquet(self, parquet_path: str, table_name: str = None) -> str:
        """从 Parquet 文件创建/填充表"""
        if table_name is None:
            table_name = Path(parquet_path).stem
        self.conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM read_parquet('{parquet_path}')")
        return table_name

    def to_parquet(self, sql: str, output_path: str, params: tuple = None) -> None:
        """将查询结果导出为 Parquet 文件"""
        if params:
            self.conn.execute(f"COPY ({sql}) TO '{output_path}' (FORMAT PARQUET)", params)
        else:
            self.conn.execute(f"COPY ({sql}) TO '{output_path}' (FORMAT PARQUET)")

    def begin(self):
        """开始事务"""
        self.conn.execute("BEGIN TRANSACTION")

    def commit(self):
        """提交事务"""
        self.conn.commit()

    def rollback(self):
        """回滚事务"""
        self.conn.rollback()

    # ========== SFT 表方法 ==========

    def add_sft(self, question: str, solution: str, answer: str,
                source: str, annotator: str, physics_topic: str,
                difficulty: int, quality_score: float,
                id: str = None, **kwargs) -> bool:
        """添加 SFT 记录"""
        from uuid import uuid4
        data = {
            'id': id or str(uuid4()),
            'question': question,
            'solution': solution,
            'answer': answer,
            'source': source,
            'annotator': annotator,
            'physics_topic': physics_topic,
            'difficulty': difficulty,
            'quality_score': quality_score,
            'created_at': datetime.now(),
            'schema_version': '9.0',
            'ai_generated': kwargs.get('ai_generated', False),
            'gold_standard': kwargs.get('gold_standard', False),
        }
        # 可选字段
        for key in ['split', 'language', 'answer_unit', 'question_type',
                    'provenance', 'solution_steps']:
            if key in kwargs:
                data[key] = kwargs[key]
        return self.insert_dict('sft', data)

    def get_sft(self, id: str) -> Optional[Dict]:
        return self.get('sft', id)

    def find_sft_by_topic(self, topic: str) -> List[Dict]:
        return self.find_by('sft', 'physics_topic', topic)

    def find_sft_by_split(self, split: str) -> List[Dict]:
        return self.find_by('sft', 'split', split)

    # ========== DPO 表方法 ==========

    def add_dpo(self, question: str, chosen: str, rejected: str,
                annotator: str, physics_topic: str, difficulty: int,
                id: str = None, **kwargs) -> bool:
        """添加 DPO 记录"""
        from uuid import uuid4
        data = {
            'id': id or str(uuid4()),
            'question': question,
            'chosen': chosen,
            'rejected': rejected,
            'annotator': annotator,
            'physics_topic': physics_topic,
            'difficulty': difficulty,
            'created_at': datetime.now(),
            'schema_version': '9.0',
        }
        for key in ['split', 'source_question_id', 'preference_source',
                    'preference_reason', 'comparison_criteria',
                    'confidence_level']:
            if key in kwargs:
                data[key] = kwargs[key]
        return self.insert_dict('dpo', data)

    def get_dpo(self, id: str) -> Optional[Dict]:
        return self.get('dpo', id)

    # ========== Eval 表方法 ==========

    def add_eval(self, question_id: str, question: str, model_output: str,
                 reference_answer: str, is_correct: bool,
                 model_checkpoint: str, benchmark: str,
                 physics_topic: str, eval_id: str = None, **kwargs) -> bool:
        """添加 Eval 记录"""
        from uuid import uuid4
        data = {
            'eval_id': eval_id or str(uuid4()),
            'question_id': question_id,
            'question': question,
            'model_output': model_output,
            'reference_answer': reference_answer,
            'is_correct': is_correct,
            'model_checkpoint': model_checkpoint,
            'benchmark': benchmark,
            'physics_topic': physics_topic,
            'eval_timestamp': datetime.now(timezone.utc),
            'schema_version': '9.0',
        }
        for key in ['prompt_template', 'calibration_score', 'score',
                    'eval_metadata', 'error_type', 'latency_ms',
                    'reasoning_trace', 'adversarial_info']:
            if key in kwargs:
                data[key] = kwargs[key]
        return self.insert_dict('eval', data)

    def get_eval(self, eval_id: str) -> Optional[Dict]:
        return self.get('eval', eval_id)

    # ========== AI_Answer 表方法 ==========

    def add_ai_answer(self, question_id: str, ai_answer: str,
                      is_correct: bool, model_version: str,
                      answer_id: str = None, **kwargs) -> bool:
        """添加 AI_Answer 记录"""
        from uuid import uuid4
        data = {
            'answer_id': answer_id or str(uuid4()),
            'question_id': question_id,
            'ai_answer': ai_answer,
            'is_correct': is_correct,
            'model_version': model_version,
            'submitted_at': datetime.now(timezone.utc),
        }
        for key in ['score', 'time_spent_seconds', 'attempt_number',
                    'prompt_used', 'error_type', 'knowledge_points',
                    'confidence_level', 'reasoning_trace', 'metadata']:
            if key in kwargs:
                data[key] = kwargs[key]
        return self.insert_dict('ai_answer', data)

    def get_ai_answer(self, answer_id: str) -> Optional[Dict]:
        return self.get('ai_answer', answer_id)

    def find_answers_by_question(self, question_id: str) -> List[Dict]:
        return self.find_by('ai_answer', 'question_id', question_id)

    # ========== Generation 表方法 ==========

    def add_generation(self, generation_id: str, question_id: str,
                       prompt: str, model_version: str,
                       difficulty_target: int, topic_constraint: str,
                       quality_check: str, **kwargs) -> bool:
        """添加 Generation 记录"""
        data = {
            'generation_id': generation_id,
            'question_id': question_id,
            'prompt': prompt,
            'model_version': model_version,
            'difficulty_target': difficulty_target,
            'topic_constraint': topic_constraint,
            'quality_check': quality_check,
            'generated_at': datetime.now(timezone.utc),
            'safety_check_passed': kwargs.get('safety_check_passed', True),
            'regeneration_count': kwargs.get('regeneration_count', 0),
        }
        for key in ['generation_params', 'seed', 'tokens_used',
                    'target_difficulty_accuracy', 'rejection_reason',
                    'human_editor', 'question_quality_score',
                    'generation_history', 'metadata', 'human_approval_id']:
            if key in kwargs:
                data[key] = kwargs[key]
        return self.insert_dict('generation', data)

    def get_generation(self, generation_id: str) -> Optional[Dict]:
        return self.get('generation', generation_id)

    # ========== Grading 表方法 ==========

    def add_grading(self, grading_id: str, answer_id: str,
                    grader_type: str, grader_id: str,
                    score: float, max_score: float,
                    **kwargs) -> bool:
        """添加 Grading 记录"""
        data = {
            'grading_id': grading_id,
            'answer_id': answer_id,
            'grader_type': grader_type,
            'grader_id': grader_id,
            'score': score,
            'max_score': max_score,
            'graded_at': datetime.now(timezone.utc),
        }
        for key in ['rubric', 'grading_time_seconds', 'rubric_adherence_score',
                    'feedback', 'error_categories', 'suggestions',
                    'feedback_quality_score', 'human_agreement_rate',
                    'consistency_check', 'requires_review', 'reviewed_by']:
            if key in kwargs:
                data[key] = kwargs[key]
        return self.insert_dict('grading', data)

    def get_grading(self, grading_id: str) -> Optional[Dict]:
        return self.get('grading', grading_id)

    def find_gradings_by_answer(self, answer_id: str) -> List[Dict]:
        return self.find_by('grading', 'answer_id', answer_id)

    # ========== Knowledge 表方法 ==========

    def add_knowledge(self, knowledge_point_id: str, name: str,
                      physics_topic: str, difficulty_level: int,
                      **kwargs) -> bool:
        """添加 Knowledge 记录"""
        data = {
            'knowledge_point_id': knowledge_point_id,
            'name': name,
            'physics_topic': physics_topic,
            'difficulty_level': difficulty_level,
        }
        for key in ['description', 'prerequisite_ids', 'question_ids',
                    'related_kp_ids', 'learning_objectives',
                    'typical_ai_errors', 'mastery_threshold',
                    'common_misconceptions', 'question_generation_templates',
                    'estimated_study_time_minutes', 'metadata',
                    'reasoning_patterns']:
            if key in kwargs:
                data[key] = kwargs[key]
        return self.insert_dict('knowledge', data)

    def get_knowledge(self, knowledge_point_id: str) -> Optional[Dict]:
        return self.get('knowledge', knowledge_point_id)

    def find_knowledge_by_topic(self, topic: str) -> List[Dict]:
        return self.find_by('knowledge', 'physics_topic', topic)


# ========== 便捷函数 ==========

def open_db(db_path: str = "physics_llm.duckdb") -> DB:
    """打开数据库"""
    return DB(db_path)


def quick_query(sql: str, db_path: str = "physics_llm.duckdb") -> List[Dict]:
    """快速查询（自动开关连接）"""
    with DB(db_path) as db:
        return db.execute(sql)

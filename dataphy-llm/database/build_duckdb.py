"""
从 PyArrow Schema 自动生成 DuckDB 建表语句
Usage: python build_duckdb.py
"""

import duckdb
from pathlib import Path

# 导入所有 schema
from schema.ai_answer_schema import AI_ANSWER_SCHEMA_V9 as AI_ANSWER_SCHEMA
from schema.dpo_schema import DPO_SCHEMA_V9 as DPO_SCHEMA
from schema.eval_schema import EVAL_SCHEMA_V9 as EVAL_SCHEMA
from schema.generation_schema import GENERATION_SCHEMA_V9 as GENERATION_SCHEMA
from schema.sft_schema import SFT_SCHEMA_V9 as SFT_SCHEMA
from schema.grading_schema import GRADING_SCHEMA_V9 as GRADING_SCHEMA
from schema.knowledge_schema import KNOWLEDGE_SCHEMA_V9 as KNOWLEDGE_SCHEMA

# schema 模块列表
SCHEMA_MODULES = {
    'ai_answer': AI_ANSWER_SCHEMA,
    'dpo': DPO_SCHEMA,
    'eval': EVAL_SCHEMA,
    'generation': GENERATION_SCHEMA,
    'sft': SFT_SCHEMA,
    'grading': GRADING_SCHEMA,
    'knowledge': KNOWLEDGE_SCHEMA,
}


# PyArrow → DuckDB 类型映射
TYPE_MAP = {
    'string': 'VARCHAR',
    'bool': 'BOOLEAN',
    'float': 'FLOAT',
    'double': 'DOUBLE',
    'int8': 'TINYINT',
    'int16': 'SMALLINT',
    'int32': 'INTEGER',
    'int64': 'BIGINT',
    'timestamp': 'TIMESTAMPTZ',
    'dictionary': 'VARCHAR',  # dictionary encoding
    'list': 'VARCHAR[]',      # list → array
    'struct': 'VARCHAR',      # struct → JSON string
}


def arrow_type_to_duckdb(arrow_type):
    """将 PyArrow 类型转换为 DuckDB 类型"""
    type_str = str(arrow_type).lower()

    # 处理 timestamp
    if 'timestamp' in type_str:
        return 'TIMESTAMPTZ'

    # 处理 list/array
    if 'list' in type_str or 'large_list' in type_str:
        return 'VARCHAR[]'

    # 处理 dictionary
    if 'dictionary' in type_str:
        return 'VARCHAR'

    # 处理 struct（转为 JSON 字符串存储）
    if 'struct' in type_str:
        return 'VARCHAR'

    # 基础类型匹配
    for arrow_key, duckdb_type in TYPE_MAP.items():
        if arrow_key in type_str:
            return duckdb_type

    # 默认返回 VARCHAR
    return 'VARCHAR'


def schema_to_create_table(schema, table_name=None):
    """将 PyArrow Schema 转换为 DuckDB CREATE TABLE 语句"""
    if table_name is None:
        table_name = schema.metadata.get(b'name', b'unknown').decode()

    columns = []
    for field in schema:
        duckdb_type = arrow_type_to_duckdb(field.type)
        nullable = 'NULL' if field.nullable else 'NOT NULL'
        col_def = f"    {field.name} {duckdb_type} {nullable}"
        columns.append(col_def)

    # 添加主键（假设第一个字段是主键）
    pk_field = schema[0].name
    columns.append(f"    PRIMARY KEY ({pk_field})")

    sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n" + ",\n".join(columns) + "\n)"
    return sql


def create_tables_from_schema(conn, schema_obj, table_name=None):
    """从 schema 对象创建 DuckDB 表"""
    # schema_obj 已经是 PyArrow schema 对象
    if table_name is None:
        table_name = schema_obj.metadata.get(b'name', b'unknown').decode()

    # 生成并执行 CREATE TABLE
    sql = schema_to_create_table(schema_obj, table_name)
    conn.execute(sql)
    print(f"[OK] 创建表：{table_name}")

    # 创建索引（基于字段名和常见查询模式）
    create_indexes(conn, schema_obj, table_name)


def create_indexes(conn, schema, table_name):
    """为常用字段创建索引"""
    indexes = []

    for field in schema:
        field_name = field.name

        # 为这些字段创建索引
        if any(kw in field_name.lower() for kw in ['id', 'type', 'split', 'topic', 'checkpoint', 'benchmark']):
            indexes.append(field_name)

        # 时间字段
        if 'timestamp' in str(field.type).lower() or 'time' in field_name.lower() or 'created_at' in field_name.lower():
            indexes.append(field_name)

    # 执行创建索引
    for idx_field in indexes:
        idx_name = f"idx_{table_name}_{idx_field}"
        try:
            conn.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({idx_field})")
            print(f"  └─ 索引：{idx_name}")
        except Exception as e:
            print(f"  └─ 索引失败：{idx_name} - {e}")


def main():
    """主函数"""
    # 连接数据库
    conn = duckdb.connect('physics_llm.duckdb')

    print("开始创建 DuckDB 表...\n")

    for table_name, schema_module in SCHEMA_MODULES.items():
        create_tables_from_schema(conn, schema_module, table_name)

    conn.commit()

    # 显示创建的表
    print("\n" + "=" * 50)
    result = conn.execute("""
        SELECT table_name,
               (SELECT COUNT(*) FROM information_schema.columns c
                WHERE c.table_name = t.table_name) as column_count
        FROM information_schema.tables t
        WHERE table_schema = 'main' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """).fetchall()

    for table, col_count in result:
        print(f"  {table}: {col_count} 列")

    print("\n完成！")
    conn.close()


if __name__ == '__main__':
    main()

"""
DuckDB Tables for Physics LLM Schema v9.0
Generated from PyArrow schema definitions
Maintainer: Team3-Schema-Group
"""

import duckdb

# 连接数据库（内存或文件）
# conn = duckdb.connect(':memory:')  # 内存数据库
conn = duckdb.connect('physics_llm.duckdb')  # 持久化文件


def create_tables():
    """创建所有表"""

    # ========================================================================
    # Table: ai_answer
    # ========================================================================
    conn.execute("""
        CREATE TABLE ai_answer (
            -- P0: 核心答题字段
            answer_id VARCHAR NOT NULL,
            question_id VARCHAR NOT NULL,
            ai_answer VARCHAR NOT NULL,
            is_correct BOOLEAN NOT NULL,
            score FLOAT,

            -- P1: AI 与时间字段
            model_version VARCHAR NOT NULL,
            submitted_at TIMESTAMPTZ NOT NULL,
            time_spent_seconds INTEGER,
            attempt_number TINYINT NOT NULL,
            prompt_used VARCHAR,

            -- P2: 分析字段
            error_type VARCHAR,
            knowledge_points VARCHAR,
            confidence_level TINYINT,
            reasoning_trace VARCHAR,

            -- P3: 扩展字段
            metadata VARCHAR,

            PRIMARY KEY (answer_id)
        )
    """)

    # ========================================================================
    # Table: dpo
    # ========================================================================
    conn.execute("""
        CREATE TABLE dpo (
            -- P0: 核心训练字段
            question VARCHAR NOT NULL,
            chosen VARCHAR NOT NULL,
            rejected VARCHAR NOT NULL,

            -- P1: 数据管理字段
            id VARCHAR NOT NULL,
            split VARCHAR,
            annotator VARCHAR NOT NULL,
            created_at TIMESTAMPTZ NOT NULL,
            schema_version VARCHAR NOT NULL,
            source_question_id VARCHAR,
            preference_source VARCHAR,

            -- P2: 质量管控字段
            physics_topic VARCHAR NOT NULL,
            difficulty TINYINT NOT NULL,

            -- P3: 扩展字段
            preference_reason VARCHAR,
            comparison_criteria VARCHAR,
            confidence_level TINYINT,

            PRIMARY KEY (id)
        )
    """)

    # ========================================================================
    # Table: eval
    # ========================================================================
    conn.execute("""
        CREATE TABLE eval (
            -- P0: 核心评测字段
            question_id VARCHAR NOT NULL,
            question VARCHAR NOT NULL,
            model_output VARCHAR NOT NULL,
            reference_answer VARCHAR NOT NULL,
            is_correct BOOLEAN NOT NULL,

            -- P1: 数据管理字段
            eval_id VARCHAR NOT NULL,
            model_checkpoint VARCHAR NOT NULL,
            benchmark VARCHAR NOT NULL,
            eval_timestamp TIMESTAMPTZ NOT NULL,
            schema_version VARCHAR NOT NULL,
            prompt_template VARCHAR,
            calibration_score FLOAT,

            -- P2: 质量管控字段
            score FLOAT,
            physics_topic VARCHAR NOT NULL,

            -- P3: 扩展字段
            eval_metadata VARCHAR,
            error_type VARCHAR,
            latency_ms INTEGER,
            reasoning_trace VARCHAR,
            adversarial_info VARCHAR,

            PRIMARY KEY (eval_id)
        )
    """)

    # ========================================================================
    # Table: generation
    # ========================================================================
    conn.execute("""
        CREATE TABLE generation (
            -- P0: 核心生成字段
            generation_id VARCHAR NOT NULL,
            question_id VARCHAR NOT NULL,
            prompt VARCHAR NOT NULL,
            model_version VARCHAR NOT NULL,

            -- P1: 生成参数字段
            difficulty_target TINYINT NOT NULL,
            topic_constraint VARCHAR NOT NULL,
            generation_params VARCHAR,
            generated_at TIMESTAMPTZ NOT NULL,
            seed BIGINT,
            tokens_used INTEGER,
            target_difficulty_accuracy FLOAT,

            -- P2: 质量与迭代字段
            regeneration_count TINYINT NOT NULL,
            quality_check VARCHAR NOT NULL,
            rejection_reason VARCHAR,
            human_editor VARCHAR,
            safety_check_passed BOOLEAN NOT NULL,
            question_quality_score FLOAT,

            -- P3: 扩展字段
            generation_history VARCHAR,
            metadata VARCHAR,
            human_approval_id VARCHAR,

            PRIMARY KEY (generation_id)
        )
    """)

    # ========================================================================
    # Table: sft
    # ========================================================================
    conn.execute("""
        CREATE TABLE sft (
            -- P0: 核心训练字段
            question VARCHAR NOT NULL,
            solution VARCHAR NOT NULL,
            answer VARCHAR NOT NULL,

            -- P1: 数据管理字段
            id VARCHAR NOT NULL,
            split VARCHAR,
            source VARCHAR NOT NULL,
            annotator VARCHAR NOT NULL,
            created_at TIMESTAMPTZ NOT NULL,
            schema_version VARCHAR NOT NULL,
            language VARCHAR,
            ai_generated BOOLEAN NOT NULL DEFAULT FALSE,
            gold_standard BOOLEAN NOT NULL DEFAULT FALSE,

            -- P2: 质量管控字段
            physics_topic VARCHAR NOT NULL,
            difficulty TINYINT NOT NULL,
            quality_score FLOAT NOT NULL,
            answer_unit VARCHAR,

            -- P3: 扩展字段
            question_type VARCHAR,
            provenance VARCHAR,
            solution_steps VARCHAR,

            PRIMARY KEY (id)
        )
    """)

    # ========================================================================
    # Table: grading
    # ========================================================================
    conn.execute("""
        CREATE TABLE grading (
            -- P0: 核心批改字段
            grading_id VARCHAR NOT NULL,
            answer_id VARCHAR NOT NULL,
            grader_type VARCHAR NOT NULL,
            grader_id VARCHAR NOT NULL,

            -- P1: 评分细节字段
            score FLOAT NOT NULL,
            max_score FLOAT NOT NULL,
            rubric VARCHAR,
            graded_at TIMESTAMPTZ NOT NULL,
            grading_time_seconds INTEGER,
            rubric_adherence_score FLOAT,

            -- P2: 反馈字段
            feedback VARCHAR,
            error_categories VARCHAR[],
            suggestions VARCHAR,
            feedback_quality_score FLOAT,
            human_agreement_rate FLOAT,

            -- P3: 扩展字段
            consistency_check VARCHAR,
            requires_review BOOLEAN,
            reviewed_by VARCHAR,

            PRIMARY KEY (grading_id)
        )
    """)

    # ========================================================================
    # Table: knowledge
    # ========================================================================
    conn.execute("""
        CREATE TABLE knowledge (
            -- P0: 核心知识字段
            knowledge_point_id VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            description VARCHAR,
            physics_topic VARCHAR NOT NULL,

            -- P1: 关联字段
            prerequisite_ids VARCHAR[],
            question_ids VARCHAR[],
            difficulty_level TINYINT NOT NULL,
            related_kp_ids VARCHAR[],
            learning_objectives VARCHAR,
            typical_ai_errors VARCHAR,

            -- P2: 统计字段
            mastery_threshold FLOAT,
            common_misconceptions VARCHAR,
            question_generation_templates VARCHAR,

            -- P3: 扩展字段
            estimated_study_time_minutes INTEGER,
            metadata VARCHAR,
            reasoning_patterns VARCHAR,

            PRIMARY KEY (knowledge_point_id)
        )
    """)

    # ========================================================================
    # 创建索引
    # ========================================================================

    # ai_answer indexes
    conn.execute("CREATE INDEX idx_ai_answer_question_id ON ai_answer(question_id)")
    conn.execute("CREATE INDEX idx_ai_answer_model_version ON ai_answer(model_version)")
    conn.execute("CREATE INDEX idx_ai_answer_submitted_at ON ai_answer(submitted_at)")

    # dpo indexes
    conn.execute("CREATE INDEX idx_dpo_physics_topic ON dpo(physics_topic)")
    conn.execute("CREATE INDEX idx_dpo_split ON dpo(split)")

    # eval indexes
    conn.execute("CREATE INDEX idx_eval_model_checkpoint ON eval(model_checkpoint)")
    conn.execute("CREATE INDEX idx_eval_benchmark ON eval(benchmark)")
    conn.execute("CREATE INDEX idx_eval_question_id ON eval(question_id)")

    # sft indexes
    conn.execute("CREATE INDEX idx_sft_physics_topic ON sft(physics_topic)")
    conn.execute("CREATE INDEX idx_sft_split ON sft(split)")
    conn.execute("CREATE INDEX idx_sft_source ON sft(source)")

    # grading indexes
    conn.execute("CREATE INDEX idx_grading_answer_id ON grading(answer_id)")
    conn.execute("CREATE INDEX idx_grading_grader_id ON grading(grader_id)")

    # knowledge indexes
    conn.execute("CREATE INDEX idx_knowledge_physics_topic ON knowledge(physics_topic)")
    conn.execute("CREATE INDEX idx_knowledge_prerequisite_ids ON knowledge(prerequisite_ids)")

    conn.commit()
    print("所有表创建成功！")


def show_tables():
    """显示所有表及其结构"""
    result = conn.execute("""
        SELECT table_name, column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'main'
        ORDER BY table_name, ordinal_position
    """).fetchdf()
    print(result.to_string())


if __name__ == '__main__':
    create_tables()
    show_tables()

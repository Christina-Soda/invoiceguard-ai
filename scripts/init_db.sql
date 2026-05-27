-- 建表脚本：scripts/init_db.sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_name     TEXT,
    document_type TEXT,
    status        TEXT DEFAULT 'pending',
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE extracted_fields (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id       UUID REFERENCES documents(id),
    field_name   TEXT,
    value        TEXT,
    evidence     TEXT,           -- 新增：视觉依据
    bounding_box JSONB,
    confidence   TEXT,
    florence_iou FLOAT           -- 新增：Florence-2 验证得分
);

CREATE TABLE rule_results (
    id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id    UUID REFERENCES documents(id),
    rule_name TEXT,
    status    TEXT,
    severity  TEXT,
    detail    TEXT
);

CREATE TABLE review_decisions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id              UUID REFERENCES documents(id),
    decision            TEXT,
    confidence_score    FLOAT,
    confidence_breakdown JSONB,
    explanation         TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE human_feedback (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id           UUID REFERENCES documents(id),
    original_fields  JSONB,
    corrected_fields JSONB,
    changed_fields   TEXT[],
    reviewer_comment TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- Vendor DB（fake）
CREATE TABLE vendors (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name       TEXT UNIQUE,
    status     TEXT DEFAULT 'approved',
    risk_level TEXT DEFAULT 'low',
    risk_reason TEXT
);

-- 历史发票向量（用于去重）
CREATE TABLE invoice_vectors (
    id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id    UUID,
    embedding vector(384)   -- sentence-transformers 维度
);
CREATE INDEX ON invoice_vectors USING ivfflat (embedding vector_cosine_ops);

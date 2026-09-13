CREATE EXTENSION IF NOT EXISTS vector;

DROP TABLE IF EXISTS knowledge;

CREATE TABLE knowledge (
    id SERIAL PRIMARY KEY,
    document_name TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(384),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(document_name, chunk_index)
);
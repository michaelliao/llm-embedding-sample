CREATE EXTENSION vector;

CREATE TABLE IF NOT EXISTS docs (
    id bigserial NOT NULL PRIMARY KEY,
    name varchar(100) NOT NULL,
    content text NOT NULL,
    embedding vector(1536) NOT NULL -- NOTE: 1536 for ChatGPT
);

CREATE INDEX ON docs USING ivfflat (embedding vector_cosine_ops);

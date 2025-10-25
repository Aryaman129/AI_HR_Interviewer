-- Initialize PostgreSQL with pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create tables schema (will be managed by Alembic migrations later)
-- This file just ensures pgvector extension is enabled

-- Test pgvector installation (using proper CAST syntax)
SELECT '[1,2,3]'::vector(3);

-- Create database user with necessary permissions
GRANT ALL PRIVILEGES ON DATABASE aihr_db TO aihr_user;

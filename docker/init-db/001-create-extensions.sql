-- Enable PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create database for testing
SELECT 'CREATE DATABASE athar_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'athar_test')\gexec

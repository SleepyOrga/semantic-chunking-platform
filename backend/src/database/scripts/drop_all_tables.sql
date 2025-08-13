-- Script to completely drop all tables from the database
-- Use with caution! This will delete all tables and data.

-- Disable triggers temporarily
SET session_replication_role = 'replica';

-- Drop tables in reverse order of dependencies
DROP TABLE IF EXISTS chunk_components CASCADE;
DROP TABLE IF EXISTS chunks CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS tags CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Drop the pgvector extension if needed
-- DROP EXTENSION IF EXISTS vector;

-- Drop the uuid-ossp extension if needed
-- DROP EXTENSION IF EXISTS "uuid-ossp";

-- Drop migration tables
DROP TABLE IF EXISTS knex_migrations CASCADE;
DROP TABLE IF EXISTS knex_migrations_lock CASCADE;

-- Re-enable triggers
SET session_replication_role = 'origin';

-- Output success message
DO $$
BEGIN
    RAISE NOTICE 'All tables have been dropped successfully.';
END $$;
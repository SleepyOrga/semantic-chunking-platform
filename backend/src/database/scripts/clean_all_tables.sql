-- Script to clean (truncate) all tables while preserving schema
-- This removes all data but keeps the table structure intact

-- Disable triggers and foreign key constraints temporarily
SET session_replication_role = 'replica';

-- Truncate all tables in reverse order of dependencies
TRUNCATE TABLE chunk_components CASCADE;
TRUNCATE TABLE chunks CASCADE;
TRUNCATE TABLE documents CASCADE;
TRUNCATE TABLE tags CASCADE;
TRUNCATE TABLE users CASCADE;

-- Reset sequences
ALTER SEQUENCE IF EXISTS tags_id_seq RESTART WITH 1;

-- Re-enable triggers and constraints
SET session_replication_role = 'origin';

-- Reset tags sequence to use after the seeded tags
DO $$
BEGIN
    EXECUTE 'SELECT setval(''tags_id_seq'', COALESCE((SELECT MAX(id) FROM tags), 0) + 1, false)';
    RAISE NOTICE 'All tables have been cleaned and sequences reset.';
END $$;
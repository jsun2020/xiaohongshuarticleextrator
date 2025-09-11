-- =====================================================
-- Neon PostgreSQL Database Migration for Multi-User Isolation
-- =====================================================

-- Step 1: Check current table structure
-- Run this first to see the current schema:
\d notes

-- Step 2: Check existing constraints
-- This will show if there are any unique constraints on note_id
SELECT 
    conname AS constraint_name,
    contype AS constraint_type,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint 
WHERE conrelid = 'notes'::regclass;

-- Step 3: Check existing indexes
-- This will show current indexes on the notes table
SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'notes';

-- Step 4: Remove old global unique constraint if it exists
-- WARNING: This will fail if the constraint doesn't exist - that's OK
ALTER TABLE notes DROP CONSTRAINT IF EXISTS notes_note_id_key;

-- Step 5: Add the new composite unique constraint
-- This allows multiple users to save the same note_id
ALTER TABLE notes ADD CONSTRAINT notes_user_id_note_id_unique UNIQUE (user_id, note_id);

-- Step 6: Verify the new constraint was added
-- Run this to confirm the constraint is in place:
SELECT 
    conname AS constraint_name,
    contype AS constraint_type,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint 
WHERE conrelid = 'notes'::regclass
AND conname = 'notes_user_id_note_id_unique';

-- Step 7: Test the constraint (optional)
-- You can test by inserting duplicate data:
-- INSERT INTO notes (user_id, note_id, title, content, type) VALUES (1, 'test123', 'Test', 'Content', 'normal');
-- INSERT INTO notes (user_id, note_id, title, content, type) VALUES (2, 'test123', 'Test', 'Content', 'normal'); -- Should succeed
-- INSERT INTO notes (user_id, note_id, title, content, type) VALUES (1, 'test123', 'Test', 'Content', 'normal'); -- Should fail
# Vercel Neon PostgreSQL Database Migration Guide

## Problem
The Vercel Neon PostgreSQL database still has the old schema where `note_id` is globally unique, preventing multiple users from saving the same Xiaohongshu article.

## Solution
Add a composite unique constraint `UNIQUE(user_id, note_id)` to allow multiple users to save the same article while preventing individual users from creating duplicates.

## Migration Steps

### 1. Connect to Your Neon Database
Use your preferred PostgreSQL client (pgAdmin, DBeaver, psql, or Neon's web console).

### 2. Check Current Schema
```sql
-- See current table structure
\d notes

-- Check existing constraints
SELECT 
    conname AS constraint_name,
    contype AS constraint_type,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint 
WHERE conrelid = 'notes'::regclass;
```

### 3. Apply the Migration
```sql
-- Remove old global unique constraint (if it exists)
ALTER TABLE notes DROP CONSTRAINT IF EXISTS notes_note_id_key;

-- Add new composite unique constraint
ALTER TABLE notes ADD CONSTRAINT notes_user_id_note_id_unique UNIQUE (user_id, note_id);
```

### 4. Verify the Migration
```sql
-- Confirm the new constraint exists
SELECT 
    conname AS constraint_name,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint 
WHERE conrelid = 'notes'::regclass
AND conname = 'notes_user_id_note_id_unique';
```

Expected output:
```
constraint_name               | constraint_definition
notes_user_id_note_id_unique | UNIQUE (user_id, note_id)
```

### 5. Test the Fix (Optional)
```sql
-- Test that different users can save the same note_id
INSERT INTO notes (user_id, note_id, title, content, type, created_at) 
VALUES (1, 'test123', 'Test Note', 'Test Content', 'normal', NOW());

INSERT INTO notes (user_id, note_id, title, content, type, created_at) 
VALUES (2, 'test123', 'Test Note', 'Test Content', 'normal', NOW());
-- ↑ This should succeed

INSERT INTO notes (user_id, note_id, title, content, type, created_at) 
VALUES (1, 'test123', 'Test Note', 'Test Content', 'normal', NOW());
-- ↑ This should fail with duplicate key error

-- Clean up test data
DELETE FROM notes WHERE note_id = 'test123';
```

## Important Notes

1. **Backup First**: Consider backing up your database before migration
2. **Downtime**: This operation should be very fast and cause minimal downtime
3. **Existing Data**: This won't affect existing data, only future inserts
4. **Error Handling**: If the old constraint doesn't exist, the DROP will be silently ignored

## Verifying the Fix Works

After migration, test with your application:
1. Have User A save a Xiaohongshu article
2. Have User B save the same article
3. Both should succeed
4. If User A tries to save the same article again, it should fail

## Alternative: Use Neon Console

If you prefer using Neon's web console:
1. Go to your Neon dashboard
2. Navigate to your database
3. Open the SQL editor
4. Copy and paste the migration commands
5. Execute them one by one
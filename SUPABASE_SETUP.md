# Supabase Setup Instructions

## ⚠️ IMPORTANT: Run This SQL First

Go to your Supabase project → SQL Editor → New Query and run this:

```sql
-- Add sub_code column if it doesn't exist
ALTER TABLE subjects ADD COLUMN IF NOT EXISTS sub_code VARCHAR(20);

-- Add designation column to faculty if it doesn't exist
ALTER TABLE faculty ADD COLUMN IF NOT EXISTS designation VARCHAR(50);

-- Verify columns exist
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'subjects' 
ORDER BY ordinal_position;
```

## ✅ Verify Setup

After running the SQL, check that these columns exist:
- subjects table: `sub_code` (VARCHAR)
- faculty table: `designation` (VARCHAR)

## 🔧 If Table Doesn't Exist

If you get "table doesn't exist" error, run the complete schema from `database_schema.sql` file.

## 📝 Test Data Entry

1. Go to subject.htm
2. Fill in:
   - Academic Year: 2024-25
   - Year: 3
   - Semester: 5
   - Subject Code: IS501
   - Subject Name: Theory of Computation
   - Credits: 4
   - Type: Theory
   - Weekly Hours: 4
3. Click "Add Subject"
4. Check Supabase → Table Editor → subjects table
5. Verify data is saved with sub_code

## 🐛 Troubleshooting

**Error: "sub_code not defined"**
- Run the ALTER TABLE command above
- Refresh your browser
- Try adding a subject again

**Error: "table subjects does not exist"**
- Run the complete database_schema.sql
- Create the table first

**Data not saving**
- Check browser console (F12) for errors
- Verify Supabase URL and API key are correct
- Check network tab for failed requests

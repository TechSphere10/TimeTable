CREATE TABLE IF NOT EXISTS timetable_status (
    id BIGSERIAL PRIMARY KEY,
    department VARCHAR(10) NOT NULL,
    academic_year VARCHAR(10) NOT NULL,
    year INTEGER NOT NULL,
    semester INTEGER NOT NULL,
    is_finalized BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(department, academic_year, year, semester)
);

-- RLS Policies for the new table
ALTER TABLE timetable_status ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all operations on timetable_status" ON timetable_status;
CREATE POLICY "Allow all operations on timetable_status" ON timetable_status FOR ALL USING (true);

-- Trigger for updated_at
DROP TRIGGER IF EXISTS update_timetable_status_updated_at ON timetable_status;
CREATE TRIGGER update_timetable_status_updated_at
    BEFORE UPDATE ON timetable_status
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

SELECT '✅ timetable_status table created successfully.' as status;

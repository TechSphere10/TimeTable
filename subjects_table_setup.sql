-- SQL commands to run in Supabase SQL Editor
-- This will create the subjects table for storing subject information

-- Create subjects table
CREATE TABLE IF NOT EXISTS subjects (
    id SERIAL PRIMARY KEY,
    department VARCHAR(100) NOT NULL,
    academic_year VARCHAR(20) NOT NULL,
    year VARCHAR(10) NOT NULL,
    semester VARCHAR(10) NOT NULL,
    name VARCHAR(255) NOT NULL,
    credits INTEGER DEFAULT 1,
    hours INTEGER DEFAULT 3,
    type VARCHAR(50) DEFAULT 'theory',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_subjects_department ON subjects(department);
CREATE INDEX IF NOT EXISTS idx_subjects_academic_year ON subjects(academic_year);
CREATE INDEX IF NOT EXISTS idx_subjects_year_semester ON subjects(year, semester);

-- Enable Row Level Security (RLS)
ALTER TABLE subjects ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations for now (you can make this more restrictive later)
CREATE POLICY "Allow all operations on subjects" ON subjects
    FOR ALL USING (true);

-- Create function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_subjects_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_subjects_updated_at 
    BEFORE UPDATE ON subjects 
    FOR EACH ROW 
    EXECUTE FUNCTION update_subjects_updated_at_column();

-- Insert some sample data (optional)
INSERT INTO subjects (department, academic_year, year, semester, name, credits, hours, type) VALUES
    ('ISE', '2024-25', '1', '1', 'Mathematics I', 4, 4, 'theory'),
    ('ISE', '2024-25', '1', '1', 'Physics', 3, 3, 'theory'),
    ('ISE', '2024-25', '1', '1', 'Programming Lab', 2, 4, 'lab'),
    ('CSE', '2024-25', '1', '1', 'Computer Fundamentals', 3, 3, 'theory'),
    ('CSE', '2024-25', '1', '1', 'C Programming Lab', 2, 4, 'lab')
ON CONFLICT DO NOTHING;
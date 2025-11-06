-- SQL commands to run in Supabase SQL Editor
-- This will create the faculty table for storing faculty information

-- Create faculty table
CREATE TABLE IF NOT EXISTS faculty (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    initials VARCHAR(10) NOT NULL,
    type VARCHAR(50) NOT NULL,
    department VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster queries by department
CREATE INDEX IF NOT EXISTS idx_faculty_department ON faculty(department);

-- Enable Row Level Security (RLS)
ALTER TABLE faculty ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations for now (you can make this more restrictive later)
CREATE POLICY "Allow all operations on faculty" ON faculty
    FOR ALL USING (true);

-- Create function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_faculty_updated_at 
    BEFORE UPDATE ON faculty 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert some sample data (optional)
INSERT INTO faculty (name, initials, type, department) VALUES
    ('Dr. John Smith', 'JS', 'Professor', 'ISE'),
    ('Ms. Sarah Johnson', 'SJ', 'Assistant Professor', 'ISE'),
    ('Mr. Mike Wilson', 'MW', 'Lab Assistant', 'ISE')
ON CONFLICT DO NOTHING;
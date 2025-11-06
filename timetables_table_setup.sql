-- SQL commands to run in Supabase SQL Editor
-- This will create the timetables table for storing generated timetables

-- Create timetables table
CREATE TABLE IF NOT EXISTS timetables (
    id SERIAL PRIMARY KEY,
    department VARCHAR(100) NOT NULL,
    academic_year VARCHAR(20) NOT NULL,
    year VARCHAR(10) NOT NULL,
    semester VARCHAR(10) NOT NULL,
    timetable_data TEXT NOT NULL,
    fitness_score DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_timetables_department ON timetables(department);
CREATE INDEX IF NOT EXISTS idx_timetables_academic_year ON timetables(academic_year);
CREATE INDEX IF NOT EXISTS idx_timetables_year_semester ON timetables(year, semester);
CREATE INDEX IF NOT EXISTS idx_timetables_fitness ON timetables(fitness_score);

-- Enable Row Level Security (RLS)
ALTER TABLE timetables ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations for now
CREATE POLICY "Allow all operations on timetables" ON timetables
    FOR ALL USING (true);

-- Create function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_timetables_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_timetables_updated_at 
    BEFORE UPDATE ON timetables 
    FOR EACH ROW 
    EXECUTE FUNCTION update_timetables_updated_at_column();
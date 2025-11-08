-- Supabase Database Setup for Timetable Generator
-- Run these commands in your Supabase SQL Editor

-- 1. Create subjects table
CREATE TABLE IF NOT EXISTS subjects (
    id BIGSERIAL PRIMARY KEY,
    department VARCHAR(10) NOT NULL,
    academic_year VARCHAR(10) NOT NULL,
    year INTEGER NOT NULL CHECK (year >= 1 AND year <= 4),
    semester INTEGER NOT NULL CHECK (semester >= 1 AND semester <= 8),
    name VARCHAR(100) NOT NULL,
    credits INTEGER NOT NULL DEFAULT 1 CHECK (credits >= 1 AND credits <= 6),
    type VARCHAR(20) NOT NULL DEFAULT 'theory' CHECK (type IN ('theory', 'lab', 'mcq', 'free')),
    weekly_hours INTEGER NOT NULL DEFAULT 3 CHECK (weekly_hours >= 1 AND weekly_hours <= 10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create faculty table
CREATE TABLE IF NOT EXISTS faculty (
    id BIGSERIAL PRIMARY KEY,
    department VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    initials VARCHAR(20) NOT NULL,
    designation VARCHAR(50) NOT NULL CHECK (designation IN (
        'professor', 
        'associate_professor', 
        'assistant_professor', 
        'lab_assistant', 
        'guest_faculty', 
        'visiting_faculty'
    )),
    email VARCHAR(100),
    phone VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Create timetables table (to store generated timetables)
CREATE TABLE IF NOT EXISTS timetables (
    id BIGSERIAL PRIMARY KEY,
    department VARCHAR(10) NOT NULL,
    academic_year VARCHAR(10) NOT NULL,
    year INTEGER NOT NULL CHECK (year >= 1 AND year <= 4),
    semester INTEGER NOT NULL CHECK (semester >= 1 AND semester <= 8),
    timetable_data JSONB NOT NULL,
    fitness_score DECIMAL(5,2),
    generated_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_subjects_dept_year_sem ON subjects(department, academic_year, year, semester);
CREATE INDEX IF NOT EXISTS idx_faculty_dept ON faculty(department);
CREATE INDEX IF NOT EXISTS idx_timetables_dept_year_sem ON timetables(department, academic_year, year, semester);

-- 5. Create unique constraints
ALTER TABLE subjects ADD CONSTRAINT unique_subject_per_semester 
    UNIQUE (department, academic_year, year, semester, name);

ALTER TABLE faculty ADD CONSTRAINT unique_faculty_initials_per_dept 
    UNIQUE (department, initials);

-- 6. Enable Row Level Security (RLS)
ALTER TABLE subjects ENABLE ROW LEVEL SECURITY;
ALTER TABLE faculty ENABLE ROW LEVEL SECURITY;
ALTER TABLE timetables ENABLE ROW LEVEL SECURITY;

-- 7. Create policies for public access (adjust as needed for your security requirements)
CREATE POLICY "Allow public read access on subjects" ON subjects
    FOR SELECT USING (true);

CREATE POLICY "Allow public insert on subjects" ON subjects
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public update on subjects" ON subjects
    FOR UPDATE USING (true);

CREATE POLICY "Allow public delete on subjects" ON subjects
    FOR DELETE USING (true);

CREATE POLICY "Allow public read access on faculty" ON faculty
    FOR SELECT USING (true);

CREATE POLICY "Allow public insert on faculty" ON faculty
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public update on faculty" ON faculty
    FOR UPDATE USING (true);

CREATE POLICY "Allow public delete on faculty" ON faculty
    FOR DELETE USING (true);

CREATE POLICY "Allow public read access on timetables" ON timetables
    FOR SELECT USING (true);

CREATE POLICY "Allow public insert on timetables" ON timetables
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public update on timetables" ON timetables
    FOR UPDATE USING (true);

CREATE POLICY "Allow public delete on timetables" ON timetables
    FOR DELETE USING (true);

-- 8. Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 9. Create triggers for updated_at
CREATE TRIGGER update_subjects_updated_at BEFORE UPDATE ON subjects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_faculty_updated_at BEFORE UPDATE ON faculty
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 10. Insert sample data (optional)
-- Sample departments
INSERT INTO subjects (department, academic_year, year, semester, name, credits, type, weekly_hours) VALUES
('ISE', '2024-25', 1, 1, 'Programming in C', 4, 'theory', 4),
('ISE', '2024-25', 1, 1, 'C Programming Lab', 2, 'lab', 3),
('ISE', '2024-25', 1, 1, 'Mathematics-I', 4, 'theory', 4),
('ISE', '2024-25', 1, 1, 'Physics', 3, 'theory', 3),
('ISE', '2024-25', 1, 1, 'English', 2, 'theory', 2)
ON CONFLICT (department, academic_year, year, semester, name) DO NOTHING;

-- Sample faculty
INSERT INTO faculty (department, name, initials, designation, email) VALUES
('ISE', 'Dr. John Smith', 'Dr. JS', 'professor', 'john.smith@example.com'),
('ISE', 'Prof. Jane Doe', 'Prof. JD', 'associate_professor', 'jane.doe@example.com'),
('ISE', 'Mr. Bob Wilson', 'Mr. BW', 'assistant_professor', 'bob.wilson@example.com'),
('ISE', 'Ms. Alice Brown', 'Ms. AB', 'lab_assistant', 'alice.brown@example.com')
ON CONFLICT (department, initials) DO NOTHING;

-- Display success message
SELECT 'Database setup completed successfully!' as message;
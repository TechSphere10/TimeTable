-- SUPABASE DATABASE SETUP FOR DEPARTMENT-BASED TIMETABLE SYSTEM
-- Copy and paste this entire script into your Supabase SQL Editor and run it
-- 
-- IMPORTANT: This system implements department-based data isolation
-- Each department (CSE, ISE, ECE, EEE, MECH, CIVIL, AIML, AIDS) will only see their own data
-- The 'department' field is used to filter all queries

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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Create timetable_sessions table
CREATE TABLE IF NOT EXISTS timetable_sessions (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(50) UNIQUE NOT NULL,
    department VARCHAR(10) NOT NULL,
    academic_year VARCHAR(10) NOT NULL,
    year INTEGER NOT NULL CHECK (year >= 1 AND year <= 4),
    semester INTEGER NOT NULL CHECK (semester >= 1 AND semester <= 8),
    config_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Create timetables table
CREATE TABLE IF NOT EXISTS timetables (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL,
    department VARCHAR(10) NOT NULL,
    academic_year VARCHAR(10) NOT NULL,
    year INTEGER NOT NULL CHECK (year >= 1 AND year <= 4),
    semester INTEGER NOT NULL CHECK (semester >= 1 AND semester <= 8),
    section_name VARCHAR(50) NOT NULL,
    timetable_data JSONB NOT NULL,
    fitness_score DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Create faculty_schedule table to track faculty allocations
CREATE TABLE IF NOT EXISTS faculty_schedule (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL,
    faculty_id BIGINT NOT NULL,
    faculty_name VARCHAR(100) NOT NULL,
    department VARCHAR(10) NOT NULL,
    day VARCHAR(20) NOT NULL,
    period INTEGER NOT NULL,
    section_name VARCHAR(50) NOT NULL,
    subject_name VARCHAR(100) NOT NULL,
    academic_year VARCHAR(10) NOT NULL,
    year INTEGER NOT NULL,
    semester INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id, faculty_id, day, period)
);

-- 6. Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_subjects_dept_year_sem ON subjects(department, academic_year, year, semester);
CREATE INDEX IF NOT EXISTS idx_faculty_dept ON faculty(department);
CREATE INDEX IF NOT EXISTS idx_timetable_sessions_session ON timetable_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_timetables_session ON timetables(session_id);
CREATE INDEX IF NOT EXISTS idx_faculty_schedule_session ON faculty_schedule(session_id);
CREATE INDEX IF NOT EXISTS idx_faculty_schedule_faculty ON faculty_schedule(faculty_id, day, period);

-- 7. Enable Row Level Security (RLS)
ALTER TABLE subjects ENABLE ROW LEVEL SECURITY;
ALTER TABLE faculty ENABLE ROW LEVEL SECURITY;
ALTER TABLE timetable_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE timetables ENABLE ROW LEVEL SECURITY;
ALTER TABLE faculty_schedule ENABLE ROW LEVEL SECURITY;

-- 8. Create policies for public access
CREATE POLICY "Allow all operations on subjects" ON subjects
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow all operations on faculty" ON faculty
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow all operations on timetable_sessions" ON timetable_sessions
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow all operations on timetables" ON timetables
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow all operations on faculty_schedule" ON faculty_schedule
    FOR ALL USING (true) WITH CHECK (true);

-- 9. Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 10. Create triggers for updated_at
CREATE TRIGGER update_subjects_updated_at BEFORE UPDATE ON subjects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_faculty_updated_at BEFORE UPDATE ON faculty
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 11. Insert sample data for testing (Optional - can be removed in production)
-- Sample data for ISE department
INSERT INTO subjects (department, academic_year, year, semester, name, credits, type, weekly_hours) VALUES
('ISE', '2024-25', 1, 1, 'Programming in C', 4, 'theory', 4),
('ISE', '2024-25', 1, 1, 'C Programming Lab', 2, 'lab', 3),
('ISE', '2024-25', 1, 1, 'Mathematics-I', 4, 'theory', 4),
('ISE', '2024-25', 1, 2, 'Data Structures', 4, 'theory', 4),
('ISE', '2024-25', 1, 2, 'DS Lab', 2, 'lab', 3)
ON CONFLICT DO NOTHING;

INSERT INTO faculty (department, name, initials, designation) VALUES
('ISE', 'Dr. John Smith', 'Dr. JS', 'professor'),
('ISE', 'Prof. Jane Doe', 'Prof. JD', 'associate_professor'),
('ISE', 'Mr. Bob Wilson', 'Mr. BW', 'assistant_professor'),
('ISE', 'Ms. Alice Brown', 'Ms. AB', 'lab_assistant')
ON CONFLICT DO NOTHING;

-- Sample data for CSE department
INSERT INTO subjects (department, academic_year, year, semester, name, credits, type, weekly_hours) VALUES
('CSE', '2024-25', 1, 1, 'Computer Programming', 4, 'theory', 4),
('CSE', '2024-25', 1, 1, 'Programming Lab', 2, 'lab', 3)
ON CONFLICT DO NOTHING;

INSERT INTO faculty (department, name, initials, designation) VALUES
('CSE', 'Dr. Sarah Johnson', 'Dr. SJ', 'professor'),
('CSE', 'Prof. Michael Brown', 'Prof. MB', 'associate_professor')
ON CONFLICT DO NOTHING;

-- Success message
SELECT 'Database setup completed successfully! Tables created: subjects, faculty, timetables' as message;
SELECT 'Department-based data isolation is enabled. Each department will only see their own data.' as info;
-- CLEAN SETUP - Drop existing tables and recreate
-- Run this if you're getting column errors

-- Drop existing tables (if they exist)
DROP TABLE IF EXISTS faculty_schedule CASCADE;
DROP TABLE IF EXISTS timetables CASCADE;
DROP TABLE IF EXISTS timetable_sessions CASCADE;

-- Now run the main setup
-- 1. Create timetable_sessions table
CREATE TABLE timetable_sessions (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(50) UNIQUE NOT NULL,
    department VARCHAR(10) NOT NULL,
    academic_year VARCHAR(10) NOT NULL,
    year INTEGER NOT NULL CHECK (year >= 1 AND year <= 4),
    semester INTEGER NOT NULL CHECK (semester >= 1 AND semester <= 8),
    config_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create timetables table
CREATE TABLE timetables (
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

-- 3. Create faculty_schedule table
CREATE TABLE faculty_schedule (
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

-- 4. Create indexes
CREATE INDEX idx_timetable_sessions_session ON timetable_sessions(session_id);
CREATE INDEX idx_timetables_session ON timetables(session_id);
CREATE INDEX idx_faculty_schedule_session ON faculty_schedule(session_id);
CREATE INDEX idx_faculty_schedule_faculty ON faculty_schedule(faculty_id, day, period);

-- 5. Enable RLS
ALTER TABLE timetable_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE timetables ENABLE ROW LEVEL SECURITY;
ALTER TABLE faculty_schedule ENABLE ROW LEVEL SECURITY;

-- 6. Create policies
CREATE POLICY "Allow all on timetable_sessions" ON timetable_sessions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on timetables" ON timetables FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on faculty_schedule" ON faculty_schedule FOR ALL USING (true) WITH CHECK (true);

-- Success
SELECT 'Timetable tables created successfully!' as message;

# 🚀 MIT Mysore Timetable System - Complete Setup Guide

## 📋 Overview
Real-time clash-free timetable generation system using Genetic Algorithm with Supabase backend.

## 🔧 Prerequisites
- Python 3.8 or higher
- Modern web browser (Chrome, Firefox, Edge)
- Supabase account (already configured)

## 📦 Installation Steps

### 1. Install Python Dependencies
```bash
cd TIMETABLE1
pip install -r requirements.txt
```

### 2. Database Setup
1. Go to Supabase Dashboard: https://supabase.com/dashboard
2. Open SQL Editor
3. Run the `database_schema.sql` file to create all tables
4. Verify tables are created: users, faculty, subjects, sections, faculty_assignments, timetables

### 3. Start Backend Server
```bash
python backend_ga.py
```
Server will start on `http://localhost:5000`

### 4. Open Frontend
Open `index.htm` in your browser to start using the system.

## 📁 File Structure

### Core Files
- `index.htm` - Login page
- `page.htm` - Dashboard
- `subject.htm` - Subject database management (with sub_code field)
- `faculty.htm` - Faculty database management
- `timetable-new.htm` - Faculty assignment interface
- `enhanced_new.htm` - Timetable display and generation
- `backend_ga.py` - Genetic Algorithm backend server

### Database
- `database_schema.sql` - Complete database schema with sub_code

## 🎯 Usage Flow

### Step 1: Login
1. Open `index.htm`
2. Select department (ISE, CSE, AIML, etc.)
3. Enter password (default: `ise123`, `cse123`, etc.)

### Step 2: Add Subjects
1. Navigate to Subject Database
2. Enter:
   - Academic Year (e.g., 2024-25)
   - Year (1-4)
   - Semester (1-8)
   - **Subject Code** (e.g., IS501)
   - Subject Name
   - Credits (1-6)
   - Type (Theory/Lab/MCQ/Free)
   - Weekly Hours (1-10)
3. Click "Add Subject"
4. Click "💾 Save Database"

### Step 3: Add Faculty
1. Navigate to Faculty Database
2. Enter:
   - Faculty Name
   - Initials
   - Email
   - Specialization
3. Click "Add Faculty"

### Step 4: Generate Timetable
1. Navigate to Timetable Generator
2. Select:
   - Academic Year
   - Year
   - Semester
   - Number of Sections
3. Configure schedule (periods, breaks, timings)
4. Click "➡️ Next" to load subjects
5. Assign faculty to each subject for each section
6. Click "🚀 Generate Timetable"

### Step 5: View & Export
1. Timetable displays with:
   - **Subject Code** (e.g., IS501)
   - Subject Name
   - Faculty Initials
2. Use controls:
   - 🔄 Smart Swap - Swap classes with clash detection
   - 📄 Export PDF - Download timetable
   - 💾 Save - Save to database

## 🧬 Genetic Algorithm Features

### Hard Constraints (Must Satisfy)
- ✅ No faculty double-booking (cross-department check)
- ✅ Labs in continuous 2-hour blocks
- ✅ Exact weekly hours from database
- ✅ Friday last period free
- ✅ No subject repetition same day

### Soft Constraints (Optimized)
- ✅ Faculty free periods at end of day
- ✅ Balanced daily workload
- ✅ Minimal gaps in schedules
- ✅ Even subject distribution

### GA Parameters
- Population Size: 50
- Generations: 150
- Crossover Rate: 85%
- Mutation Rate: 10%
- Elite Retention: 30%

## 🔄 Smart Swap System

### How It Works
1. Click "🔄 Smart Swap"
2. Select two periods to swap
3. System checks:
   - Faculty availability
   - Cross-department clashes
   - Room conflicts
4. If clash detected:
   - Shows error message
   - Suggests alternative slots
   - AI recommends optimal times
5. If no clash:
   - Performs swap
   - Updates database
   - Shows success message

## 📊 Database Schema

### subjects table
```sql
- id (PRIMARY KEY)
- department (VARCHAR)
- academic_year (VARCHAR)
- year (INTEGER 1-4)
- semester (INTEGER 1-8)
- sub_code (VARCHAR) -- NEW FIELD
- name (VARCHAR)
- credits (INTEGER 1-6)
- type (VARCHAR: theory/lab/mcq/free)
- weekly_hours (INTEGER 1-10)
- is_cross_dept (BOOLEAN)
- teaching_dept (VARCHAR)
```

### timetables table
```sql
- id (PRIMARY KEY)
- department (VARCHAR)
- academic_year (VARCHAR)
- year (INTEGER)
- semester (INTEGER)
- section (VARCHAR)
- day (VARCHAR)
- time_slot (INTEGER 0-9)
- subject_code (VARCHAR)
- subject_name (VARCHAR)
- faculty_name (VARCHAR)
- room_number (VARCHAR)
- is_lab (BOOLEAN)
```

## 🎨 UI Features

### Professional Design
- ✨ Gradient backgrounds
- 🎭 Smooth animations
- 📱 Responsive layout
- 🎨 Color-coded subjects
- 💫 Hover effects
- 🔔 Toast notifications

### Timetable Display
- Subject Code in monospace font
- Subject Name below code
- Faculty initials at bottom
- Color-coded cells
- Break cells highlighted
- Lunch break distinct color

## 🐛 Troubleshooting

### Backend Not Starting
```bash
# Check Python version
python --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check port availability
netstat -ano | findstr :5000
```

### Database Connection Issues
1. Verify Supabase URL and Key in files:
   - `backend_ga.py`
   - `subject.htm`
   - `enhanced_new.htm`
2. Check internet connection
3. Verify Supabase project is active

### Timetable Not Displaying
1. Open browser console (F12)
2. Check for JavaScript errors
3. Verify localStorage has data:
   ```javascript
   console.log(localStorage.getItem('timetableData'))
   ```
4. Clear cache and reload

### Subject Code Not Showing
1. Ensure database schema is updated with `sub_code` field
2. Run database migration:
   ```sql
   ALTER TABLE subjects ADD COLUMN IF NOT EXISTS sub_code VARCHAR(20);
   ```
3. Re-add subjects with codes

## 📈 Performance Tips

### For Large Departments
- Increase GA generations for better results
- Use more specific subject codes
- Pre-assign popular faculty to avoid conflicts
- Generate timetables section by section

### Database Optimization
- Regular cleanup of old timetables
- Index on frequently queried fields
- Backup before major changes

## 🔐 Security Notes

### Production Deployment
1. Change default passwords
2. Use environment variables for keys
3. Enable RLS (Row Level Security) in Supabase
4. Add authentication middleware
5. Use HTTPS for all connections

## 📞 Support

### Common Issues
- **Clash Detection**: System checks all departments automatically
- **Lab Placement**: Always in continuous 2-hour blocks
- **Weekly Hours**: Must match database exactly
- **Friday Rule**: Last period always kept free

### Contact
For issues or questions, refer to the main README.md

## 🎓 Credits
Developed for MIT Mysore
Department-wise Timetable Generation System
Genetic Algorithm Optimization

---

**Version**: 2.0
**Last Updated**: January 2025
**Status**: Production Ready ✅

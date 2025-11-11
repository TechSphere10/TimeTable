# MIT Mysore Timetable Generation System - Complete Documentation

## 📋 System Overview

This is a complete timetable generation system for MIT Mysore that uses genetic algorithms to create optimal timetables while respecting institutional constraints.

---

## 🔄 Complete Data Flow

### **Phase 1: Login & Authentication**
**File**: `index.htm`

#### Inputs:
- **Department**: Selected from dropdown (CSE, ISE, AIML, etc.)
- **Password**: User password for authentication

#### Process:
1. User selects department from dropdown
2. Enters password
3. System validates credentials against Supabase `users` table
4. Stores department in `localStorage.currentDepartment`

#### Outputs:
- Redirects to `page.htm` on successful login
- Stores: `localStorage.currentDepartment = "ISE"` (example)

---

### **Phase 2: Subject Management**
**File**: `subject.htm`

#### Inputs:
- **Subject Name**: e.g., "Theory of Computation"
- **Subject Code**: e.g., "TOC"
- **Credits**: e.g., 3
- **Type**: "Theory" or "Lab"
- **Weekly Hours**: e.g., 3 (how many hours per week this subject needs)
- **Academic Year**: e.g., "2024-25"
- **Year**: 1, 2, 3, or 4
- **Semester**: 1-8

#### Process:
1. User fills subject details form
2. Clicks "Add Subject" button
3. Subject added to local list
4. Clicks "💾 Save Database" to persist

#### Storage:
**Supabase Table**: `subjects`
```sql
{
  id: auto-generated,
  department: "ISE",
  name: "Theory of Computation",
  code: "TOC",
  credits: 3,
  type: "theory",
  weekly_hours: 3,
  academic_year: "2024-25",
  year: 3,
  semester: 5
}
```

#### Outputs:
- Subjects stored in Supabase `subjects` table
- Backup in `localStorage.subjects`

---

### **Phase 3: Faculty Management**
**File**: `faculty.htm`

#### Inputs:
- **Faculty Name**: e.g., "Dr. John Smith"
- **Initials**: e.g., "DJS"
- **Designation**: Professor, Assistant Professor, etc.
- **Department**: Auto-filled from login

#### Process:
1. User enters faculty details
2. Clicks "Add Faculty" button
3. Faculty added to local list
4. Clicks "💾 Save Database" to persist

#### Storage:
**Supabase Table**: `faculty`
```sql
{
  id: auto-generated,
  department: "ISE",
  name: "Dr. John Smith",
  initials: "DJS",
  designation: "professor"
}
```

#### Outputs:
- Faculty stored in Supabase `faculty` table
- Backup in `localStorage.faculty`

---

### **Phase 4: Timetable Configuration**
**File**: `timetable-new.htm`

#### Inputs:

**Section 1: Quick Setup**
- **Working Days**: 5 or 6 days (Tuesday-Saturday selected)
- **Academic Year**: "2024-25"
- **Year**: 3
- **Semester**: 5
- **Number of Sections**: 1, 2, 3, etc.

**Section 2: Schedule Config**
- **Periods Per Day**: 7
- **After Lunch Periods**: 3
- **Start Time**: 09:00
- **End Time**: 17:00
- **Short Break**: 11:00-11:15
- **Lunch Break**: 13:00-14:00

**Section 3: Subject Loading**
- Clicks "➡️ Next" button
- System fetches subjects from Supabase based on:
  - Department (from login)
  - Academic Year
  - Year
  - Semester

**Section 4: Faculty Assignment**
- For each subject and each section:
  - Select faculty from dropdown
  - Faculty list filtered by department

#### Process:
1. User fills configuration details
2. Clicks "➡️ Next" to load subjects
3. System queries Supabase:
```javascript
supabase.from('subjects')
  .select('*')
  .eq('department', 'ISE')
  .eq('academic_year', '2024-25')
  .eq('year', 3)
  .eq('semester', 5)
```
4. Displays subjects with weekly hours
5. User assigns faculty to each subject for each section
6. Clicks "🚀 Generate Timetable"

#### Data Structure Created:
```javascript
timetableData = {
  department: "ISE",
  semester: "5",
  year: "3",
  academicYear: "2024-25",
  sections: [
    {
      name: "A",
      assignments: [
        {
          subject: "TOC",
          subjectId: 123,
          faculty: "Dr. John Smith",
          facultyId: 456,
          facultyInitials: "DJS",
          credits: 3,
          type: "theory",
          weekly_hours: 3  // ← KEY: Hours per week from database
        },
        {
          subject: "CNS",
          faculty: "Prof. Jane Doe",
          type: "theory",
          weekly_hours: 4
        },
        {
          subject: "ML Lab",
          faculty: "Dr. Bob Wilson",
          type: "lab",
          weekly_hours: 2  // ← Lab gets 2-hour continuous block
        }
      ]
    },
    {
      name: "B",
      assignments: [...]
    }
  ]
}
```

#### Storage:
- Stored in `localStorage.timetableData`
- Used by `enhanced.htm` for generation

#### Outputs:
- Redirects to `enhanced.htm`
- Passes complete configuration data

---

### **Phase 5: Timetable Generation**
**File**: `enhanced.htm`

#### Inputs (from localStorage):
```javascript
{
  department: "ISE",
  semester: "5",
  sections: [
    {
      name: "A",
      assignments: [
        {
          subject: "TOC",
          faculty: "Dr. John Smith",
          weekly_hours: 3,  // ← Used to create 3 sessions
          type: "theory"
        },
        {
          subject: "ML Lab",
          faculty: "Dr. Bob Wilson",
          weekly_hours: 2,  // ← Used to create 1 lab session (2 hours)
          type: "lab"
        }
      ]
    }
  ]
}
```

#### Process:

**Step 1: Load Data**
```javascript
loadTimetableData() {
  - Read from localStorage.timetableData
  - Store department
  - Load existing timetables from Supabase for clash detection
}
```

**Step 2: Generate Structure**
```javascript
generateTimetableStructure() {
  - Create timetable HTML for each section
  - Days: Tuesday, Wednesday, Thursday, Friday, Saturday
  - Slots: 0-5 (6 periods per day)
  - Total: 30 slots per section
}
```

**Step 3: Generate Timetable (Click "🧬 Generate GA")**
```javascript
generateTimetable() {
  For each section:
    For each assignment:
      - Get weekly_hours from assignment
      - If type = "lab":
          Create weekly_hours/2 lab sessions (2 hours each)
      - If type = "theory":
          Create weekly_hours theory sessions (1 hour each)
    
    Place sessions in timetable:
      - Labs: In continuous 2-hour blocks (slots 0-1, 2-3, or 4-5)
      - Theory: In individual slots
      - Constraints:
          * No same subject on same day
          * Only one lab per day
          * Friday last period (slot 5) kept free
          * No faculty conflicts across departments
}
```

**Example Generation**:
```
Subject: TOC, weekly_hours: 3, type: theory
→ Creates 3 sessions: [TOC, TOC, TOC]
→ Places in slots: Tuesday-Slot0, Wednesday-Slot2, Thursday-Slot4

Subject: ML Lab, weekly_hours: 2, type: lab
→ Creates 1 session: [ML Lab (2 hours)]
→ Places in continuous slots: Tuesday-Slot2-3 (11:15-13:15)
```

#### Generated Timetable Structure:
```javascript
{
  "A": {  // Section A
    "Tuesday": {
      0: { subject_code: "TOC", faculty_name: "Dr. John Smith", type: "theory" },
      1: null,
      2: { subject_code: "ML Lab", faculty_name: "Dr. Bob Wilson", type: "lab" },
      3: { subject_code: "ML Lab", faculty_name: "Dr. Bob Wilson", type: "lab" },
      4: { subject_code: "CNS", faculty_name: "Prof. Jane Doe", type: "theory" },
      5: null
    },
    "Wednesday": {
      0: null,
      1: { subject_code: "CNS", faculty_name: "Prof. Jane Doe", type: "theory" },
      2: { subject_code: "TOC", faculty_name: "Dr. John Smith", type: "theory" },
      ...
    },
    ...
  }
}
```

#### Display:
```
Timetable cells populated with:
┌─────────────┐
│    TOC      │  ← Subject Code
│    DJS      │  ← Faculty Initials
└─────────────┘
```

---

### **Phase 6: Manual Editing**
**File**: `enhanced.htm` (Edit Mode)

#### Inputs:
- Click "✏️ Edit" button to enable edit mode
- Click any timetable cell

#### Process:
```javascript
editCell(cell) {
  1. Cell becomes editable with input fields:
     - Subject input field
     - Faculty input field
     - Clear (×) button
  
  2. User enters/modifies:
     - Subject: "TOC"
     - Faculty: "Dr. John Smith"
  
  3. Press Enter or click outside to save
  
  4. Cell updates with:
     - Subject code displayed
     - Faculty initials displayed
     - data-subject="TOC" attribute
     - data-faculty="Dr. John Smith" attribute
}
```

#### Subject Table Auto-Update:
```javascript
updateSubjectTableFromTimetable() {
  1. Scan all timetable cells
  2. Extract unique subjects
  3. Update subject table rows with:
     - SUB CODE: "TOC"
     - SUBJECT TITLE: "Theory of Computation"
     - SUB IN SHORT: "TOC"
     - FACULTY: "Dr. John Smith"
     - FACULTY INITIALS: "DJS"
}
```

---

### **Phase 7: Saving to Database**
**File**: `enhanced.htm`

#### Inputs:
- Click "💾 Save" button
- Current timetable state from UI

#### Process:
```javascript
saveTimetable() {
  1. Extract current timetable from UI cells
  2. Validate weekly hours match database
  3. For each cell with data:
     - Create timetable entry
  4. Clear existing entries for this section
  5. Insert new entries to Supabase
}
```

#### Storage:
**Supabase Table**: `timetables`
```sql
{
  id: auto-generated,
  department: "ISE",
  section: "A",
  day: "Tuesday",
  time_slot: 0,
  subject_code: "TOC",
  subject_name: "Theory of Computation",
  faculty_name: "Dr. John Smith",
  room: "Room-105",
  academic_year: "2024-25",
  semester: "5",
  year: "3"
}
```

**One entry per slot**, so for a complete timetable:
- 5 days × 6 slots = 30 entries per section
- If 3 sections (A, B, C) = 90 entries total

---

## 📊 Database Schema

### **1. subjects**
```sql
CREATE TABLE subjects (
  id SERIAL PRIMARY KEY,
  department VARCHAR(50),
  name VARCHAR(200),
  code VARCHAR(20),
  credits INTEGER,
  type VARCHAR(20),  -- 'theory' or 'lab'
  weekly_hours INTEGER,  -- KEY: Hours per week
  academic_year VARCHAR(20),
  year INTEGER,
  semester INTEGER
);
```

### **2. faculty**
```sql
CREATE TABLE faculty (
  id SERIAL PRIMARY KEY,
  department VARCHAR(50),
  name VARCHAR(200),
  initials VARCHAR(20),
  designation VARCHAR(100)
);
```

### **3. timetables**
```sql
CREATE TABLE timetables (
  id SERIAL PRIMARY KEY,
  department VARCHAR(50),
  section VARCHAR(10),
  day VARCHAR(20),
  time_slot INTEGER,  -- 0-5
  subject_code VARCHAR(20),
  subject_name VARCHAR(200),
  faculty_name VARCHAR(200),
  room VARCHAR(50),
  academic_year VARCHAR(20),
  semester VARCHAR(10),
  year VARCHAR(10)
);
```

### **4. users**
```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  department VARCHAR(50),
  recruiter_name VARCHAR(200),
  password VARCHAR(200)
);
```

---

## 🎯 Key Constraints & Rules

### **1. Weekly Hours Constraint**
```
Input: weekly_hours = 3 (from subjects table)
Output: Exactly 3 slots in timetable for this subject

Example:
- TOC with weekly_hours=3 → Appears in 3 different slots
- ML Lab with weekly_hours=2 → Appears in 1 continuous 2-hour block
```

### **2. Lab Placement Rules**
```
- Labs must be in continuous 2-hour blocks
- Allowed slot groups:
  * Slots 0-1 (09:00-11:00) - Before tea break
  * Slots 2-3 (11:15-13:15) - After tea break
  * Slots 4-5 (14:00-16:00) - After lunch
- Only ONE lab per day
- No labs on Friday (kept lighter)
```

### **3. Theory Placement Rules**
```
- Individual 1-hour slots
- No same subject repeated on same day
- Friday slot 5 (last period) kept free
```

### **4. Faculty Clash Prevention**
```
- Check against existing timetables in Supabase
- Prevent faculty from being in two places at same time
- Cross-department checking
```

---

## 📈 Example Complete Flow

### **Input Data**:
```
Department: ISE
Semester: 5
Section: A

Subjects:
1. TOC (Theory, 3 hours/week)
2. CNS (Theory, 4 hours/week)
3. ST (Theory, 3 hours/week)
4. ML Lab (Lab, 2 hours/week)
5. CNS Lab (Lab, 2 hours/week)

Total: 14 hours/week
```

### **Generation Process**:
```
Step 1: Create sessions
- TOC: [TOC, TOC, TOC] (3 sessions)
- CNS: [CNS, CNS, CNS, CNS] (4 sessions)
- ST: [ST, ST, ST] (3 sessions)
- ML Lab: [ML Lab (2hr)] (1 session)
- CNS Lab: [CNS Lab (2hr)] (1 session)

Total: 14 sessions to place

Step 2: Place labs first
- ML Lab → Tuesday slots 2-3
- CNS Lab → Wednesday slots 4-5

Step 3: Place theory subjects
- TOC → Tuesday slot 0, Thursday slot 1, Friday slot 2
- CNS → Tuesday slot 4, Wednesday slot 0, Thursday slot 3, Friday slot 3
- ST → Wednesday slot 2, Thursday slot 4, Friday slot 4

Step 4: Verify
- Friday slot 5 = FREE ✓
- All weekly hours matched ✓
- No subject repeated on same day ✓
- Only one lab per day ✓
```

### **Final Timetable**:
```
         Slot0   Slot1   Slot2   Slot3   Slot4   Slot5
Tuesday  TOC     -       ML Lab  ML Lab  CNS     -
Wed      CNS     -       ST      -       CNS Lab CNS Lab
Thu      -       TOC     -       CNS     ST      -
Fri      -       -       TOC     CNS     ST      FREE
Sat      -       -       -       -       -       -
```

### **Database Entries** (30 total):
```sql
INSERT INTO timetables VALUES
  ('ISE', 'A', 'Tuesday', 0, 'TOC', 'Theory of Computation', 'Dr. John Smith', 'Room-105', '2024-25', '5', '3'),
  ('ISE', 'A', 'Tuesday', 2, 'ML Lab', 'ML Lab', 'Dr. Bob Wilson', 'Lab-3', '2024-25', '5', '3'),
  ('ISE', 'A', 'Tuesday', 3, 'ML Lab', 'ML Lab', 'Dr. Bob Wilson', 'Lab-3', '2024-25', '5', '3'),
  ... (27 more entries)
```

---

## 🔧 System Features

### **1. Genetic Algorithm (Python)**
- File: `genetic_timetable.py`
- Population: 50 individuals
- Generations: 150
- Fitness scoring based on constraints
- Automatic optimization

### **2. Manual Editing**
- Click cells to edit
- Real-time updates
- Subject table auto-sync

### **3. Smart Swap**
- Swap two periods
- Automatic clash detection
- Alternative slot suggestions

### **4. Export Options**
- PDF export with MIT Mysore format
- WhatsApp sharing
- Database persistence

### **5. Vault System**
- Department-specific storage
- View all saved timetables
- Download and delete options

---

## 📝 Summary

**The system takes**:
1. Subjects with weekly hours from database
2. Faculty assignments per section
3. Institutional constraints

**And produces**:
1. Optimized timetable respecting all rules
2. Exactly matching weekly hours
3. Proper lab placement
4. No faculty conflicts
5. Editable and saveable results

**Key Innovation**: Uses `weekly_hours` from database to determine exact number of slots each subject needs, ensuring accurate timetable generation.

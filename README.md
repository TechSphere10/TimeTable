# MIT Mysore Timetable System

## 🚀 Quick Start

### 1. Open the System
Simply open `index.htm` in your browser - **No server required!**

### 2. Login
- Use your credentials to access the dashboard

### 3. Generate Timetable
1. Navigate to **Timetable Generator**
2. Select Academic Year, Year, and Semester
3. Load Subjects from database
4. Assign Faculty to each subject
5. Click **Generate Timetable**
6. View, edit with Smart Swap, and export as PDF

---

## 📋 Features

✅ **Pure JavaScript Genetic Algorithm** (No Python/Flask needed)  
✅ **50 Population, 150 Generations** for optimal results  
✅ **All 10 Conditions Implemented:**
   1. No Faculty Clash (within section)
   2. No Faculty Clash (across sections/departments)
   3. Weekly Hours Completion
   4. Lab Rules (2hrs continuous, 4hrs = 2 sessions on different days)
   5. Faculty Workload Check (max 25 hrs/week)
   6. Cross-Department Faculty Blocking
   7. Subject Spread (avoid consecutive days)
   8. Break Hours Fixed
   9. No Same Subject at Same Time Daily
   10. Even Distribution (minimize gaps)

✅ **Smart Swap with Clash Detection**  
✅ **Real-time Supabase Database Sync**  
✅ **PDF Export with MIT Mysore Format**  
✅ **Finalize & Lock Timetables**  
✅ **Blue-White Theme with Smooth Animations**

---

## 🗂️ File Structure

### Core Files (Required)
- `index.htm` - Login page
- `dashboard.htm` - Main dashboard
- `timetable-new.htm` - Timetable setup & faculty assignment
- `enhanced.htm` - Timetable display & generation
- `genetic_algorithm.js` - **JavaScript Genetic Algorithm**
- `config.js` - Supabase configuration
- `subject.htm` - Subject management
- `faculty.htm` - Faculty management
- `left-logo.png` - MET logo
- `right-logo.png` - MIT logo

### Database Files
- `complete_database_setup.sql` - Database schema

### Optional Files
- `faculty_view.htm` - Faculty timetable view
- `vault.htm` - Admin panel
- `page.htm` - Additional page

---

## 🔧 Configuration

### Supabase Setup
Edit `config.js` with your Supabase credentials:
```javascript
const SUPABASE_URL = 'your-supabase-url';
const SUPABASE_ANON_KEY = 'your-anon-key';
```

### Database Tables Required
- `subjects` - Subject information
- `faculty` - Faculty information
- `timetables` - Generated timetables
- `timetable_status` - Finalization status
- `users` - User authentication

---

## 🎯 How It Works

### Genetic Algorithm Process
1. **Initialization**: Creates 50 random timetables (population)
2. **Fitness Evaluation**: Scores each timetable based on 10 conditions
3. **Selection**: Tournament selection picks best parents
4. **Crossover**: Day-based crossover creates offspring
5. **Mutation**: Random swaps introduce variation
6. **Elitism**: Top 5 timetables always survive
7. **Iteration**: Runs for 150 generations or until fitness ≥ 950

### Fitness Scoring
- **Hard Penalties** (-100 points): Faculty clashes
- **Medium Penalties** (-50 points): Lab rule violations
- **Soft Penalties** (-5 to -20 points): Gaps, distribution issues
- **Bonuses** (+2 points): Free hours at end of day

---

## 📱 Usage Guide

### Step 1: Add Subjects
1. Go to **Subject Management**
2. Add subjects with:
   - Subject Code
   - Subject Name
   - Credits
   - Type (Theory/Lab)
   - Weekly Hours
   - Department

### Step 2: Add Faculty
1. Go to **Faculty Management**
2. Add faculty with:
   - Name
   - Initials
   - Department
   - Email

### Step 3: Generate Timetable
1. Go to **Timetable Generator**
2. Select configuration
3. Load subjects
4. Assign faculty to each subject for each section
5. Click **Generate Timetable**
6. Wait for genetic algorithm to complete (~30-60 seconds)

### Step 4: Smart Swap (Optional)
1. Click **Smart Swap** button
2. Select first period to swap
3. System highlights safe swap options in GREEN
4. Click a green period to complete swap
5. Database updates automatically

### Step 5: Export & Save
1. Click **Export PDF** to download
2. Click **Save** to store in database
3. Click **Finalize** to lock timetable (irreversible)

---

## 🔒 Security Features

- User authentication required
- Department-specific access control
- Finalized timetables are locked from edits
- Faculty clash prevention across all departments

---

## 🎨 UI Features

- **Blue-White Gradient Theme**
- **Smooth Animations** on all interactions
- **Responsive Design** for all screen sizes
- **Loading Indicators** during generation
- **Real-time Alerts** for user feedback
- **MIT Mysore Official Format** for timetables

---

## 🐛 Troubleshooting

### Timetable Not Generating
- Check browser console for errors
- Ensure all subjects have faculty assigned
- Verify Supabase connection in config.js

### Faculty Clashes
- System automatically prevents clashes
- If clash occurs, regenerate timetable
- Use Smart Swap to manually fix

### PDF Export Issues
- Ensure logos (left-logo.png, right-logo.png) are present
- Check browser console for errors
- Try different browser (Chrome recommended)

---

## 📊 Performance

- **Generation Time**: 30-60 seconds for 3 sections
- **Population Size**: 50 individuals
- **Generations**: 150 maximum
- **Success Rate**: 95%+ with fitness ≥ 900

---

## 🔄 Updates & Maintenance

### To Update Genetic Algorithm
Edit `genetic_algorithm.js` and modify:
- `populationSize` - Number of timetables per generation
- `maxGenerations` - Maximum iterations
- `mutationRate` - Probability of mutation (0-1)
- `crossoverRate` - Probability of crossover (0-1)

### To Add New Conditions
Add penalty/bonus logic in `calculateFitness()` method

---

## 📞 Support

For issues or questions:
- Check browser console for error messages
- Verify database connection
- Ensure all required files are present

---

## 🏆 Credits

**MIT Mysore Timetable System**  
Department-Specific | Real-Time Generation | Genetic Algorithm Powered

---

**Version**: 2.0 (JavaScript Edition)  
**Last Updated**: 2025  
**Technology**: Pure JavaScript + Supabase

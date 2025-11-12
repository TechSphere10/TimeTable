# Setup Instructions for Python Genetic Algorithm Backend

## 🚀 Quick Start

### Step 1: Install Python Dependencies
Open Command Prompt in the project folder and run:
```bash
pip install -r requirements.txt
```

This will install:
- Flask (web server)
- Flask-CORS (cross-origin requests)
- Supabase (database connection)

### Step 2: Start the Backend Server

**Option A: Using Batch File (Easiest)**
1. Double-click `START_SERVER.bat`
2. Wait for message: "Running on http://127.0.0.1:5000"

**Option B: Manual Start**
```bash
python flask_server.py
```

### Step 3: Use the System
1. Open `index.htm` in your browser
2. Login with your department
3. Navigate to timetable generation
4. Click "🧬 Generate GA" button
5. The system will call the Python backend automatically

---

## 📋 How It Works

### Data Flow:
```
enhanced.htm (Browser)
    ↓ HTTP POST Request
Flask Server (Python)
    ↓ Calls
genetic_timetable.py (Genetic Algorithm)
    ↓ Reads/Writes
Supabase Database
    ↓ Returns
Flask Server
    ↓ HTTP Response
enhanced.htm (Displays Timetable)
```

### API Endpoint:
- **URL**: `http://127.0.0.1:5000/generate`
- **Method**: POST
- **Input**: JSON with department, sections, assignments
- **Output**: JSON with generated timetables

### Example Request:
```json
{
  "department": "ISE",
  "semester": "5",
  "year": "3",
  "academic_year": "2024-25",
  "sections": [
    {
      "name": "A",
      "assignments": [
        {
          "subject": "TOC",
          "faculty": "Dr. John Smith",
          "type": "theory",
          "weekly_hours": 3
        }
      ]
    }
  ]
}
```

### Example Response:
```json
{
  "A": {
    "Tuesday": {
      "0": {
        "subject_code": "TOC",
        "faculty_name": "Dr. John Smith",
        "type": "theory"
      }
    }
  }
}
```

---

## 🔧 Troubleshooting

### Error: "Cannot connect to Python backend"
**Solution**: Make sure the Flask server is running
1. Open Command Prompt
2. Run: `python flask_server.py`
3. Look for: "Running on http://127.0.0.1:5000"

### Error: "Module not found"
**Solution**: Install dependencies
```bash
pip install flask flask-cors supabase
```

### Error: "Port 5000 already in use"
**Solution**: Change port in `flask_server.py`
```python
app.run(debug=True, port=5001)  # Change to 5001
```
Then update `enhanced.htm`:
```javascript
fetch('http://127.0.0.1:5001/generate', ...)  // Change to 5001
```

### Server Not Starting
**Check Python Installation**:
```bash
python --version
```
Should show Python 3.7 or higher

---

## 🎯 Features of Python GA

### Genetic Algorithm Parameters:
- **Population Size**: 50 individuals
- **Generations**: 150 iterations
- **Mutation Rate**: 10%
- **Crossover Rate**: 85%

### Constraints Enforced:
1. ✅ Exact weekly hours from database
2. ✅ Labs in continuous 2-hour blocks
3. ✅ Only one lab per day
4. ✅ No same subject on same day
5. ✅ Friday last period free
6. ✅ Faculty clash prevention across departments

### Fitness Function:
- Faculty conflicts: -200 points
- Same day repeats: -100 points
- Multiple labs per day: -150 points
- Lab continuity: +50 points
- Weekly hours match: +50 points
- Friday last period free: +50 points

---

## 📊 Testing the Backend

### Test Server Health:
Open browser and go to:
```
http://127.0.0.1:5000/health
```

Should return:
```json
{
  "status": "running",
  "message": "Flask server is active"
}
```

### Test Generation (Using curl):
```bash
curl -X POST http://127.0.0.1:5000/generate ^
  -H "Content-Type: application/json" ^
  -d "{\"department\":\"ISE\",\"sections\":[{\"name\":\"A\",\"assignments\":[]}]}"
```

---

## 🔒 Security Notes

- Server runs on localhost only (127.0.0.1)
- Not accessible from other computers
- For production, use proper authentication
- Keep Supabase keys secure

---

## 📝 File Structure

```
TIMETABLE1/
├── flask_server.py          ← Flask backend server
├── genetic_timetable.py     ← Genetic algorithm implementation
├── enhanced.htm             ← Frontend (calls backend)
├── requirements.txt         ← Python dependencies
├── START_SERVER.bat         ← Easy server start
└── SETUP_INSTRUCTIONS.md    ← This file
```

---

## ✅ Verification Checklist

Before using the system:
- [ ] Python 3.7+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Flask server running (`python flask_server.py`)
- [ ] Server health check passes (`http://127.0.0.1:5000/health`)
- [ ] Supabase credentials configured in `genetic_timetable.py`
- [ ] Database tables created (subjects, faculty, timetables)

---

## 🆘 Support

If you encounter issues:
1. Check server is running
2. Check browser console for errors (F12)
3. Check server terminal for error messages
4. Verify database connection
5. Ensure all dependencies are installed

---

**System Ready!** 🎉

Start the server with `START_SERVER.bat` and begin generating timetables!

# Automatic Timetable Generator using AI

An intelligent timetable generation system that uses genetic algorithms to create optimal class schedules while managing subjects, faculty, and constraints.

## Features

- **Subject Management**: Add subjects with credits, type (theory/lab/MCQ/free), and weekly hours
- **Faculty Management**: Manage faculty with designations (Professor, Assistant Professor, Lab Assistant, etc.)
- **AI-Powered Generation**: Uses genetic algorithm to generate optimal timetables
- **Supabase Integration**: Cloud database for data persistence
- **Real-time Updates**: All changes are automatically saved to the database
- **Multi-Department Support**: Supports multiple departments (ISE, CSE, ECE, etc.)

## Setup Instructions

### 1. Supabase Database Setup

1. Go to [Supabase](https://supabase.com) and create a new project
2. In the SQL Editor, run the contents of `database_setup.sql`
3. Your database tables will be created automatically

### 2. Frontend Setup

1. Open `index.htm` or `page.htm` in a web browser
2. The frontend uses CDN links, so no additional setup is required
3. Make sure `supabase-config.js` has the correct URL and API key

### 3. Python Backend Setup

1. Install Python 3.8 or higher
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the API server:
   ```bash
   python api_server.py
   ```
4. The server will start on `http://localhost:5000`

## Usage Guide

### Subject Database

1. Navigate to **Subject Database** from the main page
2. Select Academic Year, Year, and Semester
3. Add subjects with:
   - Subject name
   - Credits (1-6)
   - Type (Theory/Lab/MCQ/Free)
   - Weekly hours (1-10)
4. All data is automatically saved to Supabase

### Faculty Management

1. Navigate to **Faculty Core** from the main page
2. Add faculty members with:
   - Full name
   - Initials (used in timetable display)
   - Designation (Professor, Assistant Professor, etc.)
   - Contact information (optional)
3. Edit or delete faculty as needed

### Timetable Generation

1. Ensure you have subjects and faculty added for your department
2. Use the Python API to generate timetables:
   ```python
   from timetable_generator import TimetableGenerator
   
   generator = TimetableGenerator('ISE')
   result = generator.generate_timetable('2024-25', 3, 5)
   ```

## API Endpoints

- `POST /api/generate-timetable` - Generate timetable
- `GET /api/health` - Health check
- `GET /api/departments` - Get available departments

### Generate Timetable Request

```json
{
  "department": "ISE",
  "academic_year": "2024-25",
  "year": 3,
  "semester": 5
}
```

## Database Schema

### Subjects Table
- `id` - Primary key
- `department` - Department code (ISE, CSE, etc.)
- `academic_year` - Academic year (2024-25)
- `year` - Year (1-4)
- `semester` - Semester (1-8)
- `name` - Subject name
- `credits` - Credit hours (1-6)
- `type` - Subject type (theory/lab/mcq/free)
- `weekly_hours` - Hours per week (1-10)

### Faculty Table
- `id` - Primary key
- `department` - Department code
- `name` - Full name
- `initials` - Short name for timetable
- `designation` - Faculty designation
- `email` - Email address (optional)
- `phone` - Phone number (optional)

### Timetables Table
- `id` - Primary key
- `department` - Department code
- `academic_year` - Academic year
- `year` - Year
- `semester` - Semester
- `timetable_data` - Generated timetable (JSON)
- `fitness_score` - Algorithm fitness score

## Genetic Algorithm Details

The timetable generation uses a genetic algorithm with:

- **Population Size**: 50 chromosomes
- **Generations**: 100 maximum
- **Crossover Rate**: 80%
- **Mutation Rate**: 10%

### Fitness Function

The algorithm optimizes for:
- No faculty conflicts (same faculty, same time)
- Consecutive lab sessions (2-hour labs)
- Preference for morning theory classes
- Avoiding last period assignments

### Constraints

- Faculty cannot be in two places at once
- Lab sessions should be consecutive
- Maximum 7 periods per day
- 5 working days (Monday to Friday)

## File Structure

```
TIMETABLE-main/
├── index.htm              # Login/Registration page
├── page.htm               # Main navigation page
├── subject.htm            # Subject management
├── faculty.htm            # Faculty management
├── timetable-new.htm      # Timetable display
├── supabase-config.js     # Supabase configuration
├── timetable_generator.py # Genetic algorithm
├── api_server.py          # Flask API server
├── requirements.txt       # Python dependencies
├── database_setup.sql     # Database schema
└── README.md             # This file
```

## Troubleshooting

### Common Issues

1. **Supabase Connection Error**
   - Check your URL and API key in `supabase-config.js`
   - Ensure RLS policies are set correctly

2. **No Timetable Generated**
   - Make sure you have both subjects and faculty in the database
   - Check that the department, year, and semester have data

3. **Python Dependencies**
   - Use `pip install -r requirements.txt`
   - Ensure Python 3.8+ is installed

4. **CORS Issues**
   - The Flask server includes CORS headers
   - Make sure the API server is running on port 5000

## Future Enhancements

- Web interface for timetable generation
- Advanced constraint handling
- Room allocation
- Teacher preferences
- Conflict resolution UI
- Export to PDF/Excel
- Mobile responsive design

## Support

For issues and questions:
1. Check the troubleshooting section
2. Verify database setup
3. Ensure all dependencies are installed
4. Check browser console for errors

## License

This project is for educational purposes. Modify and use as needed for your institution.
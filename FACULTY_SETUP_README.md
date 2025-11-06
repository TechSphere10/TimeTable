# Faculty Management Setup Instructions

## Supabase Database Setup

To set up the faculty management system, you need to create the required table in your Supabase database.

### Steps:

1. **Login to Supabase Dashboard**
   - Go to https://supabase.com
   - Login to your account
   - Select your project: `bkmzyhroignpjebfpqug`

2. **Create the Required Tables**
   - Go to the SQL Editor in your Supabase dashboard
   - First, copy and paste the contents of `supabase_setup.sql` (for faculty table)
   - Click "Run" to execute the SQL commands
   - Then, copy and paste the contents of `subjects_table_setup.sql` (for subjects table)
   - Click "Run" to execute the SQL commands

3. **Verify Table Creation**
   - Go to the Table Editor
   - You should see two new tables:
     - `faculty` table with columns: id, name, initials, type, department, created_at, updated_at
     - `subjects` table with columns: id, department, academic_year, year, semester, name, credits, type, created_at, updated_at

## Features Implemented

### Faculty Management Page (`faculty.htm`)
- **Department-specific**: Only shows faculty from the logged-in department
- **Add Faculty**: Button to add new faculty members
- **Edit Faculty**: Edit existing faculty information
- **Delete Faculty**: Remove faculty members with confirmation
- **Faculty Types**: Professor, Associate Professor, Assistant Professor, Faculty, Lab Assistant

### Data Storage
- All faculty data is stored in Supabase
- Department-based filtering ensures data isolation
- Automatic timestamps for created_at and updated_at

### User Interface
- Responsive grid layout for faculty cards
- Modal popup for add/edit operations
- Consistent styling with the existing application
- Back button to return to main menu

## Usage

1. **Access Faculty Management**
   - From the main page (`page.htm`), click "Faculty Management"
   - The page will automatically filter by the current department

2. **Add New Faculty**
   - Click "Add New Faculty" button
   - Fill in the required information:
     - Full Name
     - Initials (will be converted to uppercase)
     - Type (select from dropdown)
   - Click "Save Faculty"

3. **Edit Faculty**
   - Click "Edit" button on any faculty card
   - Modify the information in the popup
   - Click "Save Faculty"

4. **Delete Faculty**
   - Click "Delete" button on any faculty card
   - Confirm the deletion in the popup

## Technical Details

- **Frontend**: HTML, CSS, JavaScript
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Uses Supabase anon key (consider implementing proper auth later)
- **Styling**: Consistent with existing application theme

## Security Notes

- Currently using anonymous access for simplicity
- Consider implementing proper authentication for production use
- Row Level Security (RLS) is enabled but set to allow all operations
- You may want to restrict policies based on user roles in production

## Features Implemented

### Subject Database Page (`subject.htm`) - Updated with Supabase
- **Department-specific**: Only shows subjects from the logged-in department
- **Add Subject**: Add subjects with name, credits, and type
- **Save Database**: Save subjects to Supabase (with localStorage backup)
- **View Database**: View all saved subjects by academic year from Supabase
- **Clear All**: Clear all subjects with enhanced warning confirmation
- **Export Data**: Export subjects data as JSON
- **Subject Types**: Theory, Lab, MCQ, Free
- **Removed**: View Timetables button (as requested)

### Enhanced Data Storage
- Primary storage in Supabase database
- Department-based filtering ensures data isolation
- Automatic timestamps for created_at and updated_at
- Fallback to localStorage if Supabase is unavailable
- Real-time sync between Supabase and local storage

## Usage

### Subject Database
1. **Access Subject Database**
   - From the main page (`page.htm`), click "Subject Database"
   - The page will show subjects for the current department only

2. **Add Subjects**
   - Enter Academic Year (e.g., 2024-25)
   - Select Year (1-4) and Semester
   - Enter subject name, credits, and type
   - Click "Add Subject"

3. **Save to Database**
   - After adding subjects, click "Save Database"
   - Data will be saved to Supabase with localStorage backup

4. **View Saved Data**
   - Click "View Database" to see all saved subjects
   - Data is organized by academic year and semester
   - Use "Use" button to load subjects for editing
   - Use "Delete" button to remove specific semester data

5. **Clear All Data**
   - Click "Clear All" to delete all department data
   - Enhanced warning message appears before deletion
   - Clears both Supabase and localStorage data

## Next Steps

After setting up both tables, you can:
1. Test the faculty management functionality
2. Test the subject database functionality
3. Add more faculty types or subject types if needed
4. Implement proper user authentication
5. Add more fields to records (email, phone, etc.)
6. Proceed with the genetic algorithm for timetable generation

## Important Notes

- **Department Isolation**: Both faculty and subject data are filtered by department
- **Header Display**: Department name appears in headers (not default "ISE")
- **Data Persistence**: All data is stored in Supabase with localStorage backup
- **Error Handling**: Graceful fallback to localStorage if Supabase is unavailable
- **Warning Messages**: Enhanced confirmation dialogs for data deletion
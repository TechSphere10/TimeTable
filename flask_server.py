from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from genetic_algorithm import TimetableGA # Import the new GA class
import os
import traceback
from supabase import create_client, Client


app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

@app.route('/')
def index():
    return send_from_directory('.', 'index.htm')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

# --- Supabase Client ---
# It's better to initialize this once.
SUPABASE_URL = 'https://bkmzyhroignpjebfpqug.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJrbXp5aHJvaWducGplYmZwcXVnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzQyMDU0NSwiZXhwIjoyMDcyOTk2NTQ1fQ.b-pB33oVzW2s1yYq_G9E9iP-z1j3tGg_H0w2w_i1XbA' # Use the service_role key for backend operations
supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.route('/generate', methods=['POST'])
def generate_timetable():
    try:
        print("\n" + "="*60)
        print("TIMETABLE GENERATION REQUEST RECEIVED")
        print("="*60)
        
        input_data = request.json
        if not input_data:
            print("ERROR: No data provided in request")
            return jsonify({"error": "No data provided"}), 400

        department = input_data.get('department', 'ISE')
        semester = input_data.get('semester', '5')
        academic_year = input_data.get('academicYear', '2024-25')
        year = input_data.get('year', '3')

        print(f"Department: {department}")
        print(f"Academic Year: {academic_year}")
        print(f"Year: {year}, Semester: {semester}")

        sections = input_data.get('sections', [])
        if not sections:
            print("ERROR: No sections provided")
            return jsonify({"error": "No sections provided"}), 400

        print(f"Number of sections: {len(sections)}")

        # --- Fetch existing faculty schedules for clash detection ---
        # This is crucial for ensuring faculty aren't double-booked across departments
        # OPTIMIZATION: Fetch only timetables for the current academic year to avoid old data clashes.
        all_faculty_schedules = {}
        res = supabase_client.from_('timetables') \
            .select('faculty_name, day, time_slot') \
            .eq('academic_year', academic_year) \
            .execute()
        if res.data:
            for entry in res.data:
                all_faculty_schedules.setdefault(entry['faculty_name'], {}).setdefault(entry['day'], {})[entry['time_slot']] = True
        print(f"Loaded {len(all_faculty_schedules)} existing faculty schedules for clash detection.")

        # --- GA Configuration ---
        ga_config = {
            'days': ['Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
            'slots_per_day': 6,
            'lab_slots': [0, 4] # Labs can start at 9am (slot 0) or 2pm (slot 4)
        }

        results = {}
        all_new_entries_for_db = []

        for section_data in sections:
            section_name = section_data.get('name', 'A')
            assignments = section_data.get('assignments', [])

            print(f"\nProcessing Section {section_name}:")
            print(f"  - Number of subjects: {len(assignments)}")

            print(f"\nRunning genetic algorithm for Section {section_name}...")
            ga = TimetableGA(assignments, all_faculty_schedules, ga_config)
            timetable = ga.run()

            # Prepare data for batch database insert
            for day, slots in timetable.items():
                for slot_idx, period in slots.items():
                    all_new_entries_for_db.append({
                        'department': department, 'academic_year': academic_year, 'year': year,
                        'semester': semester, 'section': section_name, 'day': day,
                        'time_slot': slot_idx, 'subject_code': period['subject_code'],
                        'faculty_name': period['faculty_name'], 'room': f"Room-{section_name}01"
                    })
                    # Update the global schedule immediately for the next section's clash detection
                    all_faculty_schedules.setdefault(period['faculty_name'], {}).setdefault(day, {})[slot_idx] = True

            results[section_name] = timetable
            print(f"✓ Section {section_name} completed successfully")

        # --- Database Operation: Perform a single batch update ---
        print("\nSaving all generated timetables to Supabase...")
        # 1. Delete all old entries for this entire department/semester
        supabase_client.from_('timetables').delete().match({
            'department': department, 'academic_year': academic_year, 'semester': semester
        }).execute()
        print(f"  - Cleared old records for {department} Sem {semester}.")

        # 2. Insert all new entries at once
        if all_new_entries_for_db:
            insert_res = supabase_client.from_('timetables').insert(all_new_entries_for_db).execute()
            if insert_res.data:
                print(f"  - Successfully saved {len(insert_res.data)} new timetable slots.")

        print(f"\n" + "="*60)
        print(f"SUCCESS: Generated timetables for {len(results)} sections")
        print("="*60 + "\n")
        # Return a structured, successful response
        return jsonify({"status": "success", "timetables": results})

    except Exception as e:
        print(f"\n" + "="*60)
        print(f"ERROR: {str(e)}")
        print("="*60)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "running", "message": "Flask server is active"})

if __name__ == '__main__':
    print("Starting Flask server on http://127.0.0.1:5000")
    print("Press Ctrl+C to stop.")
    app.run(debug=True, port=5000)

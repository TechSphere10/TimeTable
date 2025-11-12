from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from genetic_timetable import SupabaseTimetableGA

app = Flask(__name__)
CORS(app)

@app.route('/generate', methods=['POST'])
def generate_timetable():
    try:
        input_data = request.json
        print(f"Received request for {input_data.get('department')} Semester {input_data.get('semester')}")
        
        ga = SupabaseTimetableGA()
        results = {}
        
        for section_data in input_data.get('sections', []):
            section_name = section_data.get('name', 'A')
            assignments = section_data.get('assignments', [])
            
            print(f"Processing section {section_name} with {len(assignments)} subjects")
            
            # The 'assignments' list from the frontend is passed directly to the GA
            timetable = ga.evolve_section(
                department=input_data.get('department', 'ISE'),
                section=section_name,
                section_data=assignments  # Pass the assignments list directly
            )
            
            # Save to Supabase
            ga.save_to_supabase(
                timetable=timetable,
                section=section_name,
                department=input_data.get('department', 'ISE')
            )
            
            results[section_name] = timetable
        
        print(f"Successfully generated timetables for {len(results)} sections")
        return jsonify(results)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "running", "message": "Flask server is active"})

if __name__ == '__main__':
    print("Starting Flask server on http://127.0.0.1:5000")
    print("Press Ctrl+C to stop")
    app.run(debug=True, port=5000)

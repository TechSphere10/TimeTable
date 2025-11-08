from flask import Flask, request, jsonify
from flask_cors import CORS
from timetable_generator import generate_all_timetables, TimetableGenerator
import json

app = Flask(__name__)
CORS(app)

@app.route('/generate', methods=['POST'])
def generate_timetable():
    try:
        config = request.json
        result = generate_all_timetables(config)
        return jsonify({
            'success': True,
            'message': 'Timetable generated successfully',
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/generate-section', methods=['POST'])
def generate_section_timetable():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing or invalid JSON in request'
            }), 400

        if 'config' not in data:
            return jsonify({
                'success': False,
                'error': 'config is required'
            }), 400

        if 'sectionIndex' not in data:
            return jsonify({
                'success': False,
                'error': 'sectionIndex is required'
            }), 400

        config = data['config']
        section_index = data['sectionIndex']
        
        generator = TimetableGenerator(config)
        if isinstance(data, dict) and 'existingSchedule' in data:
            generator.faculty_schedule = data['existingSchedule']
        
        timetable = generator.generate_timetable(section_index)
        
        return jsonify({
            'success': True,
            'timetable': timetable,
            'facultySchedule': generator.faculty_schedule
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/faculty-schedule', methods=['POST'])
def get_faculty_schedule():
    try:
        # Safely parse JSON; request.get_json(silent=True) returns None instead of raising
        data = request.get_json(silent=True)
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing or invalid JSON in request'
            }), 400

        # Use get to avoid subscripting None and provide clear error if keys are missing
        faculty_name = data.get('facultyName')
        faculty_schedule = data.get('facultySchedule')

        if not faculty_name:
            return jsonify({
                'success': False,
                'error': 'facultyName is required'
            }), 400

        if faculty_schedule is None:
            return jsonify({
                'success': False,
                'error': 'facultySchedule is required'
            }), 400

        generator = TimetableGenerator({'sections': [], 'subjects': [], 'periodsPerDay': 7, 'workingDays': '5'})
        generator.faculty_schedule = faculty_schedule

        schedule = generator.get_faculty_schedule(faculty_name)

        return jsonify({
            'success': True,
            'schedule': schedule
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/check-conflict', methods=['POST'])
def check_conflict():
    try:
        data = request.json
        return jsonify({
            'success': True,
            'hasConflict': False,
            'suggestions': []
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("Starting Timetable Generator API Server...")
    print("Server running on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)

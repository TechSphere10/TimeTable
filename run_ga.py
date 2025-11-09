#!/usr/bin/env python3
import json
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from genetic_timetable import SupabaseTimetableGA

def main():
    try:
        # Read input from stdin
        input_data = json.loads(sys.stdin.read())
        
        # Initialize GA
        ga = SupabaseTimetableGA()
        
        # Process each section
        results = {}
        
        for section_data in input_data.get('sections', []):
            section_name = section_data.get('name', 'A')
            subjects = section_data.get('subjects', {})
            
            # Convert to format expected by GA
            section_assignments = {}
            for subject_code, subject_info in subjects.items():
                section_assignments[subject_code] = subject_info.get('faculty', '')
            
            # Generate timetable for this section
            timetable = ga.evolve_section(
                department=input_data.get('department', 'ISE'),
                section=section_name,
                section_data={'subjects': section_assignments}
            )
            
            # Save to Supabase
            ga.save_to_supabase(
                timetable=timetable,
                section=section_name,
                department=input_data.get('department', 'ISE')
            )
            
            results[section_name] = timetable
        
        # Output results
        print(json.dumps(results))
        
    except Exception as e:
        error_result = {"error": str(e)}
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
"""
Real-Time Genetic Algorithm Backend for Timetable Generation
MIT Mysore - Clash-Free Timetable System
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import copy
from supabase.client import create_client, Client
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Supabase Configuration
SUPABASE_URL = "https://bkmzyhroignpjebfpqug.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJrbXp5aHJvaWducGplYmZwcXVnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc0MjA1NDUsImV4cCI6MjA3Mjk5NjU0NX0.ICE2eYzFZvz0dtNpAa5YlJTZD-idc2J76wn1ZeHwwck"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# GA Parameters
POPULATION_SIZE = 50
GENERATIONS = 150
CROSSOVER_RATE = 0.85
MUTATION_RATE = 0.10
ELITE_SIZE = int(POPULATION_SIZE * 0.3)

# Time Configuration
DAYS = ['Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
SLOTS_PER_DAY = 6
CONTINUOUS_SLOTS = [[0, 1], [2, 3], [4, 5]]  # Lab slots

class TimetableGA:
    def __init__(self, department, semester, year, academic_year, sections_data):
        self.department = department
        self.semester = semester
        self.year = year
        self.academic_year = academic_year
        self.sections_data = sections_data
        self.existing_timetables = []
        self.load_existing_timetables()
        
    def load_existing_timetables(self):
        """Load all existing timetables for clash detection"""
        try:
            response = supabase.table('timetables').select('*').execute()
            self.existing_timetables = response.data if response.data else []
        except Exception as e:
            print(f"Error loading timetables: {e}")
            self.existing_timetables = []
    
    def check_faculty_clash(self, faculty_name, day, slot, exclude_dept=None):
        """Check if faculty has clash at given time"""
        for entry in self.existing_timetables:
            if (entry['faculty_name'] == faculty_name and 
                entry['day'] == day and 
                entry['time_slot'] == slot and
                (exclude_dept is None or entry['department'] != exclude_dept)):
                return True
        return False
    
    def create_chromosome(self, section_data):
        """Create a valid timetable chromosome"""
        chromosome = {}
        for day in DAYS:
            chromosome[day] = [None] * SLOTS_PER_DAY
        
        # Create a list of all individual sessions to be placed
        all_sessions = []
        for assignment in section_data['assignments']:
            hours = assignment.get('weekly_hours', 3)
            if assignment.get('type', 'theory').lower() == 'lab':
                num_sessions = hours // 2
                for _ in range(num_sessions):
                    all_sessions.append({**assignment, 'session_type': 'lab'})
            else:
                for _ in range(hours):
                    all_sessions.append({**assignment, 'session_type': 'theory'})
        
        random.shuffle(all_sessions)
        
        # Place labs first
        for session in all_sessions:
            if session['session_type'] == 'lab':
                placed = False
                attempts = 0
                while not placed and attempts < 50:
                    day = random.choice(DAYS)
                    if day == 'Friday': continue
                    
                    slot_group = random.choice(CONTINUOUS_SLOTS)
                    
                    if all(chromosome[day][s] is None for s in slot_group) and \
                       not self.check_faculty_clash(session['faculty'], day, slot_group[0], self.department):
                        for slot in slot_group:
                            chromosome[day][slot] = session
                        placed = True
                    attempts += 1

        # Place theory
        for session in all_sessions:
            if session['session_type'] == 'theory':
                placed = False
                attempts = 0
                while not placed and attempts < 50:
                    day = random.choice(DAYS)
                    slot = random.randint(0, SLOTS_PER_DAY - 1)
                    
                    if (day == 'Friday' and slot == 5): continue
                    
                    if chromosome[day][slot] is None and \
                       not self.check_faculty_clash(session['faculty'], day, slot, self.department):
                        chromosome[day][slot] = session
                        placed = True
                    attempts += 1
        
        return chromosome
    
    def calculate_fitness(self, chromosome, section_data):
        """Calculate fitness score"""
        score = 1000
        
        # Check faculty clashes
        for day in DAYS:
            for slot in range(SLOTS_PER_DAY):
                if chromosome.get(day, [])[slot]:
                    faculty = chromosome[day][slot]['faculty']
                    if self.check_faculty_clash(faculty, day, slot, self.department):
                        score -= 150
        
        # Check lab continuity
        for day in DAYS:
            for slot_group in CONTINUOUS_SLOTS:
                slots_data = [chromosome[day][s] for s in slot_group]
                if all(s and s.get('type', '').lower() == 'lab' and s['subject'] == slots_data[0]['subject'] for s in slots_data):
                    score += 50
                elif any(s and s.get('type', '').lower() == 'lab' for s in slots_data):
                    score -= 30
        
        # Check weekly hours
        subject_hours = {}
        for day in DAYS:
            for slot in range(SLOTS_PER_DAY):
                if chromosome.get(day, [])[slot]:
                    subj = chromosome[day][slot]['subject']
                    subject_hours[subj] = subject_hours.get(subj, 0) + 1
        
        for assignment in section_data['assignments']:
            expected = assignment.get('weekly_hours', 3)
            actual = subject_hours.get(assignment['subject'], 0)
            if expected != actual:
                score -= abs(expected - actual) * 50 # Heavier penalty
        
        # Friday last period check
        if chromosome['Friday'][5] is not None:
            score -= 30
        
        return max(0, score)
    
    def crossover(self, parent1, parent2):
        """Perform crossover"""
        child = {}
        for day in DAYS:
            if random.random() < 0.5:
                child[day] = copy.deepcopy(parent1[day])
            else:
                child[day] = copy.deepcopy(parent2[day])
        return child
    
    def mutate(self, chromosome):
        """Perform mutation"""
        if random.random() < MUTATION_RATE:
            day1, day2 = random.sample(DAYS, 2)
            slot1 = random.randint(0, SLOTS_PER_DAY - 1)
            slot2 = random.randint(0, SLOTS_PER_DAY - 1)
            
            chromosome[day1][slot1], chromosome[day2][slot2] = chromosome[day2][slot2], chromosome[day1][slot1]
        
        return chromosome
    
    def generate_timetable(self, section_data):
        """Main GA loop"""
        population = [self.create_chromosome(section_data) for _ in range(POPULATION_SIZE)]
        best_chromosome = population[0]
        
        for generation in range(GENERATIONS):
            fitness_scores = [(chromo, self.calculate_fitness(chromo, section_data)) for chromo in population]
            fitness_scores.sort(key=lambda x: x[1], reverse=True)
            best_chromosome = fitness_scores[0][0]
            
            if fitness_scores[0][1] >= 950:
                print(f"Optimal solution found at generation {generation}")
                return best_chromosome
            
            # Selection
            elite = [chromo for chromo, _ in fitness_scores[:ELITE_SIZE]]
            
            # Crossover
            new_population = elite.copy()
            while len(new_population) < POPULATION_SIZE:
                parent1, parent2 = random.sample(elite, 2)
                if random.random() < CROSSOVER_RATE:
                    child = self.crossover(parent1, parent2)
                    child = self.mutate(child)
                    new_population.append(child)
            
            population = new_population
        
        return best_chromosome

@app.route('/generate', methods=['POST'])
def generate_timetable():
    """API endpoint for timetable generation"""
    try:
        data = request.json
        if data is None:
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        department = data.get('department')
        semester = data.get('semester')
        year = data.get('year')
        academic_year = data.get('academic_year')
        sections = data.get('sections')
        
        if not all([department, semester, year, academic_year, sections]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        ga = TimetableGA(department, semester, year, academic_year, sections)
        
        result = {}
        for section_data in sections:
            section_name = section_data.get('name', 'A')
            timetable = ga.generate_timetable(section_data)
            
            # Convert to API format
            formatted_timetable = {}
            for day in DAYS:
                formatted_timetable[day] = {}
                for slot in range(SLOTS_PER_DAY):
                    entry = timetable.get(day, [None]*SLOTS_PER_DAY)[slot]
                    if entry:
                        formatted_timetable[day][slot] = {
                            'subject_code': entry.get('subCode', entry.get('subject', '')),
                            'subject_name': entry.get('subject', ''),
                            'faculty_name': entry.get('faculty', ''),
                            'faculty_initials': entry.get('facultyInitials', ''),
                            'section': section_name,
                            'type': entry.get('type', 'theory'),
                        }
                    else:
                        formatted_timetable[day][slot] = None
            
            result[section_name] = formatted_timetable
            
            # Save to database
            save_to_database(department, semester, year, academic_year, section_name, formatted_timetable)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def save_to_database(department, semester, year, academic_year, section, timetable):
    """Save timetable to Supabase"""
    try:
        # Delete existing
        supabase.table('timetables').delete().eq('department', department).eq('section', section).eq('semester', semester).execute()
        
        # Insert new
        entries = []
        for day in DAYS:
            for slot in range(SLOTS_PER_DAY):
                if timetable[day][slot]:
                    entries.append({
                        'department': department,
                        'academic_year': academic_year,
                        'year': int(year),
                        'semester': int(semester),
                        'section': section,
                        'day': day,
                        'time_slot': slot,
                        'subject_code': timetable[day][slot]['subject_code'],
                        'subject_name': timetable[day][slot]['subject_name'],
                        'faculty_name': timetable[day][slot]['faculty_name']
                    })
        
        if entries:
            supabase.table('timetables').insert(entries).execute()
    
    except Exception as e:
        print(f"Database save error: {e}")

@app.route('/check-clash', methods=['POST'])
def check_clash():
    """Check for faculty clashes"""
    try:
        data = request.json
        if data is None:
            return jsonify({'error': 'Request body must be JSON'}), 400

        faculty_name = data.get('faculty_name')
        day = data.get('day')
        slot = data.get('slot')
        department = data.get('department')

        if not all([faculty_name, day, slot]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        response = supabase.table('timetables').select('*').eq('faculty_name', faculty_name).eq('day', day).eq('time_slot', slot).execute()
        
        clashes = [entry for entry in (response.data or []) if entry.get('department') != department]
        
        return jsonify({'has_clash': len(clashes) > 0, 'clashes': clashes})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

import random
import json
from supabase.client import create_client, Client
import os

SUPABASE_URL = "https://bkmzyhroignpjebfpqug.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJrbXp5aHJvaWducGplYmZwcXVnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc0MjA1NDUsImV4cCI6MjA3Mjk5NjU0NX0.ICE2eYzFZvz0dtNpAa5YlJTZD-idc2J76wn1ZeHwwck"

class RealtimeTimetableGenerator:
    def __init__(self, session_id):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.session_id = session_id
        self.config = self._load_config()
        self.working_days = self._get_working_days()
        self.periods_per_day = int(self.config['periodsPerDay'])
        self.population_size = 100
        self.generations = 300
        self.mutation_rate = 0.3
        
    def _load_config(self):
        """Load configuration from Supabase"""
        response = self.supabase.table('timetable_sessions').select('*').eq('session_id', self.session_id).execute()
        if response.data:
            return response.data[0]['config_data']
        raise Exception("Session not found")
    
    def _get_working_days(self):
        days_config = self.config['workingDays']
        if days_config == '5':
            return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        elif days_config == '6':
            return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        else:
            return ['Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    def _get_existing_faculty_schedule(self, faculty_id):
        """Get existing schedule for a faculty from Supabase"""
        response = self.supabase.table('faculty_schedule').select('*').eq('faculty_id', faculty_id).execute()
        schedule = {}
        for entry in response.data:
            key = f"{entry['day']}_{entry['period']}"
            schedule[key] = entry
        return schedule
    
    def generate_section_timetable(self, section_index):
        """Generate timetable for a specific section"""
        section = self.config['sections'][section_index]
        section_subjects = section['subjectFaculty']
        
        # Initialize population
        population = [self._create_chromosome(section_subjects) for _ in range(self.population_size)]
        
        best_solution = None
        best_fitness = float('-inf')
        
        for generation in range(self.generations):
            fitness_scores = [(chromo, self._fitness(chromo, section_subjects)) for chromo in population]
            fitness_scores.sort(key=lambda x: x[1], reverse=True)
            
            if fitness_scores[0][1] > best_fitness:
                best_fitness = fitness_scores[0][1]
                best_solution = fitness_scores[0][0]
            
            if best_fitness >= 95:
                break
            
            parents = [fs[0] for fs in fitness_scores[:self.population_size//2]]
            offspring = []
            
            while len(offspring) < self.population_size//2:
                parent1, parent2 = random.sample(parents, 2)
                child = self._crossover(parent1, parent2)
                if random.random() < self.mutation_rate:
                    child = self._mutate(child, section_subjects)
                offspring.append(child)
            
            population = parents + offspring
        
        # Save to Supabase
        timetable_data = self._format_timetable(best_solution, section_subjects, section['name'])
        self._save_timetable(timetable_data, section['name'], best_fitness)
        self._save_faculty_schedule(best_solution, section_subjects, section['name'])
        
        return timetable_data
    
    def _create_chromosome(self, section_subjects):
        """Create random timetable chromosome"""
        chromosome = {day: [dict() if i != -1 else None for i in range(self.periods_per_day)] for day in self.working_days}
        
        for subject_info in section_subjects:
            subject = subject_info['subject']
            faculty = subject_info['faculty']
            faculty_id = subject_info['facultyId']
            weekly_hours = subject_info.get('weekly_hours', 3)
            subject_type = subject_info.get('type', 'theory')
            
            # Get existing faculty schedule
            existing_schedule = self._get_existing_faculty_schedule(faculty_id)
            
            slots_assigned = 0
            attempts = 0
            max_attempts = 100
            
            while slots_assigned < weekly_hours and attempts < max_attempts:
                attempts += 1
                day = random.choice(self.working_days)
                
                if subject_type == 'lab' and slots_assigned == 0:
                    # Lab needs 2 consecutive periods
                    period = random.randint(0, self.periods_per_day - 2)
                    slot1 = f"{day}_{period}"
                    slot2 = f"{day}_{period+1}"
                    
                    if (chromosome[day][period] is None and 
                        chromosome[day][period + 1] is None and
                        slot1 not in existing_schedule and 
                        slot2 not in existing_schedule):
                        chromosome[day][period] = {'subject': subject, 'faculty': faculty, 'facultyId': faculty_id}
                        chromosome[day][period + 1] = {'subject': subject, 'faculty': faculty, 'facultyId': faculty_id}
                        slots_assigned += 2
                else:
                    period = random.randint(0, self.periods_per_day - 1)
                    slot = f"{day}_{period}"
                    
                    if chromosome[day][period] is None and slot not in existing_schedule:
                        chromosome[day][period] = {'subject': subject, 'faculty': faculty, 'facultyId': faculty_id}
                        slots_assigned += 1
        
        # Fill remaining with FREE (prefer last period)
        for day in self.working_days:
            if chromosome[day][-1] is None:
                chromosome[day][-1] = {'subject': 'FREE', 'faculty': '', 'facultyId': None}
            for i in range(len(chromosome[day])):
                if chromosome[day][i] is None:
                    chromosome[day][i] = {'subject': 'FREE', 'faculty': '', 'facultyId': None}
        
        return chromosome
    
    def _fitness(self, chromosome, section_subjects):
        """Calculate fitness score"""
        score = 100
        
        # Check subject distribution (weekly hours)
        for subject_info in section_subjects:
            subject = subject_info['subject']
            required_hours = subject_info.get('weekly_hours', 3)
            actual_hours = sum(1 for day in chromosome.values() for slot in day if slot and slot['subject'] == subject)
            score -= abs(actual_hours - required_hours) * 5
        
        # Check lab continuity (2 consecutive periods)
        for subject_info in section_subjects:
            if subject_info.get('type') == 'lab':
                subject = subject_info['subject']
                for day in chromosome.values():
                    for i in range(len(day) - 1):
                        if day[i] and day[i]['subject'] == subject:
                            if not day[i+1] or day[i+1]['subject'] != subject:
                                score -= 10
        
        # Avoid same subject on same day (except labs)
        for subject_info in section_subjects:
            if subject_info.get('type') != 'lab':
                subject = subject_info['subject']
                for day in chromosome.values():
                    count = sum(1 for slot in day if slot and slot['subject'] == subject)
                    if count > 1:
                        score -= 15 * (count - 1)
        
        # Faculty should have at least 1 hour gap (avoid continuous classes)
        for day in chromosome.values():
            for i in range(len(day) - 1):
                if (day[i] and day[i]['subject'] != 'FREE' and 
                    day[i+1] and day[i+1]['subject'] != 'FREE'):
                    if day[i]['facultyId'] == day[i+1]['facultyId']:
                        score -= 8
        
        # Prefer FREE at last period
        for day in chromosome.values():
            if day[-1] and day[-1]['subject'] == 'FREE':
                score += 5
        
        # Check faculty conflicts (cross-department)
        for day_idx, day in enumerate(self.working_days):
            for period_idx, slot in enumerate(chromosome[day]):
                if slot and slot['subject'] != 'FREE':
                    faculty_id = slot['facultyId']
                    existing = self._get_existing_faculty_schedule(faculty_id)
                    time_slot = f"{day}_{period_idx}"
                    if time_slot in existing:
                        score -= 20
        
        return max(0, score)
    
    def _crossover(self, parent1, parent2):
        """Crossover operation"""
        child = {}
        for day in self.working_days:
            child[day] = parent1[day][:] if random.random() < 0.5 else parent2[day][:]
        return child
    
    def _mutate(self, chromosome, section_subjects):
        """Mutation operation"""
        day = random.choice(self.working_days)
        p1, p2 = random.randint(0, self.periods_per_day - 1), random.randint(0, self.periods_per_day - 1)
        chromosome[day][p1], chromosome[day][p2] = chromosome[day][p2], chromosome[day][p1]
        return chromosome
    
    def _format_timetable(self, chromosome, section_subjects, section_name):
        """Format timetable for output"""
        timetable = {'section': section_name, 'schedule': {}}
        
        for day in self.working_days:
            timetable['schedule'][day] = []
            for period_idx, slot in enumerate(chromosome[day]):
                timetable['schedule'][day].append({
                    'period': period_idx + 1,
                    'subject': slot['subject'] if slot else 'FREE',
                    'faculty': slot['faculty'] if slot else '',
                    'facultyId': slot['facultyId'] if slot else None
                })
        
        return timetable
    
    def _save_timetable(self, timetable_data, section_name, fitness_score):
        """Save timetable to Supabase"""
        self.supabase.table('timetables').insert({
            'session_id': self.session_id,
            'department': self.config['department'],
            'academic_year': self.config['academicYear'],
            'year': int(self.config['year']),
            'semester': int(self.config['semester']),
            'section_name': section_name,
            'timetable_data': timetable_data,
            'fitness_score': fitness_score
        }).execute()
    
    def _save_faculty_schedule(self, chromosome, section_subjects, section_name):
        """Save faculty schedule to Supabase"""
        entries = []
        for day in self.working_days:
            for period_idx, slot in enumerate(chromosome[day]):
                if slot and slot['subject'] != 'FREE':
                    entries.append({
                        'session_id': self.session_id,
                        'faculty_id': slot['facultyId'],
                        'faculty_name': slot['faculty'],
                        'department': self.config['department'],
                        'day': day,
                        'period': period_idx,
                        'section_name': section_name,
                        'subject_name': slot['subject'],
                        'academic_year': self.config['academicYear'],
                        'year': int(self.config['year']),
                        'semester': int(self.config['semester'])
                    })
        
        if entries:
            self.supabase.table('faculty_schedule').insert(entries).execute()

def generate_timetable_realtime(session_id, section_index):
    """Main function to generate timetable"""
    generator = RealtimeTimetableGenerator(session_id)
    return generator.generate_section_timetable(section_index)

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2:
        session_id = sys.argv[1]
        section_index = int(sys.argv[2])
        result = generate_timetable_realtime(session_id, section_index)
        print(json.dumps(result))

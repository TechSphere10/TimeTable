import random
import json
import sys
from supabase.client import create_client, Client
from typing import List, Dict, Any, Tuple
import os

class SupabaseTimetableGA:
    def __init__(self):
        self.supabase_url = "https://bkmzyhroignpjebfpqug.supabase.co"
        self.supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJrbXp5aHJvaWducGplYmZwcXVnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc0MjA1NDUsImV4cCI6MjA3Mjk5NjU0NX0.ICE2eYzFZvz0dtNpAa5YlJTZD-idc2J76wn1ZeHwwck"
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        self.days = ['Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        self.time_slots = [
            {'start': '09:00', 'end': '10:00', 'slot_id': 0},
            {'start': '10:00', 'end': '11:00', 'slot_id': 1},
            {'start': '11:15', 'end': '12:15', 'slot_id': 2},
            {'start': '12:15', 'end': '13:15', 'slot_id': 3},
            {'start': '14:00', 'end': '15:00', 'slot_id': 4},
            {'start': '15:00', 'end': '16:00', 'slot_id': 5}
        ]
        
        # Continuous slot groups for labs (2-hour blocks)
        self.continuous_slots = [[0, 1], [2, 3], [4, 5]]
        
        self.population_size = 50
        self.generations = 150
        self.mutation_rate = 0.1
        self.crossover_rate = 0.85

    def fetch_data(self, department: str, section: str):
        """Fetch subjects, faculty, and existing timetables from Supabase"""
        try:
            # Get subjects for department with hours per week
            subjects_response = self.supabase.table('subjects').select('*').eq('department', department).execute()
            subjects = subjects_response.data
            
            # Get faculty for department
            faculty_response = self.supabase.table('faculty').select('*').eq('department', department).execute()
            faculty = faculty_response.data
            
            # Get existing timetables to avoid conflicts
            existing_response = self.supabase.table('timetables').select('*').execute()
            existing_timetables = existing_response.data
            
            return subjects, faculty, existing_timetables
            
        except Exception as e:
            print(f"Error fetching data: {e}", file=sys.stderr)
            return [], [], []

    def load_section_assignments(self, section_data):
        """Load faculty assignments from timetable-new.htm data"""
        assignments = {}
        if section_data and 'subjects' in section_data:
            for subject_code, faculty_name in section_data['subjects'].items():
                assignments[subject_code] = faculty_name
        return assignments
    
    def get_subject_hours_from_db(self, department, subject_codes):
        """Get exact weekly hours for subjects from database"""
        try:
            subject_hours = {}
            for subject_code in subject_codes:
                # Get from Supabase database
                if department:
                    response = self.supabase.table('subjects').select('weekly_hours, type').eq('department', department).eq('name', subject_code).execute()
                    
                    if response.data and len(response.data) > 0:
                        subject_data = response.data[0]
                        weekly_hours = int(subject_data.get('weekly_hours', 3))
                        subject_type = subject_data.get('type', 'theory').lower()
                        
                        subject_hours[subject_code] = {
                            'weekly_hours': weekly_hours,
                            'type': subject_type
                        }
                        print(f"Subject {subject_code}: {weekly_hours} hours/week, type: {subject_type}", file=sys.stderr)
                        continue
                
                # Default if not found
                subject_hours[subject_code] = {
                    'weekly_hours': 3,
                    'type': 'theory'
                }
                print(f"Subject {subject_code}: Using default 3 hours/week", file=sys.stderr)
            
            return subject_hours
            
        except Exception as e:
            print(f"Error getting subject hours for {department}: {e}", file=sys.stderr)
            return {code: {'weekly_hours': 3, 'type': 'theory'} for code in subject_codes}

    def check_faculty_conflict(self, faculty_name: str, day: str, slot_id: int, existing_timetables: List[Dict]) -> bool:
        """Check if faculty has conflict at given time"""
        for timetable in existing_timetables:
            if (timetable.get('faculty_name') == faculty_name and 
                timetable.get('day') == day and 
                timetable.get('time_slot') == slot_id):
                return True
        return False

    def create_individual(self, subjects: List[Dict], section: str, existing_timetables: List[Dict], section_data: Dict) -> Dict:
        """Create random timetable using exact weekly hours from database"""
        timetable = {day: {slot: None for slot in range(6)} for day in self.days}
        
        section_assignments = self.load_section_assignments(section_data)
        if not section_assignments:
            return timetable
        
        department = getattr(self, '_current_department', None)
        subject_hours = self.get_subject_hours_from_db(department, list(section_assignments.keys()))
        
        # Create exact sessions based on weekly hours
        all_sessions = []
        for subject_code, faculty_name in section_assignments.items():
            hours_info = subject_hours.get(subject_code, {'weekly_hours': 3, 'type': 'theory'})
            weekly_hours = int(hours_info['weekly_hours'])
            subject_type = hours_info['type'].lower()
            
            print(f"Creating sessions for {subject_code}: {weekly_hours} hours, type: {subject_type}", file=sys.stderr)
            
            if subject_type == 'lab' or subject_code.endswith('L'):
                # Labs: place in 2-hour continuous blocks
                sessions_needed = weekly_hours // 2
                for _ in range(sessions_needed):
                    all_sessions.append({
                        'subject': subject_code, 'faculty': faculty_name, 'type': 'lab', 'slots': 2
                    })
            else:
                # Theory: place in individual 1-hour slots
                for _ in range(weekly_hours):
                    all_sessions.append({
                        'subject': subject_code, 'faculty': faculty_name, 'type': 'theory', 'slots': 1
                    })
        
        print(f"Total sessions to place: {len(all_sessions)}", file=sys.stderr)
        random.shuffle(all_sessions)
        
        # Track constraints
        daily_subjects = {day: set() for day in self.days}
        daily_labs = {day: set() for day in self.days}
        
        # Place sessions with strict constraints
        for session in all_sessions:
            self._place_session_with_constraints(timetable, session, daily_subjects, daily_labs, existing_timetables, section)
        
        return timetable
    
    def _place_session_with_constraints(self, timetable, session, daily_subjects, daily_labs, existing_timetables, section):
        """Place session with strict constraint enforcement"""
        subject = session['subject']
        faculty = session['faculty']
        session_type = session['type']
        
        if session_type == 'lab':
            # Find available continuous slots for lab
            available_slots = []
            for day in self.days:
                # No same subject on same day
                if subject in daily_subjects[day]:
                    continue
                    
                # Only one lab per day
                if daily_labs[day]:
                    continue
                    
                # Skip Friday last period (keep it free)
                if day == 'Friday':
                    continue
                    
                for slot_group in self.continuous_slots:
                    # Check if both slots are free and no faculty conflict
                    if all(timetable[day][slot] is None and 
                           not self.check_faculty_conflict(faculty, day, slot, existing_timetables)
                           for slot in slot_group):
                        available_slots.append((day, slot_group))
            
            if available_slots:
                day, slot_group = random.choice(available_slots)
                display_name = f"{subject} Lab" if not subject.endswith('Lab') else subject
                
                for slot in slot_group:
                    timetable[day][slot] = {
                        'subject_code': subject, 'subject_name': display_name, 'faculty_name': faculty,
                        'section': section, 'room': f"Lab-{random.randint(1, 10)}", 'type': 'lab'
                    }
                
                daily_subjects[day].add(subject)
                daily_labs[day].add(subject)
                
        else:
            # Theory subject placement
            available_slots = []
            for day in self.days:
                # No same subject on same day
                if subject in daily_subjects[day]:
                    continue
                    
                for slot in range(6):
                    # Skip Friday last period (keep it free)
                    if day == 'Friday' and slot == 5:
                        continue
                        
                    if (timetable[day][slot] is None and 
                        not self.check_faculty_conflict(faculty, day, slot, existing_timetables)):
                        available_slots.append((day, slot))
            
            if available_slots:
                day, slot = random.choice(available_slots)
                timetable[day][slot] = {
                    'subject_code': subject, 'subject_name': subject, 'faculty_name': faculty,
                    'section': section, 'room': f"Room-{random.randint(101, 120)}", 'type': 'theory'
                }
                daily_subjects[day].add(subject)
    
    def _is_full_lab_day(self, timetable, day):
        """Check if day already has too many lab sessions"""
        lab_count = sum(1 for slot in range(6) 
                       if timetable[day][slot] and timetable[day][slot].get('type') == 'lab')
        return lab_count >= 4  # Max 2 lab sessions (4 slots) per day

    def calculate_fitness(self, individual: Dict, existing_timetables: List[Dict], section_data: Dict) -> float:
        """Calculate comprehensive fitness score with strict constraints"""
        fitness = 1000.0  # Start with higher base score
        
        # Critical constraint: Faculty conflicts (highest penalty)
        faculty_slots = {}
        for day in individual:
            for slot_id in individual[day]:
                entry = individual[day][slot_id]
                if entry:
                    faculty = entry['faculty_name']
                    key = f"{day}-{slot_id}"
                    
                    if faculty not in faculty_slots:
                        faculty_slots[faculty] = set()
                    
                    if key in faculty_slots[faculty]:
                        fitness -= 100  # Severe penalty for internal conflicts
                    else:
                        faculty_slots[faculty].add(key)
                    
                    # Check against existing timetables (cross-section conflicts)
                    if self.check_faculty_conflict(faculty, day, slot_id, existing_timetables):
                        fitness -= 150  # Maximum penalty for external conflicts
        
        # Lab continuity check (critical for labs)
        lab_continuity_score = self._check_lab_continuity(individual)
        fitness += lab_continuity_score
        
        # Subject distribution and daily repetition
        daily_subjects = {day: {} for day in self.days}
        weekly_subject_count = {}
        
        for day in individual:
            for slot_id in individual[day]:
                entry = individual[day][slot_id]
                if entry:
                    subject_code = entry['subject_code']
                    weekly_subject_count[subject_code] = weekly_subject_count.get(subject_code, 0) + 1
                    daily_subjects[day][subject_code] = daily_subjects[day].get(subject_code, 0) + 1
        
        # Strict penalty for same subject multiple times on same day
        for day in daily_subjects:
            for subject_code, count in daily_subjects[day].items():
                if count > 2:  # Only labs should have 2 continuous slots
                    fitness -= (count - 2) * 100
                elif count > 1 and not any(individual[day][slot] and 
                                         individual[day][slot].get('type') == 'lab' and 
                                         individual[day][slot].get('subject_code') == subject_code 
                                         for slot in range(6)):
                    # Theory subject repeated on same day
                    fitness -= (count - 1) * 75
        
        # Strict weekly hours validation (critical constraint)
        section_assignments = self.load_section_assignments(section_data)
        if section_assignments:
            department = getattr(self, '_current_department', None)
            subject_hours = self.get_subject_hours_from_db(department, list(section_assignments.keys()))
            for subject_code, expected_hours in subject_hours.items():
                actual_hours = weekly_subject_count.get(subject_code, 0)
                expected = int(expected_hours.get('weekly_hours', 3))
                if actual_hours == expected:
                    fitness += 50  # Bonus for exact match
                else:
                    fitness -= abs(actual_hours - expected) * 100  # Heavy penalty for mismatch
        
        # Friday last period must be free (institutional rule)
        if individual.get('Friday', {}).get(5) is not None:
            fitness -= 100  # Heavy penalty for using Friday last period
        
        # Bonus for other free last periods
        other_days_free = sum(1 for day in ['Tuesday', 'Wednesday', 'Thursday', 'Saturday'] 
                             if not individual.get(day, {}).get(5))
        fitness += other_days_free * 5
        
        # Daily workload balance
        daily_counts = {day: len([slot for slot in individual[day] if individual[day][slot]]) for day in individual}
        if daily_counts:
            max_daily = max(daily_counts.values())
            min_daily = min(daily_counts.values())
            if max_daily - min_daily > 3:
                fitness -= (max_daily - min_daily) * 10
        
        # Faculty free periods at end of day (optimization)
        fitness += self._calculate_faculty_optimization(individual)
        
        return max(0, fitness)
    
    def _check_lab_continuity(self, individual: Dict) -> float:
        """Check if labs are placed in proper continuous slots"""
        score = 0
        
        for day in individual:
            for slot_group in self.continuous_slots:
                slots_in_group = [individual[day].get(slot) for slot in slot_group]
                
                # Check if both slots have the same lab subject
                if all(slot and slot.get('type') == 'lab' for slot in slots_in_group):
                    if slots_in_group[0]['subject_code'] == slots_in_group[1]['subject_code']:
                        score += 50  # Bonus for proper lab continuity
                    else:
                        score -= 30  # Penalty for different labs in continuous slots
        
        return score
    
    def _calculate_faculty_optimization(self, individual: Dict) -> float:
        """Calculate faculty schedule optimization score"""
        score = 0
        faculty_daily_slots = {}
        
        # Track faculty daily schedules
        for day in individual:
            for slot_id in individual[day]:
                entry = individual[day][slot_id]
                if entry:
                    faculty = entry['faculty_name']
                    if faculty not in faculty_daily_slots:
                        faculty_daily_slots[faculty] = {}
                    if day not in faculty_daily_slots[faculty]:
                        faculty_daily_slots[faculty][day] = []
                    faculty_daily_slots[faculty][day].append(slot_id)
        
        # Bonus for faculty having free periods at end of day
        for faculty, daily_schedule in faculty_daily_slots.items():
            for day, slots in daily_schedule.items():
                if slots:
                    max_slot = max(slots)
                    if max_slot < 5:  # Faculty finishes before last period
                        score += (5 - max_slot) * 2
        
        return score

    def crossover(self, parent1: Dict, parent2: Dict) -> Dict:
        """Create offspring through crossover"""
        child = {}
        
        for day in self.days:
            child[day] = {}
            for slot_id in range(6):
                if random.random() < 0.5:
                    child[day][slot_id] = parent1[day].get(slot_id)
                else:
                    child[day][slot_id] = parent2[day].get(slot_id)
        
        return child

    def mutate(self, individual: Dict, subjects: List[Dict], section: str, existing_timetables: List[Dict], section_data: Dict) -> Dict:
        """Mutate individual randomly"""
        mutated = json.loads(json.dumps(individual))
        section_assignments = self.load_section_assignments(section_data)
        
        for day in self.days:
            for slot_id in range(6):
                if random.random() < self.mutation_rate:
                    if random.random() < 0.6 and section_assignments:
                        subject_code = random.choice(list(section_assignments.keys()))
                        faculty_name = section_assignments[subject_code]
                        
                        if not self.check_faculty_conflict(faculty_name, day, slot_id, existing_timetables):
                            mutated[day][slot_id] = {
                                'subject_code': subject_code, 'subject_name': subject_code,
                                'faculty_name': faculty_name, 'section': section,
                                'room': f"Room-{random.randint(101, 120)}"
                            }
                    else:
                        mutated[day][slot_id] = None
        
        return mutated

    def evolve_section(self, department: str, section: str, section_data: Dict) -> Dict:
        """Evolve timetable for a specific section"""
        print(f"Generating timetable for {department} {section}...", file=sys.stderr)
        
        # Store current department for use in other methods
        self._current_department = department
        
        subjects, faculty, existing_timetables = self.fetch_data(department, section)
        
        if not subjects:
            print(f"No subjects found for {department} - {section}", file=sys.stderr)
            return {}
        
        # Create initial population
        population = []
        for _ in range(self.population_size):
            individual = self.create_individual(subjects, section, existing_timetables, section_data)
            population.append(individual)
        
        best_fitness = 0
        best_individual = None
        
        for generation in range(self.generations):
            # Calculate fitness
            fitness_scores = []
            for individual in population:
                fitness = self.calculate_fitness(individual, existing_timetables, section_data)
                fitness_scores.append(fitness)
            
            # Track best
            max_fitness = max(fitness_scores) if fitness_scores else 0
            if max_fitness > best_fitness:
                best_fitness = max_fitness
                best_individual = population[fitness_scores.index(max_fitness)]
            
            # Selection and reproduction
            new_population = []
            
            # Elitism - keep best 30%
            elite_count = int(self.population_size * 0.3)
            elite_indices = sorted(range(len(fitness_scores)), key=lambda i: fitness_scores[i], reverse=True)[:elite_count]
            new_population.extend([population[i] for i in elite_indices])
            
            # Generate rest through crossover and mutation
            while len(new_population) < self.population_size:
                parent1 = self.tournament_selection(population, fitness_scores)
                parent2 = self.tournament_selection(population, fitness_scores)
                
                if random.random() < self.crossover_rate:
                    child = self.crossover(parent1, parent2)
                else:
                    child = json.loads(json.dumps(parent1))
                
                child = self.mutate(child, subjects, section, existing_timetables, section_data)
                new_population.append(child)
            
            population = new_population
            
            if generation % 20 == 0:
                print(f"Generation {generation}: Best fitness = {best_fitness:.2f}", file=sys.stderr)
        
        final_timetable = best_individual or population[0]
        
        if final_timetable:
            print(f"Final timetable fitness: {best_fitness:.2f}", file=sys.stderr)
        
        return final_timetable

    def tournament_selection(self, population: List[Dict], fitness_scores: List[float]) -> Dict:
        """Tournament selection"""
        tournament_size = 3
        tournament_indices = random.sample(range(len(population)), min(tournament_size, len(population)))
        best_index = max(tournament_indices, key=lambda i: fitness_scores[i])
        return population[best_index]

    def save_to_supabase(self, timetable: Dict, section: str, department: str):
        """Save generated timetable to Supabase"""
        try:
            # Clear existing timetable for this section
            self.supabase.table('timetables').delete().eq('section', section).eq('department', department).execute()
            
            for day in timetable:
                for slot_id in timetable[day]:
                    entry = timetable[day][slot_id]
                    if entry:
                        data = {
                            'faculty_name': entry['faculty_name'],
                            'subject_code': entry['subject_code'],
                            'subject_name': entry['subject_name'],
                            'day': day,
                            'time_slot': slot_id,
                            'section': section,
                            'room': entry['room'],
                            'department': department
                        }
                        
                        self.supabase.table('timetables').insert(data).execute()
            
            print(f"Timetable saved for {section}", file=sys.stderr)
            
        except Exception as e:
            print(f"Error saving timetable: {e}", file=sys.stderr)

    def validate_timetable(self, timetable: Dict, section_data: Dict) -> bool:
        """Validate final timetable meets all requirements"""
        section_assignments = self.load_section_assignments(section_data)
        if not section_assignments:
            return False
        
        # Get department from current context
        department = getattr(self, '_current_department', None)
        subject_hours = self.get_subject_hours_from_db(department, list(section_assignments.keys()))
        weekly_count = {}
        
        # Count actual weekly hours
        for day in timetable:
            for slot_id in timetable[day]:
                entry = timetable[day][slot_id]
                if entry and entry.get('subject_code'):
                    subject = entry['subject_code']
                    weekly_count[subject] = weekly_count.get(subject, 0) + 1
        
        # Validate weekly hours exactly match database requirements
        for subject, expected_info in subject_hours.items():
            expected_hours = int(expected_info.get('weekly_hours', 3))
            actual_hours = weekly_count.get(subject, 0)
            if actual_hours != expected_hours:
                print(f"Validation failed: {subject} has {actual_hours} hours, expected {expected_hours}", file=sys.stderr)
                return False
        
        # Check lab continuity
        for day in timetable:
            for slot_group in self.continuous_slots:
                slots_in_group = [timetable[day].get(slot) for slot in slot_group]
                if all(slot and slot.get('type') == 'lab' for slot in slots_in_group):
                    if slots_in_group[0]['subject_code'] != slots_in_group[1]['subject_code']:
                        print(f"Warning: Lab continuity broken on {day}", file=sys.stderr)
                        return False
        
        return True

def main():
    try:
        input_data = json.loads(sys.stdin.read())
        
        ga = SupabaseTimetableGA()
        results = {}
        
        for section_data in input_data.get('sections', []):
            section_name = section_data.get('name', 'A')
            assignments = section_data.get('subjects', {})
            
            # Convert assignments to the format expected by the GA
            section_assignments = {subject: info['faculty'] if isinstance(info, dict) else info for subject, info in assignments.items()}
            
            print(f"Processing section {section_name} with {len(section_assignments)} subjects", file=sys.stderr)
            
            department = input_data.get('department', 'ISE')
            
            # Generate timetable with validation
            max_attempts = 3
            timetable = {}  # ensure timetable is always defined
            for attempt in range(max_attempts):
                timetable = ga.evolve_section(department, section_name, {'subjects': section_assignments})
                
                if ga.validate_timetable(timetable, {'subjects': section_assignments}):
                    print(f"Valid timetable generated for {section_name} on attempt {attempt + 1}", file=sys.stderr)
                    break
                elif attempt == max_attempts - 1:
                    print(f"Warning: Could not generate fully valid timetable for {section_name}", file=sys.stderr)
            
            # Save to Supabase only if we have a timetable
            if timetable:
                ga.save_to_supabase(timetable, section_name, department)
            else:
                print(f"No timetable to save for {section_name}", file=sys.stderr)
            
            results[section_name] = timetable
        
        # Output result
        print(json.dumps(results))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
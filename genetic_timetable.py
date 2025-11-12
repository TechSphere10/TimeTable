import random
import json
import sys
from supabase.client import create_client, Client, ClientOptions
from typing import List, Dict, Any, Tuple
import os

# --- CRITICAL FIX FOR PROXY ERROR ---
# Unset proxy environment variables that conflict with the Supabase library.
# This is the definitive solution to the "unexpected keyword argument 'proxy'" error.
os.environ.pop('http_proxy', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('https_proxy', None)
os.environ.pop('HTTPS_PROXY', None)

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
        """Fetch subjects, faculty, and ALL existing timetables from Supabase for clash detection"""
        try:
            # Get subjects for department with hours per week
            subjects_response = self.supabase.table('subjects').select('*').execute() # Fetch all subjects for cross-dept
            subjects = subjects_response.data
            
            # Get faculty for department
            faculty_response = self.supabase.table('faculty').select('*').eq('department', department).execute()
            faculty = faculty_response.data
            
            # Get existing timetables to avoid conflicts
            existing_response = self.supabase.table('timetables').select('faculty_name, day, time_slot').execute()
            existing_timetables = existing_response.data
            
            return subjects, faculty, existing_timetables
            
        except Exception as e:
            print(f"Error fetching data: {e}", file=sys.stderr)
            return [], [], []

    def load_section_assignments(self, section_data):
        """Load faculty assignments from timetable-new.htm data"""
        assignments = {}
        # The incoming section_data is the 'assignments' list from the frontend
        if isinstance(section_data, list):
            for assignment in section_data:
                # Use subject name as the key, as it's unique per semester
                assignments[assignment['subject']] = assignment['faculty']
        return assignments
    
    def get_subject_hours_from_db(self, department, subject_codes):
        """Get exact weekly hours for subjects from database"""
        try:
            subject_hours = {}
            for subject_code in subject_codes:
                # Get from Supabase database
                if department:
                    response = self.supabase.table('subjects').select('weekly_hours, type').eq('name', subject_code).execute()
                    
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

    def create_individual(self, assignments_list: List[Dict], section: str, existing_timetables: List[Dict]) -> Dict:
        """Create random timetable using exact weekly hours from database"""
        timetable = {day: {slot: None for slot in range(6)} for day in self.days}
        
        # Use the direct assignments_list passed in
        if not assignments_list:
            return timetable
        
        department = getattr(self, '_current_department', None)
        subject_hours = self.get_subject_hours_from_db(department, [a['subject'] for a in assignments_list])
        
        # Create exact sessions based on weekly hours
        all_sessions = []
        for assignment in assignments_list:
            hours_info = subject_hours.get(assignment['subject'], {'weekly_hours': 3, 'type': 'theory'})
            weekly_hours = int(hours_info['weekly_hours'])
            subject_type = hours_info['type'].lower()
            
            print(f"Creating sessions for {assignment['subject']}: {weekly_hours} hours, type: {subject_type}", file=sys.stderr)
            
            if subject_type == 'lab':
                # Labs: place in 2-hour continuous blocks
                sessions_needed = weekly_hours // 2
                for _ in range(sessions_needed):
                    all_sessions.append({
                        'subject': assignment['subject'], 'faculty': assignment['faculty'], 'type': 'lab', 'slots': 2
                    })
            else:
                # Theory: place in individual 1-hour slots
                for _ in range(weekly_hours):
                    all_sessions.append({
                        'subject': assignment['subject'], 'faculty': assignment['faculty'], 'type': 'theory', 'slots': 1
                    })
        
        print(f"Total sessions to place: {len(all_sessions)}", file=sys.stderr)
        random.shuffle(all_sessions)
        
        # Track constraints
        daily_subjects = {day: set() for day in self.days}
        daily_labs = {day: set() for day in self.days}
        
        # Place sessions with strict constraints
        unplaced_sessions = []
        for session in all_sessions:
            placed = self._place_session_with_constraints(timetable, session, daily_subjects, daily_labs, existing_timetables, section)
            if not placed:
                unplaced_sessions.append(session)
        
        # Force-place any remaining sessions into the first available empty slots
        if unplaced_sessions:
            print(f"Force-placing {len(unplaced_sessions)} unplaced sessions.", file=sys.stderr)
            for session in unplaced_sessions:
                self._force_place_session(timetable, session, section)
        
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
                if daily_labs[day]: # Strict: only one lab session of any kind per day
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
                return True
                
        else: # Theory
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
                return True
        
        return False # Could not place session
    
    def _force_place_session(self, timetable, session, section):
        """Forcefully place a session in the first available empty slot."""
        for day in self.days:
            for slot_id in range(6):
                if timetable[day][slot_id] is None:
                    timetable[day][slot_id] = {
                        'subject_code': session['subject'],
                        'subject_name': session['subject'],
                        'faculty_name': session['faculty'],
                        'section': section,
                        'room': f"Room-{random.randint(101, 120)}",
                        'type': session['type']
                    }
                    return # Placed, so exit
    def _is_full_lab_day(self, timetable, day):
        """Check if day already has too many lab sessions"""
        lab_count = sum(1 for slot in range(6) 
                       if timetable[day][slot] and timetable[day][slot].get('type') == 'lab')
        return lab_count >= 4  # Max 2 lab sessions (4 slots) per day

    def calculate_fitness(self, individual: Dict, existing_timetables: List[Dict], section_data: List[Dict]) -> float:
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
                # Check if the subject is a lab
                is_lab = any(
                    individual[day][slot] and individual[day][slot].get('type') == 'lab' and
                    individual[day][slot].get('subject_code') == subject_code
                    for slot in range(6)
                )
                # For labs, a count of 2 is okay. For theory, only 1.
                if is_lab and count > 2:
                    fitness -= (count - 2) * 50 # Penalty for more than one lab session of same subject
                elif not is_lab and count > 1:
                    fitness -= (count - 1) * 75 # Penalty for repeated theory subject
                if count > 2:  # Only labs should have 2 continuous slots
                    fitness -= (count - 2) * 100
                elif count > 1 and not any(individual[day][slot] and 
                                         individual[day][slot].get('type') == 'lab' and 
                                         individual[day][slot].get('subject_code') == subject_code 
                                         for slot in range(6)):
                    # Theory subject repeated on same day
                    fitness -= (count - 1) * 75

        # New Constraint: Subject should not repeat at the same period across all days
        period_subjects = {slot_id: set() for slot_id in range(6)}
        for day in individual:
            for slot_id, entry in individual[day].items():
                if entry:
                    subject_code = entry['subject_code']
                    if subject_code in period_subjects[slot_id]:
                        fitness -= 20 # Penalty for subject repeating at the same time
                    period_subjects[slot_id].add(subject_code)

        # Strict weekly hours validation (critical constraint)
        section_assignments = self.load_section_assignments(section_data)
        if section_assignments:
            department = getattr(self, '_current_department', None) # Get department from context
            subject_hours = self.get_subject_hours_from_db(department, list(section_assignments.keys()))
            for subject_code, expected_hours in subject_hours.items():
                actual_hours = weekly_subject_count.get(subject_code, 0)
                expected = int(expected_hours.get('weekly_hours', 3))
                if actual_hours == expected:
                    fitness += 50  # Bonus for exact match
                else:
                    fitness -= abs(actual_hours - expected) * 150  # Increased penalty for mismatch
        
        # Friday last period must be free (institutional rule)
        if individual.get('Friday', {}).get(5) is not None:
            fitness -= 100  # Heavy penalty for using Friday last period
        
        # Bonus for faculty free periods at the end of the day
        for faculty in faculty_slots:
            for day in self.days:
                last_period_worked = -1
                for slot_id in range(6):
                    key = f"{day}-{slot_id}"
                    if key in faculty_slots[faculty]:
                        last_period_worked = slot_id
                if last_period_worked != -1 and last_period_worked < 5:
                    fitness += (5 - last_period_worked) * 2 # Bonus for finishing early
        
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

    def mutate(self, individual: Dict, subjects: List[Dict], section: str, existing_timetables: List[Dict], section_data: List[Dict]) -> Dict:
        """Mutate individual randomly"""
        if random.random() < self.mutation_rate:
            mutated = json.loads(json.dumps(individual))

            # Select two random, different slots to swap
            day1, day2 = random.choices(self.days, k=2)
            slot1, slot2 = random.choices(range(6), k=2)

            # Ensure they are different slots if on the same day
            if day1 == day2 and slot1 == slot2:
                return individual # No change

            # Perform the swap
            temp = mutated[day1][slot1]
            mutated[day1][slot1] = mutated[day2][slot2]
            mutated[day2][slot2] = temp
            return mutated
        return individual

    def evolve_section(self, department: str, section: str, section_data: List[Dict]) -> Dict:
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
        # CRITICAL FIX: The section_data IS the assignments_list.
        assignments_list = section_data if isinstance(section_data, list) else []
        for _ in range(self.population_size):
            individual = self.create_individual(assignments_list, section, existing_timetables)
            population.append(individual)
        
        best_fitness = 0
        best_individual = None
        
        for generation in range(self.generations):
            # Calculate fitness for each individual in the population
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
                
                child = self.mutate(child, assignments_list, section, existing_timetables, section_data)
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

    def validate_timetable(self, timetable: Dict, section_data: List[Dict]) -> bool:
        """Validate final timetable meets all requirements"""
        section_assignments = self.load_section_assignments(section_data)
        if not section_assignments:
            return False
        
        # Get department from current context
        department = getattr(self, '_current_department', None)
        subject_hours_info = self.get_subject_hours_from_db(department, [a['subject'] for a in section_data])
        weekly_count = {}
        
        # Count actual weekly hours
        for day in timetable:
            for slot_id in timetable[day]:
                entry = timetable[day][slot_id]
                if entry and entry.get('subject_code'):
                    subject = entry['subject_code']
                    weekly_count[subject] = weekly_count.get(subject, 0) + 1
        
        # Validate weekly hours exactly match database requirements
        for assignment in section_data:
            subject = assignment['subject']
            expected_hours = int(subject_hours_info.get(subject, {}).get('weekly_hours', 3))
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
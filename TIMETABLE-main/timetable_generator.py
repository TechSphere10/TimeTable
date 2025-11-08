import random
import json
from datetime import datetime, timedelta

class TimetableGenerator:
    def __init__(self, config):
        self.config = config
        self.subjects = config['subjects']
        self.sections = config['sections']
        self.periods_per_day = int(config['periodsPerDay'])
        self.working_days = self._get_working_days(config['workingDays'])
        self.population_size = 100
        self.generations = 500
        self.mutation_rate = 0.3
        self.faculty_schedule = {}  # Track faculty assignments across all sections
        
    def _get_working_days(self, days_config):
        if days_config == '5':
            return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        elif days_config == '6':
            return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        else:
            return ['Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    def generate_timetable(self, section_index=0):
        """Generate timetable for a specific section"""
        section = self.sections[section_index]
        section_subjects = section['subjectFaculty']
        
        # Initialize population
        population = [self._create_chromosome(section_subjects) for _ in range(self.population_size)]
        
        best_solution = None
        best_fitness = float('-inf')
        
        for generation in range(self.generations):
            # Evaluate fitness
            fitness_scores = [(chromo, self._fitness(chromo, section_subjects)) for chromo in population]
            fitness_scores.sort(key=lambda x: x[1], reverse=True)
            
            if fitness_scores[0][1] > best_fitness:
                best_fitness = fitness_scores[0][1]
                best_solution = fitness_scores[0][0]
            
            # Early stopping if perfect solution found
            if best_fitness >= 100:
                break
            
            # Selection
            parents = [fs[0] for fs in fitness_scores[:self.population_size//2]]
            
            # Crossover and Mutation
            offspring = []
            while len(offspring) < self.population_size//2:
                parent1, parent2 = random.sample(parents, 2)
                child = self._crossover(parent1, parent2)
                if random.random() < self.mutation_rate:
                    child = self._mutate(child, section_subjects)
                offspring.append(child)
            
            population = parents + offspring
        
        # Update faculty schedule with best solution
        self._update_faculty_schedule(best_solution, section_subjects, section['name'])
        
        return self._format_timetable(best_solution, section_subjects, section['name'])
    
    def _create_chromosome(self, section_subjects):
        """Create a random timetable chromosome"""
        chromosome = {}
        for day in self.working_days:
            chromosome[day] = [None] * self.periods_per_day
        
        # Assign subjects to slots
        for subject_info in section_subjects:
            subject = subject_info['subject']
            weekly_hours = subject_info.get('weekly_hours', 3)
            subject_type = subject_info.get('type', 'theory')
            
            slots_needed = weekly_hours
            slots_assigned = 0
            
            while slots_assigned < slots_needed:
                day = random.choice(self.working_days)
                
                if subject_type == 'lab' and slots_assigned == 0:
                    # Lab needs 2 consecutive periods
                    period = random.randint(0, self.periods_per_day - 2)
                    if chromosome[day][period] is None and chromosome[day][period + 1] is None:
                        chromosome[day][period] = subject
                        chromosome[day][period + 1] = subject
                        slots_assigned += 2
                else:
                    # Regular subject
                    period = random.randint(0, self.periods_per_day - 1)
                    if chromosome[day][period] is None:
                        chromosome[day][period] = subject
                        slots_assigned += 1
        
        # Assign FREE periods to last period preferably
        for day in self.working_days:
            free_count = chromosome[day].count(None)
            if free_count > 0:
                # Try to place FREE at last period
                if chromosome[day][-1] is None:
                    chromosome[day][-1] = 'FREE'
                # Fill remaining with FREE
                for i in range(len(chromosome[day])):
                    if chromosome[day][i] is None:
                        chromosome[day][i] = 'FREE'
        
        return chromosome
    
    def _fitness(self, chromosome, section_subjects):
        """Calculate fitness score for a chromosome"""
        score = 100
        
        # Check subject distribution
        for subject_info in section_subjects:
            subject = subject_info['subject']
            required_hours = subject_info.get('weekly_hours', 3)
            actual_hours = sum(day.count(subject) for day in chromosome.values())
            
            if actual_hours != required_hours:
                score -= abs(actual_hours - required_hours) * 5
        
        # Check lab continuity
        for subject_info in section_subjects:
            if subject_info.get('type') == 'lab':
                subject = subject_info['subject']
                for day in chromosome.values():
                    for i in range(len(day) - 1):
                        if day[i] == subject and day[i+1] != subject:
                            score -= 10  # Lab should be continuous
        
        # Check FREE period placement (prefer last period)
        for day in chromosome.values():
            if day[-1] == 'FREE':
                score += 5
            else:
                score -= 3
        
        # Check faculty conflicts
        faculty_conflicts = self._check_faculty_conflicts(chromosome, section_subjects)
        score -= faculty_conflicts * 20
        
        # Avoid too many classes on same day
        for day in chromosome.values():
            non_free = [s for s in day if s != 'FREE']
            if len(non_free) > self.periods_per_day - 1:
                score -= 5
        
        return max(0, score)
    
    def _check_faculty_conflicts(self, chromosome, section_subjects):
        """Check if faculty has conflicts with existing schedule"""
        conflicts = 0
        faculty_map = {s['subject']: s['faculty'] for s in section_subjects}
        
        for day_idx, day in enumerate(self.working_days):
            for period_idx, subject in enumerate(chromosome[day]):
                if subject and subject != 'FREE':
                    faculty = faculty_map.get(subject)
                    if faculty and faculty in self.faculty_schedule:
                        # Check if faculty is already assigned at this time
                        time_slot = f"{day}_{period_idx}"
                        if time_slot in self.faculty_schedule[faculty]:
                            conflicts += 1
        
        return conflicts
    
    def _crossover(self, parent1, parent2):
        """Perform crossover between two parents"""
        child = {}
        for day in self.working_days:
            if random.random() < 0.5:
                child[day] = parent1[day][:]
            else:
                child[day] = parent2[day][:]
        return child
    
    def _mutate(self, chromosome, section_subjects):
        """Mutate a chromosome"""
        day = random.choice(self.working_days)
        period1 = random.randint(0, self.periods_per_day - 1)
        period2 = random.randint(0, self.periods_per_day - 1)
        
        # Swap two periods
        chromosome[day][period1], chromosome[day][period2] = chromosome[day][period2], chromosome[day][period1]
        
        return chromosome
    
    def _update_faculty_schedule(self, chromosome, section_subjects, section_name):
        """Update global faculty schedule"""
        faculty_map = {s['subject']: s['faculty'] for s in section_subjects}
        
        for day in self.working_days:
            for period_idx, subject in enumerate(chromosome[day]):
                if subject and subject != 'FREE':
                    faculty = faculty_map.get(subject)
                    if faculty:
                        if faculty not in self.faculty_schedule:
                            self.faculty_schedule[faculty] = {}
                        time_slot = f"{day}_{period_idx}"
                        if time_slot not in self.faculty_schedule[faculty]:
                            self.faculty_schedule[faculty][time_slot] = []
                        self.faculty_schedule[faculty][time_slot].append({
                            'section': section_name,
                            'subject': subject
                        })
    
    def _format_timetable(self, chromosome, section_subjects, section_name):
        """Format timetable for output"""
        faculty_map = {s['subject']: s['faculty'] for s in section_subjects}
        
        timetable = {
            'section': section_name,
            'schedule': {}
        }
        
        for day in self.working_days:
            timetable['schedule'][day] = []
            for period_idx, subject in enumerate(chromosome[day]):
                faculty = faculty_map.get(subject, '') if subject != 'FREE' else ''
                timetable['schedule'][day].append({
                    'period': period_idx + 1,
                    'subject': subject or 'FREE',
                    'faculty': faculty
                })
        
        return timetable
    
    def get_faculty_schedule(self, faculty_name):
        """Get complete schedule for a specific faculty"""
        if faculty_name not in self.faculty_schedule:
            return None
        
        schedule = {}
        for time_slot, assignments in self.faculty_schedule[faculty_name].items():
            day, period = time_slot.split('_')
            if day not in schedule:
                schedule[day] = {}
            schedule[day][int(period)] = assignments
        
        return schedule

def generate_all_timetables(config):
    """Generate timetables for all sections"""
    generator = TimetableGenerator(config)
    all_timetables = []
    
    for i in range(len(config['sections'])):
        timetable = generator.generate_timetable(i)
        all_timetables.append(timetable)
    
    return {
        'timetables': all_timetables,
        'faculty_schedule': generator.faculty_schedule,
        'config': config
    }

if __name__ == '__main__':
    # Test with sample config
    sample_config = {
        'periodsPerDay': 7,
        'workingDays': '5',
        'subjects': [],
        'sections': [
            {
                'name': 'Section 1',
                'subjectFaculty': [
                    {'subject': 'Mathematics', 'faculty': 'Dr. Smith', 'weekly_hours': 4, 'type': 'theory'},
                    {'subject': 'Physics', 'faculty': 'Dr. Jones', 'weekly_hours': 3, 'type': 'theory'},
                    {'subject': 'Physics Lab', 'faculty': 'Dr. Jones', 'weekly_hours': 2, 'type': 'lab'},
                ]
            }
        ]
    }
    
    result = generate_all_timetables(sample_config)
    print(json.dumps(result, indent=2))

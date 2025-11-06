import random
import json
import sys
from typing import List, Dict, Tuple
import copy

class Subject:
    def __init__(self, name: str, credits: int, hours: int, subject_type: str):
        self.name = name
        self.credits = credits
        self.hours = hours
        self.type = subject_type  # 'theory', 'lab', 'mcq', 'free'

class Faculty:
    def __init__(self, name: str, initials: str, faculty_type: str):
        self.name = name
        self.initials = initials
        self.type = faculty_type

class Assignment:
    def __init__(self, subject: Subject, faculty: Faculty, section: str):
        self.subject = subject
        self.faculty = faculty
        self.section = section

class TimeSlot:
    def __init__(self, day: int, period: int, time_str: str):
        self.day = day  # 0-5 (Mon-Sat)
        self.period = period  # 0-8
        self.time_str = time_str
        self.is_break = time_str in ['BREAK', 'LUNCH']

class TimetableGene:
    def __init__(self, assignment: Assignment, time_slot: TimeSlot):
        self.assignment = assignment
        self.time_slot = time_slot

class Timetable:
    def __init__(self, sections: int):
        self.sections = sections
        self.genes: List[TimetableGene] = []
        self.fitness = 0
        
        # Time slots configuration
        self.time_slots = [
            TimeSlot(day, period, time_str) 
            for day in range(6)  # Mon-Sat
            for period, time_str in enumerate([
                '9:00-9:50', '9:50-10:40', 'BREAK', '11:00-11:50', 
                '11:50-12:40', 'LUNCH', '1:30-2:20', '2:20-3:10', '3:10-4:00'
            ])
        ]
        
        # Filter out break periods for allocation
        self.available_slots = [slot for slot in self.time_slots if not slot.is_break]

class GeneticTimetableGenerator:
    def __init__(self, assignments: List[Assignment], sections: int):
        self.assignments = assignments
        self.sections = sections
        self.population_size = 50
        self.generations = 100
        self.mutation_rate = 0.1
        self.crossover_rate = 0.8
        
        # Create time slots
        self.time_slots = [
            TimeSlot(day, period, time_str) 
            for day in range(6)  # Mon-Sat
            for period, time_str in enumerate([
                '9:00-9:50', '9:50-10:40', 'BREAK', '11:00-11:50', 
                '11:50-12:40', 'LUNCH', '1:30-2:20', '2:20-3:10', '3:10-4:00'
            ])
        ]
        
        self.available_slots = [slot for slot in self.time_slots if not slot.is_break]
        
    def create_individual(self) -> Timetable:
        """Create a random timetable individual"""
        timetable = Timetable(self.sections)
        
        for assignment in self.assignments:
            hours_needed = assignment.subject.hours
            allocated_hours = 0
            
            # For lab subjects, try to allocate consecutive hours
            if assignment.subject.type == 'lab':
                allocated_hours = self._allocate_lab_hours(timetable, assignment, hours_needed)
            else:
                allocated_hours = self._allocate_theory_hours(timetable, assignment, hours_needed)
        
        return timetable
    
    def _allocate_lab_hours(self, timetable: Timetable, assignment: Assignment, hours_needed: int) -> int:
        """Allocate consecutive hours for lab subjects"""
        allocated = 0
        attempts = 0
        max_attempts = 50
        
        while allocated < hours_needed and attempts < max_attempts:
            # Try to find consecutive slots
            day = random.randint(0, 5)
            start_period = random.choice([0, 1, 3, 4, 6, 7])  # Avoid break periods
            
            # Check if we can allocate consecutive hours
            consecutive_slots = []
            for i in range(2):  # Lab needs 2 consecutive hours
                period = start_period + i
                if period < 9 and period not in [2, 5]:  # Skip break periods
                    slot = next((s for s in self.available_slots 
                               if s.day == day and s.period == period), None)
                    if slot and not self._is_slot_occupied(timetable, assignment.section, slot):
                        consecutive_slots.append(slot)
                    else:
                        break
            
            if len(consecutive_slots) >= 2:
                for slot in consecutive_slots[:2]:
                    gene = TimetableGene(assignment, slot)
                    timetable.genes.append(gene)
                    allocated += 1
                    if allocated >= hours_needed:
                        break
            
            attempts += 1
        
        return allocated
    
    def _allocate_theory_hours(self, timetable: Timetable, assignment: Assignment, hours_needed: int) -> int:
        """Allocate hours for theory subjects with smart distribution"""
        allocated = 0
        attempts = 0
        max_attempts = 200
        
        # Prefer distribution across different days
        used_days = set()
        
        while allocated < hours_needed and attempts < max_attempts:
            slot = random.choice(self.available_slots)
            
            if not self._is_slot_occupied(timetable, assignment.section, slot):
                # Special handling for different subject types
                should_allocate = True
                
                if assignment.subject.type == 'mcq':
                    # MCQ prefers after lunch, but allow morning if needed
                    if slot.period >= 6:  # After lunch periods
                        should_allocate = True
                    elif allocated == 0 and attempts > 50:  # Allow morning if struggling
                        should_allocate = random.random() < 0.5
                    else:
                        should_allocate = random.random() < 0.2
                elif assignment.subject.type == 'free':
                    # Free periods prefer end of day
                    should_allocate = slot.period >= 7 or random.random() < 0.3
                else:
                    # Regular theory - prefer spreading across days
                    if slot.day not in used_days:
                        should_allocate = True
                    elif len(used_days) >= 3:  # If already spread, allow same day
                        should_allocate = True
                    else:
                        should_allocate = random.random() < 0.6
                
                if should_allocate:
                    gene = TimetableGene(assignment, slot)
                    timetable.genes.append(gene)
                    used_days.add(slot.day)
                    allocated += 1
            
            attempts += 1
        
        return allocated
    
    def _is_slot_occupied(self, timetable: Timetable, section: str, slot: TimeSlot) -> bool:
        """Check if a time slot is already occupied"""
        for gene in timetable.genes:
            if (gene.assignment.section == section and 
                gene.time_slot.day == slot.day and 
                gene.time_slot.period == slot.period):
                return True
        return False
    
    def calculate_fitness(self, timetable: Timetable) -> float:
        """Calculate comprehensive fitness score for a timetable"""
        fitness = 100.0
        
        # Critical constraints (heavy penalties)
        faculty_conflicts = self._check_faculty_conflicts(timetable)
        fitness -= faculty_conflicts * 15  # Increased penalty
        
        section_conflicts = self._check_section_conflicts(timetable)
        fitness -= section_conflicts * 20  # Very heavy penalty
        
        # Important constraints (medium penalties)
        lab_violations = self._check_lab_violations(timetable)
        fitness -= lab_violations * 12
        
        hours_violations = self._check_hours_allocation(timetable)
        fitness -= hours_violations * 8
        
        # Preference constraints (light penalties)
        mcq_violations = self._check_mcq_placement(timetable)
        fitness -= mcq_violations * 3
        
        free_period_violations = self._check_free_period_placement(timetable)
        fitness -= free_period_violations * 4
        
        # Bonuses for good practices
        balance_bonus = self._calculate_balance_bonus(timetable)
        fitness += balance_bonus
        
        distribution_bonus = self._calculate_distribution_bonus(timetable)
        fitness += distribution_bonus
        
        timetable.fitness = max(0, fitness)
        return timetable.fitness
    
    def _check_section_conflicts(self, timetable: Timetable) -> int:
        """Check for multiple subjects assigned to same section at same time"""
        conflicts = 0
        section_schedule = {}
        
        for gene in timetable.genes:
            key = (gene.assignment.section, gene.time_slot.day, gene.time_slot.period)
            if key in section_schedule:
                conflicts += 1
            else:
                section_schedule[key] = gene
        
        return conflicts
    
    def _check_hours_allocation(self, timetable: Timetable) -> int:
        """Check if subjects get their required hours"""
        violations = 0
        subject_hours = {}
        
        # Count allocated hours for each subject-section combination
        for gene in timetable.genes:
            key = (gene.assignment.subject.name, gene.assignment.section)
            if key not in subject_hours:
                subject_hours[key] = 0
            subject_hours[key] += 1
        
        # Check against required hours
        for assignment in self.assignments:
            key = (assignment.subject.name, assignment.section)
            allocated = subject_hours.get(key, 0)
            required = assignment.subject.hours
            
            if allocated < required:
                violations += (required - allocated)
        
        return violations
    
    def _calculate_distribution_bonus(self, timetable: Timetable) -> float:
        """Bonus for good distribution of subjects across time slots"""
        bonus = 0
        
        # Check for variety in each day
        for section_num in range(1, self.sections + 1):
            section = chr(64 + section_num)
            
            for day in range(6):  # Monday to Saturday
                day_subjects = set()
                for gene in timetable.genes:
                    if (gene.assignment.section == section and 
                        gene.time_slot.day == day):
                        day_subjects.add(gene.assignment.subject.name)
                
                # Bonus for variety (more different subjects in a day)
                if len(day_subjects) >= 3:
                    bonus += 2
                elif len(day_subjects) >= 2:
                    bonus += 1
        
        return bonus
    
    def _check_faculty_conflicts(self, timetable: Timetable) -> int:
        """Check for faculty teaching conflicts"""
        conflicts = 0
        time_faculty_map = {}
        
        for gene in timetable.genes:
            key = (gene.time_slot.day, gene.time_slot.period)
            if key not in time_faculty_map:
                time_faculty_map[key] = set()
            
            if gene.assignment.faculty.initials in time_faculty_map[key]:
                conflicts += 1
            else:
                time_faculty_map[key].add(gene.assignment.faculty.initials)
        
        return conflicts
    
    def _check_lab_violations(self, timetable: Timetable) -> int:
        """Check if lab subjects have consecutive hours"""
        violations = 0
        lab_genes = [gene for gene in timetable.genes if gene.assignment.subject.type == 'lab']
        
        # Group lab genes by assignment and section
        lab_groups = {}
        for gene in lab_genes:
            key = (gene.assignment.subject.name, gene.assignment.section)
            if key not in lab_groups:
                lab_groups[key] = []
            lab_groups[key].append(gene)
        
        for genes in lab_groups.values():
            if len(genes) >= 2:
                # Check if any two genes are consecutive
                genes.sort(key=lambda g: (g.time_slot.day, g.time_slot.period))
                consecutive_found = False
                for i in range(len(genes) - 1):
                    if (genes[i].time_slot.day == genes[i+1].time_slot.day and
                        genes[i+1].time_slot.period - genes[i].time_slot.period == 1):
                        consecutive_found = True
                        break
                if not consecutive_found:
                    violations += 1
        
        return violations
    
    def _check_mcq_placement(self, timetable: Timetable) -> int:
        """Check MCQ placement preference (after lunch)"""
        violations = 0
        mcq_genes = [gene for gene in timetable.genes if gene.assignment.subject.type == 'mcq']
        
        for gene in mcq_genes:
            if gene.time_slot.period < 6:  # Before lunch
                violations += 1
        
        return violations
    
    def _check_free_period_placement(self, timetable: Timetable) -> int:
        """Check if free periods are placed at the end"""
        violations = 0
        free_genes = [gene for gene in timetable.genes if gene.assignment.subject.type == 'free']
        
        for gene in free_genes:
            if gene.time_slot.period < 7:  # Not in last periods
                violations += 1
        
        return violations
    
    def _calculate_balance_bonus(self, timetable: Timetable) -> float:
        """Calculate bonus for balanced distribution"""
        day_counts = [0] * 6
        for gene in timetable.genes:
            day_counts[gene.time_slot.day] += 1
        
        # Calculate standard deviation
        mean = sum(day_counts) / len(day_counts)
        variance = sum((x - mean) ** 2 for x in day_counts) / len(day_counts)
        std_dev = variance ** 0.5
        
        # Lower standard deviation = better balance = higher bonus
        return max(0, 10 - std_dev)
    
    def crossover(self, parent1: Timetable, parent2: Timetable) -> Tuple[Timetable, Timetable]:
        """Perform crossover between two parent timetables"""
        if random.random() > self.crossover_rate:
            return copy.deepcopy(parent1), copy.deepcopy(parent2)
        
        child1 = Timetable(self.sections)
        child2 = Timetable(self.sections)
        
        # Single point crossover
        crossover_point = random.randint(1, len(parent1.genes) - 1)
        
        child1.genes = parent1.genes[:crossover_point] + parent2.genes[crossover_point:]
        child2.genes = parent2.genes[:crossover_point] + parent1.genes[crossover_point:]
        
        return child1, child2
    
    def mutate(self, timetable: Timetable) -> Timetable:
        """Perform mutation on a timetable"""
        if random.random() > self.mutation_rate:
            return timetable
        
        if len(timetable.genes) > 0:
            # Select random gene to mutate
            gene_index = random.randint(0, len(timetable.genes) - 1)
            gene = timetable.genes[gene_index]
            
            # Find a new valid time slot
            attempts = 0
            while attempts < 20:
                new_slot = random.choice(self.available_slots)
                if not self._is_slot_occupied_except(timetable, gene.assignment.section, new_slot, gene_index):
                    timetable.genes[gene_index] = TimetableGene(gene.assignment, new_slot)
                    break
                attempts += 1
        
        return timetable
    
    def _is_slot_occupied_except(self, timetable: Timetable, section: str, slot: TimeSlot, except_index: int) -> bool:
        """Check if slot is occupied, excluding a specific gene"""
        for i, gene in enumerate(timetable.genes):
            if (i != except_index and 
                gene.assignment.section == section and 
                gene.time_slot.day == slot.day and 
                gene.time_slot.period == slot.period):
                return True
        return False
    
    def generate(self) -> Timetable:
        """Generate timetable using genetic algorithm"""
        print(f"Starting genetic algorithm with {len(self.assignments)} assignments for {self.sections} sections")
        
        # Initialize population with diverse individuals
        population = []
        for i in range(self.population_size):
            individual = self.create_individual()
            self.calculate_fitness(individual)
            population.append(individual)
            if i % 10 == 0:
                print(f"Created individual {i+1}/{self.population_size}")
        
        best_fitness = 0
        best_individual = None
        stagnation_count = 0
        
        for generation in range(self.generations):
            # Sort by fitness
            population.sort(key=lambda x: x.fitness, reverse=True)
            
            # Track best individual
            current_best_fitness = population[0].fitness
            if current_best_fitness > best_fitness:
                best_fitness = current_best_fitness
                best_individual = copy.deepcopy(population[0])
                stagnation_count = 0
            else:
                stagnation_count += 1
            
            # Early termination if fitness is good enough
            if best_fitness >= 95.0:
                print(f"Excellent solution found at generation {generation} with fitness {best_fitness:.2f}")
                break
            
            # Increase mutation rate if stagnating
            if stagnation_count > 20:
                self.mutation_rate = min(0.3, self.mutation_rate * 1.1)
            else:
                self.mutation_rate = max(0.1, self.mutation_rate * 0.99)
            
            # Selection and reproduction
            new_population = []
            
            # Keep best individuals (elitism)
            elite_count = max(2, self.population_size // 10)
            new_population.extend([copy.deepcopy(ind) for ind in population[:elite_count]])
            
            # Generate offspring
            while len(new_population) < self.population_size:
                parent1 = self._tournament_selection(population)
                parent2 = self._tournament_selection(population)
                
                child1, child2 = self.crossover(parent1, parent2)
                child1 = self.mutate(child1)
                child2 = self.mutate(child2)
                
                # Repair invalid solutions
                child1 = self._repair_timetable(child1)
                child2 = self._repair_timetable(child2)
                
                self.calculate_fitness(child1)
                self.calculate_fitness(child2)
                
                new_population.extend([child1, child2])
            
            population = new_population[:self.population_size]
            
            # Print progress
            if generation % 10 == 0:
                avg_fitness = sum(ind.fitness for ind in population) / len(population)
                print(f"Generation {generation}: Best={best_fitness:.2f}, Avg={avg_fitness:.2f}, Mutation={self.mutation_rate:.3f}")
        
        final_best = best_individual if best_individual else population[0]
        print(f"Final best fitness: {final_best.fitness:.2f}")
        return final_best
    
    def _repair_timetable(self, timetable: Timetable) -> Timetable:
        """Repair invalid timetable by fixing obvious conflicts"""
        # Remove duplicate assignments for same section at same time
        seen_slots = set()
        valid_genes = []
        
        for gene in timetable.genes:
            slot_key = (gene.assignment.section, gene.time_slot.day, gene.time_slot.period)
            if slot_key not in seen_slots:
                seen_slots.add(slot_key)
                valid_genes.append(gene)
        
        timetable.genes = valid_genes
        return timetable
    
    def _tournament_selection(self, population: List[Timetable]) -> Timetable:
        """Tournament selection for parent selection"""
        tournament_size = 5
        tournament = random.sample(population, min(tournament_size, len(population)))
        return max(tournament, key=lambda x: x.fitness)
    
    def timetable_to_dict(self, timetable: Timetable) -> Dict:
        """Convert timetable to dictionary format"""
        result = {}
        
        # Initialize structure
        for section_num in range(1, self.sections + 1):
            section_name = chr(64 + section_num)  # A, B, C, etc.
            result[section_name] = {}
            
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            time_strings = [
                '9:00-9:50', '9:50-10:40', 'BREAK', '11:00-11:50', 
                '11:50-12:40', 'LUNCH', '1:30-2:20', '2:20-3:10', '3:10-4:00'
            ]
            
            for day_idx, day in enumerate(days):
                result[section_name][day] = {}
                for period_idx, time_str in enumerate(time_strings):
                    result[section_name][day][time_str] = None
        
        # Fill in the scheduled classes
        for gene in timetable.genes:
            section_name = gene.assignment.section
            day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][gene.time_slot.day]
            time_str = gene.time_slot.time_str
            
            result[section_name][day_name][time_str] = {
                'subject': gene.assignment.subject.name,
                'faculty': gene.assignment.faculty.initials,
                'type': gene.assignment.subject.type
            }
        
        return result

def main():
    """Main function to run genetic algorithm"""
    if len(sys.argv) < 2:
        print("Usage: python genetic_timetable.py <input_json>")
        print("Example: python genetic_timetable.py input.json")
        return
    
    try:
        # Read input data
        input_file = sys.argv[1]
        print(f"Reading input from: {input_file}")
        
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        print(f"Input data loaded: {len(data.get('assignments', []))} assignments, {data.get('sections', 0)} sections")
        
        # Parse assignments
        assignments = []
        for i, assignment_data in enumerate(data['assignments']):
            try:
                subject = Subject(
                    assignment_data['subject']['name'],
                    assignment_data['subject']['credits'],
                    assignment_data['subject']['hours'],
                    assignment_data['subject']['type']
                )
                faculty = Faculty(
                    assignment_data['faculty']['name'],
                    assignment_data['faculty']['initials'],
                    assignment_data['faculty']['type']
                )
                assignments.append(Assignment(subject, faculty, assignment_data['section']))
            except KeyError as e:
                print(f"Error parsing assignment {i}: Missing key {e}")
                continue
        
        sections = data.get('sections', 1)
        
        if not assignments:
            print("No valid assignments found in input data")
            return
        
        print(f"Parsed {len(assignments)} valid assignments")
        
        # Generate timetable
        generator = GeneticTimetableGenerator(assignments, sections)
        best_timetable = generator.generate()
        
        # Convert to output format
        result = generator.timetable_to_dict(best_timetable)
        result['fitness'] = best_timetable.fitness
        result['metadata'] = {
            'total_assignments': len(assignments),
            'sections': sections,
            'generation_time': str(datetime.now()),
            'algorithm': 'genetic_algorithm_v2'
        }
        
        # Output result
        print("\n=== TIMETABLE GENERATION COMPLETE ===")
        print(json.dumps(result, indent=2))
        
    except FileNotFoundError:
        print(f"Error: Input file '{sys.argv[1]}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Add missing import
from datetime import datetime

if __name__ == "__main__":
    main()
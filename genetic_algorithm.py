import random
import copy

class TimetableGA:
    def __init__(self, assignments, faculty_schedules, config):
        self.assignments = assignments
        self.faculty_schedules = faculty_schedules
        self.config = config
        self.periods_to_schedule = self._create_periods()

        # --- GA Parameters ---
        self.population_size = 50
        self.max_generations = 200  # Strict termination condition
        self.mutation_rate = 0.1
        self.crossover_rate = 0.8
        self.elitism_count = 2

    def _create_periods(self):
        """Create a flat list of all individual class periods to be scheduled."""
        periods = []
        for sub in self.assignments:
            # Handle all labs as 2-hour blocks.
            if sub['type'].lower() == 'lab' and sub.get('weekly_hours', 0) >= 2:
                num_lab_blocks = sub['weekly_hours'] // 2
                for _ in range(num_lab_blocks):
                    periods.append({'subject': sub, 'duration': 2, 'is_lab': True})
            # Handle theory classes
            else:
                for _ in range(sub['weekly_hours']):
                    periods.append({'subject': sub, 'duration': 1, 'is_lab': False})
        return periods

    def _create_individual(self):
        """Creates a single random timetable (an individual chromosome)."""
        timetable = {day: {} for day in self.config['days']}
        
        # Create a temporary copy of periods to place
        periods = random.sample(self.periods_to_schedule, len(self.periods_to_schedule))

        for period in periods:
            placed = False
            # Try to place each period randomly
            for _ in range(100): # Limit attempts to prevent infinite loops
                day = random.choice(self.config['days'])
                
                if period['duration'] > 1: # Lab blocks
                    possible_starts = [slot for slot in self.config['lab_slots'] if slot + period['duration'] <= self.config['slots_per_day']]
                    if not possible_starts: continue
                    start_slot = random.choice(possible_starts)
                    
                    # Check if block is free
                    is_free = all(slot not in timetable[day] for slot in range(start_slot, start_slot + period['duration']))
                    if is_free:
                        for i in range(period['duration']):
                            timetable[day][start_slot + i] = period
                        placed = True
                        break
                else: # Theory
                    start_slot = random.randint(0, self.config['slots_per_day'] - 1)
                    if start_slot not in timetable[day]:
                        timetable[day][start_slot] = period
                        placed = True
                        break
        return timetable

    def _calculate_fitness(self, timetable):
        """Calculates the fitness of a timetable. Higher is better."""
        fitness = 1000
        
        # --- Hard Constraints (High Penalties) ---
        # 1. Faculty Clash: Check for clashes within this section and with global schedule
        faculty_clashes = 0
        temp_faculty_schedule = {}
        for day, slots in timetable.items():
            for slot_idx, period in slots.items():
                faculty_name = period['subject']['faculty']
                # Check for clash within the same generated timetable
                if (faculty_name, day, slot_idx) in temp_faculty_schedule:
                    faculty_clashes += 1
                temp_faculty_schedule[(faculty_name, day, slot_idx)] = True
                # Check for clash with other sections/departments
                if self.faculty_schedules.get(faculty_name, {}).get(day, {}).get(slot_idx):
                    faculty_clashes += 1
        fitness -= faculty_clashes * 100

        # --- Soft Constraints (Lower Penalties) ---
        # 1. Gaps in the day (prefer classes to be clustered)
        for day in self.config['days']:
            day_slots = sorted(timetable[day].keys())
            if not day_slots: continue
            # Penalize gaps between first and last class
            gaps = (day_slots[-1] - day_slots[0] + 1) - len(day_slots)
            fitness -= gaps * 5

        # 2. Free hours at the end of the day (Bonus)
        for day in self.config['days']:
            day_slots = timetable[day].keys()
            if not day_slots:
                fitness += 10 # Bonus for a completely free day
                continue
            last_class_slot = max(day_slots)
            # Bonus for having the last slots of the day free
            if last_class_slot < self.config['slots_per_day'] - 1:
                fitness += (self.config['slots_per_day'] - 1 - last_class_slot) * 2

        return fitness

    def _selection(self, population_with_fitness):
        """Selects parents using tournament selection."""
        selected = []
        for _ in range(len(population_with_fitness)):
            tournament = random.sample(population_with_fitness, 3)
            winner = max(tournament, key=lambda x: x[1])
            selected.append(winner[0])
        return selected

    def _crossover(self, parent1, parent2):
        """Performs a day-based crossover."""
        if random.random() > self.crossover_rate:
            return parent1, parent2

        child1, child2 = copy.deepcopy(parent1), copy.deepcopy(parent2)
        crossover_day = random.choice(self.config['days'])
        
        # Swap the selected day between parents
        child1[crossover_day], child2[crossover_day] = child2[crossover_day], child1[crossover_day]

        # Simple repair mechanism to handle duplicates/missing classes (a full repair is complex)
        # This is a simplification; a production system might need a more robust repair function.
        # For now, we accept that crossover may produce invalid timetables that fitness will penalize.

        return child1, child2

    def _mutate(self, timetable):
        """Mutates a timetable by swapping two random periods."""
        if random.random() > self.mutation_rate:
            return timetable

        # Pick two random, non-empty slots to swap
        day1, day2 = random.choices(self.config['days'], k=2)
        
        slots1 = list(timetable[day1].keys())
        slots2 = list(timetable[day2].keys())

        if not slots1 or not slots2:
        if not slots1 or not slots2 or (day1 == day2 and len(slots1) < 2):
            return timetable # Cannot mutate if a day is empty

        slot1 = random.choice(slots1)
        slot2 = random.choice(slots2)

        period1 = timetable[day1][slot1]
        period2 = timetable[day2][slot2]

        # Simple swap, ignoring duration constraints for this mutation
        # A more advanced mutation would handle labs carefully
        if period1['duration'] == period2['duration']:
            timetable[day1][slot1], timetable[day2][slot2] = timetable[day2][slot2], timetable[day1][slot1]

        return timetable

    def run(self):
        """Main execution function to run the Genetic Algorithm."""
        # 1. Create initial population
        population = [self._create_individual() for _ in range(self.population_size)]

        best_timetable = None
        best_fitness = -float('inf')

        # 2. Start the evolution loop with a fixed number of generations
        for generation in range(self.max_generations):
            # Calculate fitness for each individual
            population_with_fitness = [(ind, self._calculate_fitness(ind)) for ind in population]

            # Find the best individual in the current generation
            current_best_ind, current_best_fit = max(population_with_fitness, key=lambda x: x[1])
            if current_best_fit > best_fitness:
                best_fitness = current_best_fit
                best_timetable = copy.deepcopy(current_best_ind)
            
            # --- Stopping Condition ---
            # Stop if a very high fitness score is achieved (optional)
            if best_fitness >= 950:
                print(f"✅ Ideal fitness reached at generation {generation+1}. Stopping early.")
                break

            # 3. Selection
            parents = self._selection(population_with_fitness)

            # 4. Crossover and Mutation
            next_generation = []
            
            # Elitism: carry over the best individuals
            sorted_population = sorted(population_with_fitness, key=lambda x: x[1], reverse=True)
            for i in range(self.elitism_count):
                next_generation.append(sorted_population[i][0])

            # Create the rest of the new generation
            while len(next_generation) < self.population_size:
                p1, p2 = random.sample(parents, 2)
                c1, c2 = self._crossover(p1, p2)
                next_generation.append(self._mutate(c1))
                if len(next_generation) < self.population_size:
                    next_generation.append(self._mutate(c2))
            
            population = next_generation
            
            if (generation + 1) % 20 == 0:
                print(f"  -> Generation {generation+1}/{self.max_generations}, Best Fitness: {best_fitness:.2f}")

        # Final formatting of the best timetable
        final_timetable = {day: {} for day in self.config['days']}
        if best_timetable:
            for day, slots in best_timetable.items():
                for slot_idx, period in slots.items():
                    final_timetable[day][slot_idx] = {
                        "subject_code": period['subject']['subCode'],
                        "faculty_name": period['subject']['faculty'],
                        "is_lab": period['is_lab']
                    }
        
        return final_timetable
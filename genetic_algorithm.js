/**
 * MIT Mysore Timetable Genetic Algorithm
 * Implements all 10 conditions with Supabase integration
 */

class GeneticTimetableGenerator {
    constructor(config) {
        this.department = config.department;
        this.semester = config.semester;
        this.year = config.year;
        this.academicYear = config.academicYear;
        this.sections = config.sections;
        this.subjects = config.subjects;
        this.faculty = config.faculty;
        
        // GA Parameters
        this.populationSize = 50;
        this.maxGenerations = 150;
        this.mutationRate = 0.15;
        this.crossoverRate = 0.8;
        this.elitismCount = 5;
        
        // Timetable Configuration
        this.days = ['Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        this.slotsPerDay = 6;
        this.breakSlots = [2, 4];
        this.labSlots = [[0, 1], [2, 3], [4, 5]];
        
        // Global faculty schedule (cross-section & cross-department tracking)
        this.globalFacultySchedule = {};
        this.globalLabSlotSchedule = {}; // NEW: Tracks lab slot usage across sections
        this.existingTimetables = [];
    }

    async loadExistingTimetables() {
        try {
            const { data, error } = await supabase
                .from('timetables')
                .select('*')
                .eq('academic_year', this.academicYear)
                .eq('year', this.year)
                .eq('semester', this.semester);
            if (error) throw error;
            this.existingTimetables = data || [];
            
            // Load existing schedules into global faculty schedule
            this.existingTimetables.forEach(entry => {
                const key = `${entry.faculty_name}_${entry.day}_${entry.time_slot}`;
                this.globalFacultySchedule[key] = entry.section;

                // NEW: Populate global lab schedule from existing timetables
                if (entry.is_lab && entry.block_id) { // Use the is_lab and block_id flags from the database
                    // Find which lab block this slot belongs to
                    const labSlot = this.labSlots.find(([start, end]) => entry.time_slot === start || entry.time_slot === end);
                    if (labSlot) {
                        const labKey = `${entry.day}_${labSlot[0]}`; // Use start slot as the key
                        this.globalLabSlotSchedule[labKey] = entry.section;
                    }
                }
            });
            
            console.log('✓ Loaded existing timetables:', this.existingTimetables.length);
        } catch (error) {
            console.error('Error loading existing timetables:', error);
            this.existingTimetables = [];
        }
    }

    createPeriodsToSchedule(sectionAssignments) {
        const periods = [];
        sectionAssignments.forEach(assignment => {
            const isLab = assignment.type.toLowerCase() === 'lab';
            const weeklyHours = assignment.weekly_hours || assignment.credits || 3;
            const subCode = assignment.subCode || assignment.subject;
            
            if (isLab) {
                const sessions = Math.ceil(weeklyHours / 2);
                for (let i = 0; i < sessions; i++) {
                    periods.push({
                        subject: assignment,
                        blockId: `${subCode}_lab_${i}`, // Assign a consistent, unique blockId upfront
                        duration: 2,
                        isLab: true,
                        sessionId: i
                    });
                }
            } else {
                for (let i = 0; i < weeklyHours; i++) {
                    periods.push({
                        subject: assignment,
                        duration: 1,
                        isLab: false
                    });
                }
            }
        });
        return periods;
    }

    createIndividual(periods) {
        const timetable = {};
        this.days.forEach(day => {
            timetable[day] = {};
        });

        // Separate labs and theory
        const labs = periods.filter(p => p.duration === 2);
        const theory = periods.filter(p => p.duration === 1);

        // --- GUARANTEED PLACEMENT FOR LABS ---
        for (const lab of labs) {
            let placed = false;
            const shuffledDays = [...this.days].sort(() => 0.5 - Math.random());
            const shuffledLabSlots = [...this.labSlots].sort(() => 0.5 - Math.random());

            for (const day of shuffledDays) {
                for (const labSlotPair of shuffledLabSlots) {
                    const [start, end] = labSlotPair;
                    if (!timetable[day][start] && !timetable[day][end]) {
                        const labBlock = { ...lab };
                        timetable[day][start] = labBlock;
                        timetable[day][end] = labBlock;
                        placed = true;
                        break; // Exit inner loop
                    }
                }
                if (placed) break; // Exit outer loop
            }
            if (!placed) {
                console.warn(`Could not place lab: ${lab.subject.subject}`);
            }
        }

        // --- GUARANTEED PLACEMENT FOR THEORY ---
        const availableSlots = [];
        this.days.forEach(day => {
            for (let slot = 0; slot < this.slotsPerDay; slot++) {
                if (!timetable[day][slot]) {
                    availableSlots.push({ day, slot });
                }
            }
        });
        
        // Shuffle the available slots
        for (let i = availableSlots.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [availableSlots[i], availableSlots[j]] = [availableSlots[j], availableSlots[i]];
        }

        for (const theoryPeriod of theory) {
            if (availableSlots.length > 0) {
                const slotToFill = availableSlots.pop();
                timetable[slotToFill.day][slotToFill.slot] = theoryPeriod;
            } else {
                console.warn(`Could not place theory period: ${theoryPeriod.subject.subject}. No available slots left.`);
            }
        }

        return timetable;
    }

    calculateFitness(timetable, sectionName) {
        let fitness = 1000;
        
        // CONDITION 1 & 2: No faculty clash (within section & across sections)
        const facultySchedule = {};
        for (const day of this.days) {
            for (let slot = 0; slot < this.slotsPerDay; slot++) {
                const period = timetable[day][slot];
                if (period) {
                    const faculty = period.subject.faculty;
                    const key = `${faculty}_${day}_${slot}`;
                    if (facultySchedule[key]) {
                        fitness -= 100;
                    }
                    facultySchedule[key] = true;
                    
                    if (this.isFacultyBusyGlobally(faculty, day, slot, sectionName)) {
                        fitness -= 100;
                    }
                }
            }
        }
        
        // CONDITION 3: Weekly hours completion
        const subjectHours = {};
        for (const day of this.days) {
            for (let slot = 0; slot < this.slotsPerDay; slot++) {
                const period = timetable[day][slot];
                if (period) {
                    const subCode = period.subject.subCode || period.subject.subject;
                    subjectHours[subCode] = (subjectHours[subCode] || 0) + 1;
                }
            }
        }
        
        for (const assignment of this.sections.find(s => s.name === sectionName).assignments) {
            const expected = assignment.weekly_hours || assignment.credits || 3;
            const actual = subjectHours[assignment.subCode || assignment.subject] || 0;
            if (actual !== expected) {
                fitness -= Math.abs(expected - actual) * 20;
            }
        }
        
        // CONDITION 4: Lab rules (2hrs continuous, different days for multiple sessions)
        const labSessions = {};
        const labDays = {};
        const processedLabs = new Set();
        
        for (const day of this.days) {
            for (let slot = 0; slot < this.slotsPerDay; slot++) {
                const period = timetable[day][slot];
                if (period && period.isLab) {
                    const blockId = period.blockId;
                    if (processedLabs.has(blockId)) continue;
                    
                    const subCode = period.subject.subCode || period.subject.subject;
                    const nextSlot = slot + 1;
                    
                    // Check if lab occupies both current and next slot
                    if (nextSlot < this.slotsPerDay && timetable[day][nextSlot] && 
                        timetable[day][nextSlot].blockId === blockId) {
                        
                        // Verify it's in allowed continuous slots
                        const isContinuous = this.labSlots.some(([s, e]) => s === slot && e === nextSlot);
                        if (!isContinuous) {
                            fitness -= 100;
                        }
                        
                        if (!labSessions[subCode]) {
                            labSessions[subCode] = [];
                            labDays[subCode] = new Set();
                        }
                        labSessions[subCode].push({ day, slot });
                        labDays[subCode].add(day);

                        // NEW: Check for global lab slot clash
                        if (this.isLabSlotBusyGlobally(day, slot, sectionName)) {
                            fitness -= 100;
                        }

                        processedLabs.add(blockId);
                    } else {
                        // Lab not continuous - heavy penalty
                        fitness -= 100;
                    }
                }
            }
        }
        
        for (const [subCode, sessions] of Object.entries(labSessions)) {
            if (sessions.length >= 2) {
                if (labDays[subCode].size < sessions.length) {
                    fitness -= 100;
                }
                // Explicitly check if a 4-hour lab (2 sessions) is on the same day
                if (sessions.length === 2 && labDays[subCode].size === 1) {
                    fitness -= 150; // Heavy penalty for 4-hour lab on the same day
                }
            }
        }
        
        // CONDITION 5: Faculty workload check
        const facultyLoad = {};
        for (const day of this.days) {
            for (let slot = 0; slot < this.slotsPerDay; slot++) {
                const period = timetable[day][slot];
                if (period) {
                    const faculty = period.subject.faculty;
                    facultyLoad[faculty] = (facultyLoad[faculty] || 0) + 1;
                }
            }
        }
        
        for (const [faculty, load] of Object.entries(facultyLoad)) {
            if (load > 25) {
                fitness -= (load - 25) * 10;
            }
        }
        
        // CONDITION 6 (NEW): No same theory subject on the same day
        for (const day of this.days) {
            const dailyTheorySubjects = {};
            for (let slot = 0; slot < this.slotsPerDay; slot++) {
                const period = timetable[day][slot];
                if (period && !period.isLab) { // Only check for theory subjects
                    const subCode = period.subject.subCode || period.subject.subject;
                    dailyTheorySubjects[subCode] = (dailyTheorySubjects[subCode] || 0) + 1;
                }
            }
            
            for (const count of Object.values(dailyTheorySubjects)) {
                if (count > 1) {
                    fitness -= (count - 1) * 50; // Heavy penalty for each repetition
                }
            }
        }
        
        // CONDITION 7: Subject spread (avoid consecutive days)
        for (let i = 0; i < this.days.length - 1; i++) {
            const day1 = this.days[i];
            const day2 = this.days[i + 1];
            
            for (let slot = 0; slot < this.slotsPerDay; slot++) {
                const p1 = timetable[day1][slot];
                const p2 = timetable[day2][slot];
                
                if (p1 && p2) {
                    const sub1 = p1.subject.subCode || p1.subject.subject;
                    const sub2 = p2.subject.subCode || p2.subject.subject;
                    if (sub1 === sub2) {
                        fitness -= 5;
                    }
                }
            }
        }
        
        // CONDITION 9: No same subject at same time daily
        for (let slot = 0; slot < this.slotsPerDay; slot++) {
            const subjectsAtSlot = new Set();
            for (const day of this.days) {
                const period = timetable[day][slot];
                if (period) {
                    const subCode = period.subject.subCode || period.subject.subject;
                    if (subjectsAtSlot.has(subCode)) {
                        fitness -= 10;
                    }
                    subjectsAtSlot.add(subCode);
                }
            }
        }
        
        // CONDITION 10: Even distribution (minimize gaps)
        for (const day of this.days) {
            const slots = Object.keys(timetable[day]).map(Number).sort((a, b) => a - b);
            if (slots.length > 0) {
                const gaps = (slots[slots.length - 1] - slots[0] + 1) - slots.length;
                fitness -= gaps * 5;
            }
        }
        
        // BONUS: Free hours at end of day
        for (const day of this.days) {
            const slots = Object.keys(timetable[day]).map(Number);
            if (slots.length > 0) {
                const lastSlot = Math.max(...slots);
                if (lastSlot < this.slotsPerDay - 1) {
                    fitness += (this.slotsPerDay - 1 - lastSlot) * 2;
                }
            }
        }
        
        return fitness;
    }

    isFacultyBusyGlobally(faculty, day, slot, currentSection) {
        const key = `${faculty}_${day}_${slot}`;
        return this.globalFacultySchedule[key] && this.globalFacultySchedule[key] !== currentSection;
    }

    markFacultyBusy(faculty, day, slot, sectionName) {
        const key = `${faculty}_${day}_${slot}`;
        this.globalFacultySchedule[key] = sectionName;
    }

    isLabSlotBusyGlobally(day, startSlot, currentSection) {
        const key = `${day}_${startSlot}`;
        return this.globalLabSlotSchedule[key] && this.globalLabSlotSchedule[key] !== currentSection;
    }

    markLabSlotBusy(day, startSlot, sectionName) {
        const key = `${day}_${startSlot}`;
        this.globalLabSlotSchedule[key] = sectionName;
    }

    selection(populationWithFitness) {
        const selected = [];
        for (let i = 0; i < populationWithFitness.length; i++) {
            const tournament = [];
            for (let j = 0; j < 3; j++) {
                const idx = Math.floor(Math.random() * populationWithFitness.length);
                tournament.push(populationWithFitness[idx]);
            }
            const winner = tournament.reduce((best, curr) => curr[1] > best[1] ? curr : best);
            selected.push(winner[0]);
        }
        return selected;
    }

    crossover(parent1, parent2) {
        if (Math.random() > this.crossoverRate) {
            return [JSON.parse(JSON.stringify(parent1)), JSON.parse(JSON.stringify(parent2))];
        }
        
        const child1 = JSON.parse(JSON.stringify(parent1)); // Deep copy
        const child2 = JSON.parse(JSON.stringify(parent2)); // Deep copy

        // Crossover point is a random day and slot
        const day = this.days[Math.floor(Math.random() * this.days.length)];
        const slot = Math.floor(Math.random() * this.slotsPerDay);

        // Swap everything from the crossover point onwards
        for (let i = this.days.indexOf(day); i < this.days.length; i++) {
            const currentDay = this.days[i];
            const startSlot = (currentDay === day) ? slot : 0;
            for (let j = startSlot; j < this.slotsPerDay; j++) {
                // --- DEFINITIVE LAB-AWARE CROSSOVER ---
                const p1 = child1[currentDay][j];
                const p2 = child2[currentDay][j];
                
                // Check if the current slot 'j' is the start of a lab block.
                const isLabStartSlot = this.labSlots.some(([s, e]) => s === j);

                if (isLabStartSlot) {
                    const p1_is_lab_block = p1 && p1.isLab && child1[currentDay][j+1]?.blockId === p1.blockId;
                    const p2_is_lab_block = p2 && p2.isLab && child2[currentDay][j+1]?.blockId === p2.blockId;

                    // If either parent has a complete lab block here, swap the entire block atomically.
                    if (p1_is_lab_block || p2_is_lab_block) {
                        [child1[currentDay][j], child2[currentDay][j]] = [child2[currentDay][j], child1[currentDay][j]];
                        [child1[currentDay][j + 1], child2[currentDay][j + 1]] = [child2[currentDay][j + 1], child1[currentDay][j + 1]];
                        j++; // Manually advance the counter to skip the second half of the block.
                        continue;
                    }
                }

                // Swap the single period
                [child1[currentDay][j], child2[currentDay][j]] = [child2[currentDay][j], child1[currentDay][j]];
            }
        }

        return [child1, child2];
    }

    mutate(timetable) {
        if (Math.random() > this.mutationRate) return timetable;

        const day1 = this.days[Math.floor(Math.random() * this.days.length)];
        const slot1 = Math.floor(Math.random() * this.slotsPerDay);
        const day2 = this.days[Math.floor(Math.random() * this.days.length)];
        const slot2 = Math.floor(Math.random() * this.slotsPerDay);

        const period1 = timetable[day1][slot1];
        const period2 = timetable[day2][slot2];

        // If swapping a lab, find its block and swap the whole thing
        if (period1 && period1.isLab) {
            const [start1, end1] = this.labSlots.find(([s, e]) => s === slot1 || e === slot1);
            
            // Case 1: Swapping a lab with another lab
            if (period2 && period2.isLab) {
                const [start2, end2] = this.labSlots.find(([s, e]) => s === slot2 || e === slot2);
                // Swap entire blocks
                [timetable[day1][start1], timetable[day2][start2]] = [timetable[day2][start2], timetable[day1][start1]];
                [timetable[day1][end1], timetable[day2][end2]] = [timetable[day2][end2], timetable[day1][end1]];
            } else { 
                // Case 2: Moving a lab to an empty slot
                // Find a random empty lab slot and move it there. This is more robust than swapping with theory.
                const shuffledDays = [...this.days].sort(() => 0.5 - Math.random());
                const shuffledLabSlots = [...this.labSlots].sort(() => 0.5 - Math.random());

                for (const day of shuffledDays) {
                    for (const [start, end] of shuffledLabSlots) {
                        // Ensure the target slot is actually empty
                        if (timetable[day] && !timetable[day][start] && !timetable[day][end]) {
                            // Move the lab block to the new empty slot
                            timetable[day][start] = timetable[day1][start1];
                            timetable[day][end] = timetable[day1][end1];
                            // Clear the old slot
                            delete timetable[day1][start1];
                            delete timetable[day1][end1];
                            // A successful move is a complete mutation.
                            return timetable; // Exit after successful move
                        }
                    }
                }
            }
        } else if (period2 && period2.isLab) {
            // Symmetrical case: if the second period is a lab, move it to a new empty slot.
            // This avoids recursion and ensures the logic is symmetrical.
            const [start2, end2] = this.labSlots.find(([s, e]) => s === slot2 || e === slot2);
            const shuffledDays = [...this.days].sort(() => 0.5 - Math.random());
            const shuffledLabSlots = [...this.labSlots].sort(() => 0.5 - Math.random());

            for (const day of shuffledDays) {
                for (const [start, end] of shuffledLabSlots) {
                    if (timetable[day] && !timetable[day][start] && !timetable[day][end]) {
                        // Move the lab block to the new empty slot
                        timetable[day][start] = timetable[day2][start2];
                        timetable[day][end] = timetable[day2][end2];
                        // Clear the old slot
                        delete timetable[day2][start2];
                        delete timetable[day2][end2];
                        return timetable; // Exit after successful move
                    }
                }
            }
        } else {
            // Standard swap for two theory/empty periods
            if (day1 === day2 && slot1 === slot2) return timetable; // Avoid swapping a slot with itself
            [timetable[day1][slot1], timetable[day2][slot2]] = [timetable[day2][slot2], timetable[day1][slot1]];
        }
        return timetable;
    }

    async run() {
        await this.loadExistingTimetables();
        
        const allTimetables = {};
        
        for (const section of this.sections) {
            console.log(`\n🧬 Generating timetable for Section ${section.name}...`);
            
            const periods = this.createPeriodsToSchedule(section.assignments);
            let population = [];
            
            for (let i = 0; i < this.populationSize; i++) {
                let individual = this.createIndividual(periods);
                individual = this._repairTimetable(individual, periods); // Ensure initial population is valid
                population.push(individual);
            }
            
            let bestTimetable = null;
            let bestFitness = -Infinity;
            
            for (let gen = 0; gen < this.maxGenerations; gen++) {
                const populationWithFitness = population.map(ind => [ind, this.calculateFitness(ind, section.name)]);
                
                const currentBest = populationWithFitness.reduce((best, curr) => curr[1] > best[1] ? curr : best);
                
                if (currentBest[1] > bestFitness) {
                    bestFitness = currentBest[1];
                    bestTimetable = JSON.parse(JSON.stringify(currentBest[0]));
                }
                
                if (bestFitness >= 950) {
                    console.log(`✅ Optimal fitness reached at generation ${gen + 1}`);
                    break;
                }
                
                const parents = this.selection(populationWithFitness);
                const nextGeneration = [];
                
                const sorted = populationWithFitness.sort((a, b) => b[1] - a[1]);
                for (let i = 0; i < this.elitismCount; i++) {
                    nextGeneration.push(sorted[i][0]);
                }
                
                while (nextGeneration.length < this.populationSize) {
                    const p1 = parents[Math.floor(Math.random() * parents.length)];
                    const p2 = parents[Math.floor(Math.random() * parents.length)];
                    let [c1, c2] = this.crossover(p1, p2);
                    
                    c1 = this.mutate(c1);
                    c1 = this._repairTimetable(c1, periods); // Repair after crossover and mutation
                    nextGeneration.push(c1);

                    if (nextGeneration.length < this.populationSize) {
                        c2 = this.mutate(c2);
                        c2 = this._repairTimetable(c2, periods); // Repair after crossover and mutation
                        nextGeneration.push(c2);
                    }
                }
                
                population = nextGeneration;
                
                if ((gen + 1) % 30 === 0) {
                    console.log(`  Generation ${gen + 1}/${this.maxGenerations}, Best Fitness: ${bestFitness.toFixed(2)}`);
                }
            }
            
            for (const day of this.days) {
                for (let slot = 0; slot < this.slotsPerDay; slot++) {
                    const period = bestTimetable[day][slot];
                    if (period) {
                        this.markFacultyBusy(period.subject.faculty, day, slot, section.name);
                        // NEW: Mark lab slots as busy globally
                        if (period.isLab) {
                            const labSlotInfo = this.labSlots.find(([start, end]) => slot === start || slot === end);
                            if (labSlotInfo) {
                                // Mark the block by its start slot, but only once per block
                                if (slot === labSlotInfo[0]) this.markLabSlotBusy(day, labSlotInfo[0], section.name);
                            }
                        }
                    }
                }
            }
            
            const formattedTimetable = {};
            for (const day of this.days) {
                formattedTimetable[day] = {};
                for (let slot = 0; slot < this.slotsPerDay; slot++) {
                    const period = bestTimetable[day][slot];
                    if (period) {
                        formattedTimetable[day][slot] = {
                            subject_code: period.subject.subCode || period.subject.subject,
                            subject_name: period.subject.subject,
                            faculty_name: period.subject.faculty,
                            block_id: period.blockId, // NEW: Add blockId to the formatted output
                            is_lab: period.isLab
                        };
                    }
                }
            }
            
            allTimetables[section.name] = formattedTimetable;
            console.log(`✅ Section ${section.name} completed with fitness: ${bestFitness.toFixed(2)}`);
        }
        
        return allTimetables;
    }

    _repairTimetable(timetable, allPeriods) {
        const repairedTimetable = timetable;

        // --- 1. Build a count of required periods for every subject/lab block ---
        const requiredCounts = {};
        allPeriods.forEach(p => {
            const key = p.isLab ? p.blockId : p.subject.subjectId;
            requiredCounts[key] = (requiredCounts[key] || 0) + 1;
        });

        // --- 2. Get current counts from the timetable ---
        const currentCounts = {};
        const placedBlocks = new Set(); // To avoid double-counting labs
        for (const day of this.days) {
            for (let slot = 0; slot < this.slotsPerDay; slot++) {
                const period = repairedTimetable[day][slot];
                if (period) {
                    const key = period.isLab ? period.blockId : period.subject.subjectId;
                    // For labs, only count them once per block
                    if (period.isLab) {
                        if (!placedBlocks.has(period.blockId)) {
                            currentCounts[key] = (currentCounts[key] || 0) + 2; // Labs are 2 hours
                            placedBlocks.add(period.blockId);
                        }
                    } else {
                        currentCounts[key] = (currentCounts[key] || 0) + 1;
                    }
                }
            }
        }

        // --- 3. Find and fix discrepancies (deficits and surpluses) ---

        // Remove surplus periods first to create space
        for (const key in currentCounts) {
            const required = requiredCounts[key] || 0;
            let current = currentCounts[key];
            if (current > required) {
                const surplus = current - required;
                let removedCount = 0;
                for (const day of this.days) {
                    for (let slot = 0; slot < this.slotsPerDay; slot++) {
                        if (removedCount >= surplus) break;
                        const period = repairedTimetable[day][slot];
                        if (period) {
                            const periodKey = period.isLab ? period.blockId : period.subject.subjectId;
                            if (periodKey === key) {
                                if (period.isLab) {
                                    // Find the lab block and remove it
                                    const labSlot = this.labSlots.find(([start, end]) => repairedTimetable[day][start]?.blockId === key);
                                    if (labSlot) {
                                        delete repairedTimetable[day][labSlot[0]];
                                        delete repairedTimetable[day][labSlot[1]];
                                        removedCount += 2;
                                    }
                                } else {
                                    delete repairedTimetable[day][slot];
                                    removedCount += 1;
                                }
                            }
                        }
                    }
                    if (removedCount >= surplus) break;
                }
            }
        }

        // Add missing periods
        for (const key in requiredCounts) {
            const required = requiredCounts[key];
            const current = currentCounts[key] || 0;
            if (current < required) {
                const deficit = required - current;
                const periodTemplate = allPeriods.find(p => (p.isLab ? p.blockId : p.subject.subjectId) === key);
                
                if (periodTemplate) {
                    let addedCount = 0;
                    // Find empty slots and add the period
                    for (const day of this.days) {
                        if (addedCount >= deficit) break;
                        if (periodTemplate.isLab) {
                            const labSlot = this.labSlots.find(([start, end]) => !repairedTimetable[day][start] && !repairedTimetable[day][end]);
                            if (labSlot) {
                                repairedTimetable[day][labSlot[0]] = periodTemplate;
                                repairedTimetable[day][labSlot[1]] = periodTemplate;
                                addedCount += 2;
                            }
                        } else {
                            for (let slot = 0; slot < this.slotsPerDay; slot++) {
                                if (addedCount >= deficit) break;
                                if (!repairedTimetable[day][slot]) {
                                    repairedTimetable[day][slot] = periodTemplate;
                                    addedCount += 1;
                                }
                            }
                        }
                    }
                }
            }
        }

        return repairedTimetable;
    }
}


if (typeof window !== 'undefined') {
    window.GeneticTimetableGenerator = GeneticTimetableGenerator;
}

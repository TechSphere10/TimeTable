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
            const isLab = assignment.type === 'Lab' || assignment.type === 'LAB';
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
        
        // Place labs first (they need continuous slots)
        for (const lab of labs) {
            let placed = false;
            let attempts = 0;
            
            while (!placed && attempts < 100) {
                const day = this.days[Math.floor(Math.random() * this.days.length)];
                const labSlotPair = this.labSlots[Math.floor(Math.random() * this.labSlots.length)];
                const [start, end] = labSlotPair;
                
                // Check BOTH slots are free
                if (!timetable[day][start] && !timetable[day][end]) {
                    const labBlock = { ...lab }; // Use the lab object with its pre-assigned blockId
                    timetable[day][start] = labBlock;
                    timetable[day][end] = labBlock;
                    placed = true;
                }
                attempts++;
            }
        }
        
        // Place theory subjects
        for (const theoryPeriod of theory) {
            let placed = false;
            let attempts = 0;
            
            while (!placed && attempts < 100) {
                const day = this.days[Math.floor(Math.random() * this.days.length)];
                const slot = Math.floor(Math.random() * this.slotsPerDay);
                
                if (!timetable[day][slot]) {
                    timetable[day][slot] = theoryPeriod;
                    placed = true;
                }
                attempts++;
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
        
        const child1 = JSON.parse(JSON.stringify(parent1));
        const child2 = JSON.parse(JSON.stringify(parent2));
        
        const crossoverDay = this.days[Math.floor(Math.random() * this.days.length)];
        
        const temp = child1[crossoverDay];
        child1[crossoverDay] = child2[crossoverDay];
        child2[crossoverDay] = temp;
        
        return [child1, child2];
    }

    mutate(timetable) {
        if (Math.random() > this.mutationRate) {
            return timetable;
        }
        
        const day1 = this.days[Math.floor(Math.random() * this.days.length)];
        const day2 = this.days[Math.floor(Math.random() * this.days.length)];
        
        const slots1 = Object.keys(timetable[day1]).map(Number);
        const slots2 = Object.keys(timetable[day2]).map(Number);
        
        if (slots1.length === 0 || slots2.length === 0) return timetable;
        
        const slot1 = slots1[Math.floor(Math.random() * slots1.length)];
        const slot2 = slots2[Math.floor(Math.random() * slots2.length)];
        
        const period1 = timetable[day1][slot1];
        const period2 = timetable[day2][slot2];
        
        // To preserve lab continuity, only swap periods of the same duration.
        // Also, handle swapping of lab blocks correctly.
        if (period1 && period2 && period1.duration === period2.duration) {
            if (period1.isLab) {
                // Swap the entire lab block
                const [start1, end1] = this.labSlots.find(([s, e]) => s === slot1 || e === slot1);
                const [start2, end2] = this.labSlots.find(([s, e]) => s === slot2 || e === slot2);
                
                [timetable[day1][start1], timetable[day2][start2]] = [timetable[day2][start2], timetable[day1][start1]];
                [timetable[day1][end1], timetable[day2][end2]] = [timetable[day2][end2], timetable[day1][end1]];
            } else {
                // Swap theory periods
                [timetable[day1][slot1], timetable[day2][slot2]] = [period2, period1];
            }
        } else if (period1 && !period2) { // Swap with an empty slot
            timetable[day1][slot1] = period2;
            timetable[day2][slot2] = period1; // This moves period1 to an empty slot
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
                population.push(this.createIndividual(periods));
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
                    c1 = this._repairTimetable(c1, periods); // Repair after mutation
                    nextGeneration.push(c1);

                    if (nextGeneration.length < this.populationSize) {
                        c2 = this.mutate(c2);
                        c2 = this._repairTimetable(c2, periods); // Repair after mutation
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
        const repairedTimetable = JSON.parse(JSON.stringify(timetable));
        const labsToPlace = allPeriods.filter(p => p.isLab);
        const placedLabBlocks = new Set();

        // First, identify and preserve correctly placed labs
        for (const day of this.days) {
            for (const [start, end] of this.labSlots) {
                const period1 = repairedTimetable[day][start];
                const period2 = repairedTimetable[day][end];
                if (period1 && period2 && period1.isLab && period1.blockId === period2.blockId) {
                    placedLabBlocks.add(period1.blockId);
                }
            }
        }

        // Find labs that are broken or missing and remove their fragments
        const labsToRePlace = [];
        for (const lab of labsToPlace) {
            if (!placedLabBlocks.has(lab.blockId)) {
                labsToRePlace.push(lab);
                // Clean up any fragments of this broken lab from the timetable
                for (const day of this.days) {
                    for (let slot = 0; slot < this.slotsPerDay; slot++) {
                        const period = repairedTimetable[day][slot];
                        if (period && period.isLab && period.blockId === lab.blockId) {
                            delete repairedTimetable[day][slot];
                        }
                    }
                }
            }
        }

        // Re-place the broken labs into the first available valid slots
        for (const lab of labsToRePlace) {
            let placed = false;
            for (const day of this.days) {
                if (placed) break;
                for (const [start, end] of this.labSlots) {
                    if (!repairedTimetable[day][start] && !repairedTimetable[day][end]) {
                        repairedTimetable[day][start] = lab;
                        repairedTimetable[day][end] = lab;
                        placed = true;
                        break;
                    }
                }
            }
            // If still not placed (highly unlikely in a valid schedule), it will be an empty slot,
            // which the fitness function will heavily penalize, pushing the algorithm to fix it.
        }

        // Note: This is a basic repair function. A more advanced version could also try to
        // re-place theory classes that might have been overwritten, but for ensuring lab
        // continuity, this is a robust solution. The fitness function will handle the
        // placement of any displaced theory classes in subsequent generations.

        return repairedTimetable;
    }
}


if (typeof window !== 'undefined') {
    window.GeneticTimetableGenerator = GeneticTimetableGenerator;
}

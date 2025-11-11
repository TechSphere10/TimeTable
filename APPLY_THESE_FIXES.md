# Critical Fixes to Apply - DO THIS NOW

## 🔴 ISSUE 1: Labs at Same Time for All Sections

**In enhanced.htm, add this BEFORE the `createAdvancedTimetable` function:**

```javascript
// Global faculty schedule tracker
const globalFacultySchedule = {};

function initGlobalSchedule() {
    globalFacultySchedule = {};
}

function markFacultyBusy(facultyName, day, slot) {
    if (!globalFacultySchedule[facultyName]) {
        globalFacultySchedule[facultyName] = {};
    }
    if (!globalFacultySchedule[facultyName][day]) {
        globalFacultySchedule[facultyName][day] = new Set();
    }
    globalFacultySchedule[facultyName][day].add(slot);
}

function isFacultyBusy(facultyName, day, slot) {
    return globalFacultySchedule[facultyName]?.[ day]?.has(slot) || false;
}
```

**In `callPythonGA` function, add at the START:**

```javascript
async function callPythonGA(inputData) {
    try {
        initGlobalSchedule(); // ADD THIS LINE
        console.log('Python GA Input:', inputData);
        const result = {};
        // ... rest of code
```

**In `createAdvancedTimetable`, REPLACE the lab placement section with:**

```javascript
// Place labs first with GLOBAL faculty tracking
allSessions.filter(s => s.type === 'lab').forEach(item => {
    let placed = false;
    for (const day of days) {
        if (placed) break;
        if (dailySubjects[day].has(item.code)) continue;
        if (dailyLabs[day].size > 0) continue;
        if (day === 'Friday') continue;
        
        for (const slotGroup of continuousSlots) {
            if (placed) break;
            // Check GLOBAL faculty availability
            const canPlace = slotGroup.every(slot => 
                timetable[day][slot] === null && 
                !isFacultyBusy(item.faculty, day, slot)
            );
            
            if (canPlace) {
                const displayName = item.code.toLowerCase().includes('lab') ? item.code : `${item.code} Lab`;
                slotGroup.forEach(slot => {
                    timetable[day][slot] = {
                        subject_code: item.code,
                        subject_name: displayName,
                        faculty_name: item.faculty,
                        section: section,
                        type: 'lab'
                    };
                    markFacultyBusy(item.faculty, day, slot); // MARK GLOBALLY
                });
                dailySubjects[day].add(item.code);
                dailyLabs[day].add(item.code);
                placed = true;
                console.log(`✅ Placed lab ${item.code} for section ${section} on ${day} slots ${slotGroup.join(',')}`);
            }
        }
    }
    if (!placed) {
        console.warn(`❌ Could not place lab ${item.code} for section ${section}`);
    }
});
```

**In theory placement, REPLACE with:**

```javascript
// Place theory subjects with GLOBAL faculty tracking
allSessions.filter(s => s.type === 'theory').forEach(item => {
    let placed = false;
    for (const day of days) {
        if (placed) break;
        if (dailySubjects[day].has(item.code)) continue;
        
        for (let slot = 0; slot < 6; slot++) {
            if (placed) break;
            if (day === 'Friday' && slot === 5) continue;
            
            // Check GLOBAL faculty availability
            if (timetable[day][slot] === null && !isFacultyBusy(item.faculty, day, slot)) {
                timetable[day][slot] = {
                    subject_code: item.code,
                    subject_name: item.code,
                    faculty_name: item.faculty,
                    section: section,
                    type: 'theory'
                };
                markFacultyBusy(item.faculty, day, slot); // MARK GLOBALLY
                dailySubjects[day].add(item.code);
                placed = true;
                console.log(`✅ Placed theory ${item.code} for section ${section} on ${day} slot ${slot}`);
            }
        }
    }
    if (!placed) {
        console.warn(`❌ Could not place theory ${item.code} for section ${section}`);
    }
});
```

## 🔴 ISSUE 2: Weekly Hours Not Matching

**The code already calculates correctly:**
- Labs: `Math.floor(weeklyHours / 2)` sessions
- Theory: `weeklyHours` sessions

**But ensure NO SAME SUBJECT ON SAME DAY. The fix above already handles this with `dailySubjects[day].has(item.code)`**

## 🔴 ISSUE 3: Smart Swap Not Working

**REPLACE the entire `toggleSwapMode` and `handleCellClick` functions:**

```javascript
let swapMode = false;
let selectedCell = null;

function toggleSwapMode() {
    swapMode = !swapMode;
    selectedCell = null;
    
    const btn = document.querySelector('.btn-swap');
    const cells = document.querySelectorAll('.subject-cell');
    
    if (swapMode) {
        btn.innerHTML = '❌ Cancel Swap';
        btn.style.background = '#ef4444';
        cells.forEach(cell => {
            cell.classList.add('swap-mode');
            cell.style.cursor = 'pointer';
        });
        showAlert('🔄 Click the period you want to change', 'info');
    } else {
        btn.innerHTML = '🔄 Smart Swap';
        btn.style.background = '#a855f7';
        cells.forEach(cell => {
            cell.classList.remove('swap-mode', 'selected', 'safe-swap');
            cell.style.background = '';
            cell.style.border = '';
        });
        showAlert('❌ Swap cancelled', 'warning');
    }
}

function handleCellClick(cell) {
    if (!swapMode) return;
    
    const day = cell.dataset.day;
    const slot = parseInt(cell.dataset.slot);
    const currentSubject = cell.getAttribute('data-subject');
    const currentFaculty = cell.getAttribute('data-faculty');
    
    if (!selectedCell) {
        // First click - select period to change
        selectedCell = { cell, day, slot, subject: currentSubject, faculty: currentFaculty };
        cell.classList.add('selected');
        cell.style.background = '#a855f7';
        cell.style.color = 'white';
        
        // Find and highlight safe swap options
        findSafeSwapOptions(currentFaculty, day, slot);
        showAlert('✅ Now click a GREEN period to swap', 'success');
    } else {
        // Second click - perform swap
        if (cell.classList.contains('safe-swap')) {
            performSafeSwap(selectedCell, { day, slot, cell });
            showAlert('✅ Swap completed!', 'success');
            toggleSwapMode(); // Exit swap mode
        } else if (cell === selectedCell.cell) {
            // Clicked same cell - deselect
            cell.classList.remove('selected');
            cell.style.background = '';
            cell.style.color = '';
            clearSafeSwapHighlights();
            selectedCell = null;
            showAlert('🔄 Selection cleared. Click another period', 'info');
        } else {
            showAlert('❌ Select a GREEN period for safe swap', 'danger');
        }
    }
}

function findSafeSwapOptions(faculty, currentDay, currentSlot) {
    clearSafeSwapHighlights();
    
    days.forEach(day => {
        for (let slot = 0; slot < 6; slot++) {
            if (day === 'Friday' && slot === 5) continue;
            if (day === currentDay && slot === currentSlot) continue;
            
            const cell = document.querySelector(`[data-day="${day}"][data-slot="${slot}"]`);
            if (!cell) continue;
            
            const targetFaculty = cell.getAttribute('data-faculty');
            
            // Check if swap is safe (no faculty clashes)
            const isSafe = checkSwapSafety(faculty, currentDay, currentSlot, targetFaculty, day, slot);
            
            if (isSafe) {
                cell.classList.add('safe-swap');
                cell.style.background = '#d4edda';
                cell.style.border = '3px solid #28a745';
            }
        }
    });
}

function checkSwapSafety(faculty1, day1, slot1, faculty2, day2, slot2) {
    // For now, simple check - can be enhanced with Supabase
    // Faculty1 going to (day2, slot2) - check if faculty1 is free there
    // Faculty2 going to (day1, slot1) - check if faculty2 is free there
    
    // Check if faculty1 has another class at (day2, slot2)
    const faculty1Clash = document.querySelector(
        `[data-day="${day2}"][data-slot="${slot2}"][data-faculty="${faculty1}"]`
    );
    
    // Check if faculty2 has another class at (day1, slot1)
    const faculty2Clash = faculty2 ? document.querySelector(
        `[data-day="${day1}"][data-slot="${slot1}"][data-faculty="${faculty2}"]`
    ) : null;
    
    return !faculty1Clash && !faculty2Clash;
}

function performSafeSwap(source, target) {
    // Swap HTML content
    const tempHTML = source.cell.innerHTML;
    const tempSubject = source.cell.getAttribute('data-subject');
    const tempFaculty = source.cell.getAttribute('data-faculty');
    const tempBg = source.cell.style.backgroundColor;
    
    source.cell.innerHTML = target.cell.innerHTML;
    source.cell.setAttribute('data-subject', target.cell.getAttribute('data-subject') || '');
    source.cell.setAttribute('data-faculty', target.cell.getAttribute('data-faculty') || '');
    source.cell.style.backgroundColor = target.cell.style.backgroundColor;
    
    target.cell.innerHTML = tempHTML;
    target.cell.setAttribute('data-subject', tempSubject || '');
    target.cell.setAttribute('data-faculty', tempFaculty || '');
    target.cell.style.backgroundColor = tempBg;
    
    // Update database
    updateSupabaseAfterSwap();
}

function clearSafeSwapHighlights() {
    document.querySelectorAll('.safe-swap').forEach(cell => {
        cell.classList.remove('safe-swap');
        cell.style.background = '';
        cell.style.border = '';
    });
}
```

## ✅ TESTING

After applying fixes:

1. **Test Lab Scheduling:**
   - Create 2 sections (A and B)
   - Assign same faculty to same lab in both
   - Generate timetable
   - **Expected:** Labs at DIFFERENT times

2. **Test Weekly Hours:**
   - Lab with 2h/week → 1 session (2 continuous hours)
   - Lab with 4h/week → 2 sessions (2 continuous hours each)
   - Theory with 3h/week → 3 separate 1-hour slots
   - **Expected:** NO empty slots, all hours allocated

3. **Test Smart Swap:**
   - Click "Smart Swap"
   - Click a period (turns purple)
   - See green highlighted safe options
   - Click green period
   - **Expected:** Swap completes, no clashes

## 🎨 BONUS: Fix timetable-new.htm Design

Apply blue/white theme - I'll create this in next file.

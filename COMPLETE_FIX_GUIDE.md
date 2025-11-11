# Complete Fix Guide - MIT Mysore Timetable System

## 🔧 Critical Issues & Solutions

### Issue 1: Labs Generating at Same Time for All Sections

**Problem:** All sections get labs scheduled at the same time, causing faculty conflicts.

**Root Cause:** Timetable generation doesn't track faculty availability across sections.

**Solution:**
```javascript
// In enhanced.htm, modify createAdvancedTimetable function:

// Track faculty usage globally across all sections
const globalFacultySchedule = {};

function hasFacultyClash(facultyName, day, slot, section) {
    // Check if faculty is already scheduled at this time in ANY section
    if (!globalFacultySchedule[facultyName]) {
        globalFacultySchedule[facultyName] = {};
    }
    if (!globalFacultySchedule[facultyName][day]) {
        globalFacultySchedule[facultyName][day] = new Set();
    }
    return globalFacultySchedule[facultyName][day].has(slot);
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
```

### Issue 2: Weekly Hours Not Matching (Empty Boxes)

**Problem:** 
- 2 hours/week lab should be 1 day × 2 continuous hours
- 4 hours/week lab should be 2 days × 2 continuous hours each
- Empty slots appearing

**Solution:**
```javascript
// Correct lab session calculation:
function calculateLabSessions(weeklyHours) {
    // Each lab session is exactly 2 continuous hours
    return Math.floor(weeklyHours / 2);
}

// Example:
// 2 hours/week = 1 session (1 day, 2 hours)
// 4 hours/week = 2 sessions (2 days, 2 hours each)
// 6 hours/week = 3 sessions (3 days, 2 hours each)

// For theory subjects:
function calculateTheorySessions(weeklyHours) {
    // Each theory session is 1 hour
    return weeklyHours; // Direct mapping
}
```

**Implementation:**
```javascript
// Place labs first
allSessions.filter(s => s.type === 'lab').forEach(item => {
    const sessionsNeeded = Math.floor(item.weekly_hours / 2);
    let sessionsPlaced = 0;
    
    for (let session = 0; session < sessionsNeeded; session++) {
        // Find available 2-hour continuous slot
        for (const day of days) {
            if (sessionsPlaced >= sessionsNeeded) break;
            
            for (const slotGroup of continuousSlots) {
                // Check both slots are free AND no faculty clash
                const canPlace = slotGroup.every(slot => 
                    timetable[day][slot] === null && 
                    !hasFacultyClash(item.faculty, day, slot, section)
                );
                
                if (canPlace) {
                    // Place lab in both slots
                    slotGroup.forEach(slot => {
                        timetable[day][slot] = {
                            subject_code: item.code,
                            faculty_name: item.faculty,
                            type: 'lab'
                        };
                        markFacultyBusy(item.faculty, day, slot);
                    });
                    sessionsPlaced++;
                    break;
                }
            }
        }
    }
});

// Then place theory subjects
allSessions.filter(s => s.type === 'theory').forEach(item => {
    const sessionsNeeded = item.weekly_hours;
    let sessionsPlaced = 0;
    
    for (const day of days) {
        if (sessionsPlaced >= sessionsNeeded) break;
        
        for (let slot = 0; slot < 6; slot++) {
            if (sessionsPlaced >= sessionsNeeded) break;
            
            // Skip Friday last period
            if (day === 'Friday' && slot === 5) continue;
            
            // Check slot is free AND no faculty clash
            if (timetable[day][slot] === null && 
                !hasFacultyClash(item.faculty, day, slot, section)) {
                
                timetable[day][slot] = {
                    subject_code: item.code,
                    faculty_name: item.faculty,
                    type: 'theory'
                };
                markFacultyBusy(item.faculty, day, slot);
                sessionsPlaced++;
            }
        }
    }
});
```

### Issue 3: Smart Swap Not Working Properly

**Problem:** Swap doesn't analyze faculty availability properly.

**Solution:**
```javascript
// Enhanced Smart Swap Implementation

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
        showAlert('🔄 Select the period you want to change', 'info');
    } else {
        btn.innerHTML = '🔄 Smart Swap';
        btn.style.background = '#a855f7';
        cells.forEach(cell => {
            cell.classList.remove('swap-mode', 'selected', 'safe-swap');
        });
        clearSwapHighlights();
    }
}

function handleCellClick(cell) {
    if (!swapMode) return;
    
    const day = cell.dataset.day;
    const slot = parseInt(cell.dataset.slot);
    const currentSubject = cell.getAttribute('data-subject');
    const currentFaculty = cell.getAttribute('data-faculty');
    
    if (!selectedCell) {
        // First click - select the period to change
        selectedCell = { cell, day, slot, subject: currentSubject, faculty: currentFaculty };
        cell.classList.add('selected');
        
        // Find and highlight safe swap options
        findSafeSwapOptions(currentFaculty, day, slot);
        showAlert('✅ Now select a safe period to swap with (highlighted in green)', 'success');
    } else {
        // Second click - perform swap
        const targetDay = day;
        const targetSlot = slot;
        
        // Check if this is a safe swap option
        if (cell.classList.contains('safe-swap')) {
            performSafeSwap(selectedCell, { day: targetDay, slot: targetSlot, cell });
        } else {
            showAlert('❌ This swap would cause a faculty clash. Select a green highlighted period.', 'danger');
        }
    }
}

function findSafeSwapOptions(faculty, currentDay, currentSlot) {
    // Clear previous highlights
    clearSwapHighlights();
    
    // Check all periods for safe swaps
    days.forEach(day => {
        for (let slot = 0; slot < 6; slot++) {
            // Skip Friday last period
            if (day === 'Friday' && slot === 5) continue;
            
            // Skip current position
            if (day === currentDay && slot === currentSlot) continue;
            
            const cell = document.querySelector(`[data-day="${day}"][data-slot="${slot}"]`);
            if (!cell) continue;
            
            const targetFaculty = cell.getAttribute('data-faculty');
            
            // Check if swap is safe:
            // 1. Target slot's faculty can move to current slot (no clash)
            // 2. Current faculty can move to target slot (no clash)
            
            const isSafe = checkSwapSafety(
                faculty, currentDay, currentSlot,
                targetFaculty, day, slot
            );
            
            if (isSafe) {
                cell.classList.add('safe-swap');
                cell.style.background = '#d4edda';
                cell.style.border = '2px solid #28a745';
            }
        }
    });
}

async function checkSwapSafety(faculty1, day1, slot1, faculty2, day2, slot2) {
    // Check if faculty1 can go to (day2, slot2)
    const { data: clash1 } = await supabase
        .from('timetables')
        .select('*')
        .eq('faculty_name', faculty1)
        .eq('day', day2)
        .eq('time_slot', slot2)
        .neq('section', currentSection);
    
    if (clash1 && clash1.length > 0) return false;
    
    // Check if faculty2 can go to (day1, slot1)
    if (faculty2) {
        const { data: clash2 } = await supabase
            .from('timetables')
            .select('*')
            .eq('faculty_name', faculty2)
            .eq('day', day1)
            .eq('time_slot', slot1)
            .neq('section', currentSection);
        
        if (clash2 && clash2.length > 0) return false;
    }
    
    return true;
}

function performSafeSwap(source, target) {
    // Swap the cell contents
    const tempHTML = source.cell.innerHTML;
    const tempSubject = source.cell.getAttribute('data-subject');
    const tempFaculty = source.cell.getAttribute('data-faculty');
    
    source.cell.innerHTML = target.cell.innerHTML;
    source.cell.setAttribute('data-subject', target.cell.getAttribute('data-subject'));
    source.cell.setAttribute('data-faculty', target.cell.getAttribute('data-faculty'));
    
    target.cell.innerHTML = tempHTML;
    target.cell.setAttribute('data-subject', tempSubject);
    target.cell.setAttribute('data-faculty', tempFaculty);
    
    // Update database
    updateSupabaseAfterSwap();
    
    showAlert('✅ Swap completed successfully!', 'success');
    toggleSwapMode(); // Exit swap mode
}

function clearSwapHighlights() {
    document.querySelectorAll('.safe-swap').forEach(cell => {
        cell.classList.remove('safe-swap');
        cell.style.background = '';
        cell.style.border = '';
    });
}
```

### Issue 4: UI Enhancement for timetable-new.htm

**Apply Blue/White Theme:**
```css
/* Add to timetable-new.htm */
body {
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
}

.card {
    background: white;
    border: 1px solid #e0f2fe;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(30, 64, 175, 0.1);
}

.btn {
    background: #3b82f6;
    border-radius: 8px;
    transition: all 0.3s ease;
}

.btn:hover {
    background: #2563eb;
    transform: translateY(-2px);
}

.btn-success {
    background: #22c55e;
}

.btn-success:hover {
    background: #16a34a;
}
```

## 📋 Implementation Checklist

- [ ] Fix lab scheduling with global faculty tracking
- [ ] Implement correct weekly hours calculation
- [ ] Fix smart swap with safety checks
- [ ] Apply blue/white theme to timetable-new.htm
- [ ] Test with multiple sections
- [ ] Verify no faculty clashes
- [ ] Verify all weekly hours allocated
- [ ] Test swap functionality

## 🧪 Testing Steps

1. **Test Lab Scheduling:**
   - Create 2 sections with same lab subject
   - Assign same faculty to both
   - Generate timetable
   - Verify labs are at different times

2. **Test Weekly Hours:**
   - Add lab with 2 hours/week → Should get 1 session (2 continuous hours)
   - Add lab with 4 hours/week → Should get 2 sessions (2 continuous hours each)
   - Add theory with 3 hours/week → Should get 3 separate 1-hour slots
   - Verify no empty slots

3. **Test Smart Swap:**
   - Click "Smart Swap"
   - Select a period
   - Verify green highlights show safe options
   - Select green period
   - Verify swap completes
   - Check no faculty clashes created

## 🚀 Quick Fix Priority

1. **HIGHEST:** Fix lab scheduling (faculty conflicts)
2. **HIGH:** Fix weekly hours allocation (empty slots)
3. **MEDIUM:** Fix smart swap (usability)
4. **LOW:** UI enhancement (cosmetic)

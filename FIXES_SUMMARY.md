# Critical Fixes Required

## Issues to Fix:

1. **Lab Scheduling Problem**
   - Labs generating at same time for all sections
   - Need section-wise independent scheduling

2. **Weekly Hours Not Matching**
   - Empty boxes appearing (incomplete allocation)
   - 2 hours/week lab = 1 day with 2 continuous hours
   - 4 hours/week lab = 2 days with 2 continuous hours each

3. **Smart Swap Not Working**
   - Should ask user to select period to swap
   - Analyze and show safe swap options
   - Check faculty clashes before swapping

4. **UI Enhancement Needed**
   - timetable-new.htm needs better design
   - Match blue/white theme

## Solutions Being Implemented:

### 1. Fix Lab Scheduling
- Generate timetable independently for each section
- Track faculty availability per section
- Prevent same-time lab conflicts

### 2. Fix Weekly Hours
- Ensure exact weekly hours allocation
- Labs: 2h = 1 session, 4h = 2 sessions
- Theory: distribute evenly across week
- No empty slots unless intentional

### 3. Fix Smart Swap
- Click "Smart Swap" → Select period to change
- System analyzes faculty availability
- Shows only safe swap options
- Confirms no clashes before swapping

### 4. Enhance UI
- Apply blue/white theme to timetable-new.htm
- Clean card-based layout
- Better form organization

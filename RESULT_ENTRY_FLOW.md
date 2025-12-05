# Fight Result Entry Flow - Complete Guide

## What Happens When You Enter Fight Results

### 1. Admin Enters Results
When an admin enters results for a fight in the admin panel:

**Location**: Admin Panel → Events → [Event Name] → Бои (Fights) Tab → Результат button

**What you enter**:
- Winner (Fighter 1, Fighter 2, Draw, or No Contest)
- Method (KO/TKO, Submission, Decision, or DQ)
- Finish details (round/time if not a decision)
- Judge scorecards (if decision - 3 judges with round-by-round scores)

### 2. Backend Processing
The system automatically:

**a) Saves the Result**:
- Creates `FightResult` record with winner and method
- Creates `OfficialScorecard` records for each judge (if decision)
- Creates `OfficialRoundScore` records for each round

**b) Resolves Predictions**:
- Finds all user predictions for this fight
- Marks each as correct/incorrect based on:
  - ✅ Correct: Predicted winner AND method BOTH match official result
  - ❌ Incorrect: Either winner or method don't match
- Sets `is_correct` field and `resolved_at` timestamp

**c) Resolves Scorecards** (if decision):
- Finds all user scorecards for this fight
- For each round, checks if user's score matches ANY of the 3 judges
- Marks each round as correct/incorrect
- Calculates total correct rounds
- Sets `resolved_at` timestamp

**d) Updates Event Status**:
- Checks if ALL fights in the event now have results
- If yes, automatically marks event as `is_upcoming = False` (completed)

### 3. User-Facing Changes

**Event Status**:
- ❌ Before: Event shows in "Предстоящие События" (Upcoming Events)
- ✅ After: Event marked with "✓ Завершено" (Completed) badge
- Event may move to past events section

**Prediction Display**:
When users view the fight page, they see:

**If Correct**:
```
Ваш прогноз
[Fighter Name] - [Method]
✓ Правильный прогноз!
```

**If Incorrect**:
```
Ваш прогноз
[Fighter Name] - [Method]
✗ Неправильный прогноз
```

**Scorecard Display** (if decision):
```
Ваша карта: 2/3 раундов правильно

Раунд 1: 10-9  ✓ (green highlight)
Раунд 2: 10-9  ✗ (red/default)
Раунд 3: 9-10  ✓ (green highlight)
```

**Profile Page**:
Users can see their statistics:
- Prediction Accuracy: X% (correct predictions / total predictions)
- Scorecard Accuracy: Y% (average correct rounds / total rounds)

### 4. Database Changes

**Tables Affected**:
1. `fight_results` - Result created/updated
2. `official_scorecards` - Judge cards created/updated
3. `official_round_scores` - Round scores created/updated
4. `predictions` - All predictions for fight have `is_correct` and `resolved_at` set
5. `scorecards` - User scorecards have `correct_rounds`, `total_rounds`, and `resolved_at` set
6. `round_scores` - Individual rounds have `is_correct` set
7. `events` - May have `is_upcoming` set to False

## Current Status - Victor Fight Event

### Results Entered:
- ✅ Fight 1464 (Абдулла Аль Бушери vs Абдул Разак Санкара): Winner FIGHTER1, Method DECISION
- ✅ Fight 1465: Winner FIGHTER1, Method DECISION
- ✅ Fight 1466: Winner FIGHTER1, Method DECISION

### Predictions Resolved:
- ✅ 1 prediction for fight 1464:
  - User predicted: FIGHTER1 via SUBMISSION
  - Result was: FIGHTER1 via DECISION
  - Marked as INCORRECT (wrong method)
  - Resolved at: 2025-12-04 21:42:20

### Event Status:
- ✅ Victor Fight event marked as `is_upcoming = False` (completed)
- ✅ Event will show with "✓ Завершено" badge

## How to View Results as User

1. **As Admin**: You can see results in Admin Panel → Events → Victor Fight → Бои tab
2. **As User**: 
   - Go to the specific fight page (if you have the link)
   - Your prediction will show as ✓ Correct or ✗ Incorrect
   - Your scorecard will show which rounds you got right

## Troubleshooting

**If results don't show**:
1. Refresh the page (Ctrl+R or Cmd+R)
2. Clear browser cache
3. Check if you're logged in (predictions only show for authenticated users)

**If event still shows as upcoming**:
1. Make sure ALL fights have results entered
2. Check database: `SELECT is_upcoming FROM events WHERE id = 57;` should return 0

**If predictions don't resolve**:
1. Check logs in `backend.log`
2. Verify fight result was created: `SELECT * FROM fight_results WHERE fight_id = X;`
3. Verify predictions exist: `SELECT * FROM predictions WHERE fight_id = X;`


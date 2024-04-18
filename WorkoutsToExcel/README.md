This program identifies and reads workouts from the specified source, and writes them to the target sheet in the target Excel file. 

**How it works** _(subject to change)_
1) This program reads notes from a Google Keep account or local files (txt, md).

2) It filters notes matching the expected format, namely: 
   - A date in the note's title in YYYY-MM-DD format followed by any text (for example "2024-01-03 cardio workout")...
   - with the note's text containing what we call an "est XX mins line", where "XX" refers to a string of 1-3 digits, or 1-3 question marks, but not both.
   - Each note must have a unique date in its title.

3) It then writes each workout to the correct date cell of the target spreadsheet.

4) Checks occur for each workout, to ensure that no existing cell value in the workout column (see params.py) will be overwritten.

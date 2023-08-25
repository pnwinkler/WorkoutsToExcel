This program transfers workouts from the source notes to a local file. 

**How it works** _(subject to change)_
1) This program reads notes from a Google Keep account or local files (txt, md).

2) It filters notes matching the expected format, namely: 
   - a date in the note's title in YYYY-MM-DD format followed by any text (for example "2023-01-03 cardio workout")...
   - with the note's text containing what we call an "est XX mins line", where "XX" refers to a string of 1-3 digits, or 1-3 question marks, but not both.

3) It then writes each workout to the correct date cell of the target spreadsheet.

4) Checks occur for each workout, which are logged to console. No existing not-empty cell value in the workout column (see params.py) will be overwritten.

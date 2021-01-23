GKeepToCalc transfers workouts from Google Keep notes to a local file. 

Instructions (for this program only) under "Wiki" tab.

*How it works*
1) This program reads notes from a Google Keep account.

2) It filters notes matching a particular format (i.e. they're workout notes). The expected format is as follows: a date in the note's title such as "03 January", with the note's body containing an "est XX mins line", where "XX" refers to a 2-3 digit string or 2-3 question marks (not one!).

3) It re-formats them on the local machine. At this stage, it asks the user to verify the file, whose location is specified in utilities/params.py "cleaned_data_path" variable. This file contains everything that the program has classified as workout data, according to step 2, in a slightly cleaned up state. The user's attention is requested in order to correct any erroneous data in that file, if any. That might be: absent workouts, or non-workouts mistaken as workouts.

4) It then writes each workout to the correct date cell of the target spreadsheet. This is done by comparing the title of each note (now part of one large text file, as specified in stage 3), and comparing it to the datetime value of cells in the "date_column", specified in utilities/params.py.

5) Checks occur for each workout, which are logged to console. No not-empty cell in the workout column (see params.py) will be overwritten! 3 possible scenarios are logged: 1) cell successfully written to; 2) workout already written to cell; 3) unexpected data already written to cell. Whether scenario 2 or 3 is printed depends on an exact comparison between the existing content of a workout cell, and the intended write. If they're identical, it's scenario 2, else it's 3. 

6) The created file from stage 2 is deleted. 

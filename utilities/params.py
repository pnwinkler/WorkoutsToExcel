import os

# ______________________________________________________________________________________________________

# CHANGE AS NEEDED:

# source_path is where Keep2Calc writes the data that it pulls from Google Keep, for you to then verify. The idea is that you can delete any non-workout data that the program has erroneously retrieved (if any).
# cleaned_data_path is where Keep2Calc will write to, for its own use, after you've verified that source_path contains only workouts.
# Before the end of program execution, both files will be deleted automatically. 
source_path = os.path.join(os.path.sep, 'home','philip','Desktop', 'keep2calc_source.txt')
cleaned_data_path = os.path.join(os.path.sep, 'home','philip','Desktop', 'keep2calc_source_CLEANED.txt')

# if left as None, will default to "Keep2Calc.backups/" in same dir as target file
backup_folder_name = None

# these variables set which columns the program expects to find dates, bodyweights and workouts in, within the target spreadsheet. 
date_column = 2
bodyweight_column = 3
workout_column = 5

# target_path contains the path of the spreadsheet file to which you wish to write. Non .xlsx file formats may work, but are untested.
# target_sheet is the sheet within the spreadsheet to which workouts and bodyweights will be written. So far (23-JAN-2021), multiple target sheets may not be specified. That means bodyweights will go on the same sheet as workouts. 
target_path = os.path.join(os.path.sep, 'home','philip', 'PRIO', 'food_eaten_diet.xlsx')
target_sheet = 'Bodyweight and workouts'
# ______________________________________________________________________________________________________


import os

# ______________________________________________________________________________________________________

# CHANGE AS NEEDED:

# source_path is where Keep2Calc writes the data that it pulls from Google Keep, for internal use. This will be tidied up, then written to cleaned_data_path.
# cleaned_data_path is where Keep2Calc will write the tidied output of source_path to, for you to verify. The idea is that you can delete non-workout data that the program has erroneously retrieved (if any) before execution resumes.
# Both files will be deleted automatically before program termination. 
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


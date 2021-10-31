import os

# ______________________________________________________________________________________________________

# CHANGE AS NEEDED:

# TARGET_PATH contains the path of the spreadsheet file to which you wish to write. Non .xlsx file formats may work, but are untested.
# TARGET_SHEET is the sheet within the spreadsheet to which workouts and bodyweights will be written. So far (23-JAN-2021), multiple target sheets may not be specified. That means bodyweights will go on the same sheet as workouts.
TARGET_PATH = os.path.join(os.path.sep, 'home/philip/Laptop-Desktop/enc_files/home/philip/PRIO/personal/medication_and_health', 'food_eaten_diet.xlsx')
TARGET_SHEET = 'Bodyweight and workouts'

# SOURCE_PATH is where Keep2Calc writes the data that it pulls from Google Keep, for internal use. This will be tidied up, then written to CLEANED_DATA_PATH.
# CLEANED_DATA_PATH is where Keep2Calc will write the tidied output of SOURCE_PATH to, for you to verify. The idea is that you can delete non-workout data that the program has erroneously retrieved (if any) before execution resumes.
# Both files will be deleted automatically before program termination.
SOURCE_PATH = os.path.join(os.path.sep, 'home', 'philip', 'Desktop', 'keep2calc_source.txt')
CLEANED_DATA_PATH = os.path.join(os.path.sep, 'home', 'philip', 'Desktop', 'keep2calc_source_CLEANED.txt')

# if left as None, will default to "Keep2Calc.backups/" in same dir as target file
BACKUP_FOLDER_NAME = None

# these variables set which columns the program expects to find dates, bodyweights and workouts in, within the target spreadsheet. 
DATE_COLUMN = 2
BODYWEIGHT_COLUMN = 3
WORKOUT_COLUMN = 5

# ______________________________________________________________________________________________________

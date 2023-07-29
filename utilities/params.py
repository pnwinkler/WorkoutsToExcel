import os

# ______________________________________________________________________________________________________

# CHANGE AS NEEDED:

# TARGET_PATH contains the path of the spreadsheet file to which you wish to write. Non .xlsx file formats may work, but are untested.
# TARGET_SHEET is the sheet within the spreadsheet to which workouts and bodyweights will be written. So far (23-JAN-2021), multiple target sheets may not be specified. That means bodyweights will go on the same sheet as workouts.
TARGET_PATH = os.path.join(os.path.sep, 'home/philip/Laptop-Desktop/enc_files/home/philip/PRIO/personal/medication_and_health', 'food_eaten_diet.xlsx')
TARGET_SHEET = 'Bodyweight and workouts'

# if left as None, will default to "Keep2Calc.backups/" in same dir as target file
BACKUP_FOLDER_NAME = None

# these variables set which columns the program expects to find dates, bodyweights and workouts in, within the target spreadsheet. 
DATE_COLUMN = 2
BODYWEIGHT_COLUMN = 3
WORKOUT_COLUMN = 5

# the string for which bodyweights2calc will search for in note titles, in order to identify the bodyweights note.
# case is irrelevant.
BODYWEIGHTS_NOTE_TITLE = "Bodyweights note"

# history_length is the "X" most recent commits to the local file (where X is an integer), which Bodyweights2Calc will
# use in order to create a context window (the parenthesized and comma-separated list of the "X" most recent
# bodyweights in the bodyweights note).
HISTORY_LENGTH = 3

# this is how many characters the Note and XLSX snippets will be, when presented to the user for comparison,
# by KeepPruner
SNIPPET_LENGTH = 31

# ______________________________________________________________________________________________________

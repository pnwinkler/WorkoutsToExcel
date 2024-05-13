
# ______________________________________________________________________________________________________

# CHANGE AS NEEDED:

# These variables are only used if RETRIEVAL_METHOD is set to LOCAL_STR.
# This specifies the full path of the directory containing the notes to be processed.
LOCAL_NOTES_SOURCE_DIR = "/PATH/TO/WorkoutNotes"
# This specifies the full path of the directory to which notes will be moved after being processed.
LOCAL_NOTES_ARCHIVE_DIR = "/PATH/TO/WorkoutNotesArchive"
# This specifies the full path for the directory into which the target Excel file will be backed up
LOCAL_EXCEL_BACKUP_DIR = "/PATH/TO/ExcelBackupDirectory"

# This specifies the path of the spreadsheet file to which you wish to write.
TARGET_PATH = "/PATH/TO/ExcelToWriteTo.xlsx"
# This specifies the unique sheet name within that spreadsheet to which workout and bodyweight data will be written.
TARGET_SHEET = "Name Of Your Sheet"

# These specify which columns the program expects to find dates, bodyweights and workouts in, within the
# target spreadsheet. Note that the first column (A) maps to 1, not 0.
DATE_COLUMN = 2
BODYWEIGHT_COLUMN = 3
WORKOUT_COLUMN = 5

# The note within which bodyweights are stored should have this title (case-insensitive)
BODYWEIGHTS_NOTE_TITLE = "Bodyweights note"

# History_length specifies how many of the most recent bodyweights should be left in the bodyweights file after
# processing. These values are left to provide context, and will not be processed again.
# integer > 0
HISTORY_LENGTH = 3

# This specifies how many characters of each note and potentially corresponding Excel snippet will be when presented
# to the user for comparison. This value is an integer > 0 specifying the number of characters.
SNIPPET_LENGTH = 31

# ______________________________________________________________________________________________________


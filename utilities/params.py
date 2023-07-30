# supported retrieval methods:
LOCAL_STR = "local"
GKEEPAPI_STR = "gkeepapi"

# ______________________________________________________________________________________________________

# CHANGE AS NEEDED:

# RETRIEVAL_METHOD specifies whether we retrieve data from local files (set to LOCAL_STR) or from Google Keep using
# gkeepapi (set to GKEEPAPI_STR)
RETRIEVAL_METHOD = GKEEPAPI_STR

# LOCAL_SOURCE_DIR specifies the path of the directory containing the notes to be processed. This is only used if
# RETRIEVAL_METHOD is set to LOCAL_STR.
LOCAL_SOURCE_DIR = "YOUR/PATH/TO/LOCAL/NOTES"

# TARGET_PATH specifies the path of the spreadsheet file to which you wish to write. TARGET_SHEET is the sheet within
# that spreadsheet to which data will be written. To date, multiple target sheets may not be specified.
TARGET_PATH = "YOUR/PATH/TO/EXCEL.xlsx"
TARGET_SHEET = 'Bodyweight and workouts'

# specifies the full path for the directory into which files will be backed up. Specifically: the file specified by
# TARGET_PATH, and also the bodyweights file if running locally.
LOCAL_BACKUP_DIR = "YOUR/PATH/TO/BACKUP_DIR"

# these variables specify which columns the program expects to find dates, bodyweights and workouts in, within the
# target spreadsheet. Note that the first column (A) maps to 1, not 0.
DATE_COLUMN = 2
BODYWEIGHT_COLUMN = 3
WORKOUT_COLUMN = 5

# if using gkeepapi, then this specifies the title of the only Google Keep note within which bodyweights are stored.
# case-insensitive
BODYWEIGHTS_NOTE_TITLE = "Bodyweights note"

# history_length specifies how many of the most recent bodyweights should be left in the bodyweights file after
# processing. These values are left to provide context, and will not be processed again.
# integer > 0
HISTORY_LENGTH = 3

# this specifies how many characters of each note and potentially corresponding Excel snippet will be when presented
# to the user for comparison. This value is an integer > 0 specifying the number of characters.
SNIPPET_LENGTH = 31

# ______________________________________________________________________________________________________

if RETRIEVAL_METHOD == GKEEPAPI_STR:
    try:
        import gkeepapi
    except ImportError:
        raise ImportError("gkeepapi is specified as the retrieval method in params.py but is not installed. "
                          "Please install it using 'pip install gkeepapi==0.14.1'")

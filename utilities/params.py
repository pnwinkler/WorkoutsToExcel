import os

# keep2calc params
# ______________________________________________________________________________________________________

# CHANGE AS NEEDED:
source_path = os.path.join(os.path.sep, 'home','philip','Desktop', 'keep2calc_source.txt')
cleaned_data_path = os.path.join(os.path.sep, 'home','philip','Desktop', 'keep2calc_source_CLEANED.txt')

# if left as None, will default to "Keep2Calc.backups" in same dir as target file
backup_folder_name = None

date_column = 2
workout_column = 5

# ______________________________________________________________________________________________________

# shared params (between keep2calc and keep_pruner)
target_sheet = 'Bodyweight and workouts'
target_path = os.path.join(os.path.sep, 'home','philip', 'PRIO', 'food_eaten_diet.xlsx')

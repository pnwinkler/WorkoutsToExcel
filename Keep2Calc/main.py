# todo: make this not write to desktop?
# BEST CALLED VIA COMMAND LINE
# !!NOTE: should not be used for workouts more than 1 year old!!
#   you will get bad results.
#   they may be written to the wrong cell, and noise may be misidentified as workouts.
# this is a limitation of the format for the title of each gkeep note
# "24 October" for example does not specify a year

import GKeepToCalc.Keep2Calc.retrieve_data_from_gkeep as retrieve
import GKeepToCalc.Keep2Calc.keep_to_calc as ktc
import GKeepToCalc.utilities.params as p
import sys
import os

# the --no-fetch console parameter allows a user to skip
# retrieving gkeep data again. Useful if SOURCE_PATH contents
# needed manual editing (if the program fails to remove
# extraneous (non-workout) data from SOURCE_PATH contents)
if '--no-fetch' not in sys.argv:
    retrieve.write_gkeep_data_to_desktop()

# check that files all exist (source, target, xlsx sheet)
print('Running initial checks')
ktc.initial_checks()

# remove extraneous data from source file
# create temporary file holding cleaned data,
# to be inspected by the user
# clean_data = ktc.return_list_of_workouts_from_file(p.SOURCE_PATH)
# ktc.write_workouts_to_xlsx(clean_data)

# "clean" means that all non-workout data is removed from the file / output
with open(p.CLEANED_DATA_PATH, 'w+') as f:
    list_of_workouts = ktc.return_list_of_workouts_from_file(p.SOURCE_PATH)
    for workout in list_of_workouts:
        f.write(''.join(workout))
        # add 2 newlines after at the end of each entry
        f.write('\n\n')

print()
# hacky attempt to print filename, not the whole path
print(
    f'Removed unrelated lines from source. Please verify that new file "{p.CLEANED_DATA_PATH.split("/")[-1]}" contains no data unrelated to workouts')
print('When ready, press \'y\'.')
print('If the file needs modifying, press \'n\' to quit, and use the --no-fetch parameter next execution')
print('cleaned file = ', p.CLEANED_DATA_PATH)
uin = input('Input: ')

if uin != 'y':
    print('User input did not equal \'y\'. Exiting program in 5 seconds')
    import time

    time.sleep(5)
    exit()

# user agreed: replace original SOURCE_PATH with cleaned data
os.remove(p.SOURCE_PATH)
os.rename(p.CLEANED_DATA_PATH, p.SOURCE_PATH)

# intentionally run twice: first, to save the user time;
# here, it's to counteract user error (like accidentally
# deleting a date line)
ktc.initial_checks()

# process the now-cleaned data, to have a write-ready format
# it's a list of tuples. Maybe rename it
strings_to_write_lst = ktc.return_parsed_data(p.SOURCE_PATH)

# write it to target file
ktc.write_workouts_to_xlsx(strings_to_write_lst, backup=True)

os.remove(p.SOURCE_PATH)
print(
    "All done! Consider double-checking the now-updated target file, then running KeepPruner if you'd like to delete the "
    "old entries from Keep"
)

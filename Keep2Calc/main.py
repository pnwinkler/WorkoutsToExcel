# todo: delete source on desktop after successful program run
# BEST CALLED VIA COMMAND LINE
# NOTE: should not be used for workouts more than 1 year old!!
# it will write them to the wrong cell
# this is a limitation of the format for the title of each gkeep note
# "24 October" for example does not specify a year

import Keep2Calc.retrieve_data_from_gkeep as retrieve
import Keep2Calc.keep_to_calc as ktc
import utilities.params as p
import sys
import os

# the --no-fetch console parameter allows a user to skip
# retrieving gkeep data again. Useful if source_path contents
# needed manual editing (if the program fails to remove
# extraneous (non-workout) data from source_path contents)
if '--no-fetch' not in sys.argv:
    retrieve.write_gkeep_data_to_desktop()

# check that files all exist (source, target, xlsx sheet)
print('Running initial checks')
ktc.initial_checks()

# remove extraneous data from source file
# create temporary file holding cleaned data,
# to be inspected by the user
# clean_data = ktc.return_clean_data_matrix(p.source_path)
# ktc.write_workouts_to_xlsx(clean_data)

# "clean" means that all non-workout data is removed from the file / output
with open(p.cleaned_data_path, 'w+') as f:
    matrix = ktc.return_clean_data_matrix(p.source_path)
    for l in matrix:
        f.write(''.join(l))
        # add 2 newlines after "Est ?? mins" to match the 'unclean' source
        # this also aids legibility
        f.write('\n\n')

print()
# hacky attempt to print filename, not the whole path
print(
    f'Removed unrelated lines from source. Please verify that new file "{p.cleaned_data_path.split("/")[-1]}" contains no data unrelated to workouts')
print('When ready, press \'y\'.')
print('If the file needs modifying, press \'n\' to quit, and use the --no-fetch parameter next execution')
print('cleaned file = ', p.cleaned_data_path)
uin = input('Input: ')

if uin != 'y':
    print('User input did not equal \'y\'. Exiting program in 5 seconds')
    import time

    time.sleep(5)
    exit()

# user agreed: replace original source_path with cleaned data
os.remove(p.source_path)
os.rename(p.cleaned_data_path, p.source_path)

# intentionally run twice: first, to save the user time;
# here, it's to counteract user error (like accidentally
# deleting a date line)
ktc.initial_checks()

# process the now-cleaned data, to have a write-ready format
# it's a list of tuples. Maybe rename it
strings_to_write_lst = ktc.return_parsed_data(p.source_path)

# write it to target file
ktc.write_workouts_to_xlsx(strings_to_write_lst, backup=True)

print("All done!")

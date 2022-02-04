# BEST CALLED VIA COMMAND LINE
# !!NOTE: should not be used for workouts more than 1 year old!!
#   you will get bad results.
#   they may be written to the wrong cell, and noise may be misidentified as workouts.
# this is a limitation of the format for the title of each gkeep note
# "24 October" for example does not specify a year
import GKeepToCalc.Keep2Calc.keep_to_calc as ktc
import GKeepToCalc.utilities.utility_functions as uf

keep_obj = uf.login_and_return_keep_obj()
all_notes = list(uf.retrieve_notes(keep_obj))

# check that the target path, and the notes list are OK
print('Running initial checks')
ktc.initial_checks(all_notes)

# filter out non-workout notes
workout_notes = [note for note in all_notes if uf.is_workout_note(note, raise_error_if_has_xx_line_but_no_date=True)]

# get each workout into a writeable format
parsed_workouts = ktc.parse_workout_notes(workout_notes)

# pair the parsed workouts with target rows in the Excel file
data_to_write = ktc.pair_workouts_with_rows(parsed_workouts)

# write it to target file
ktc.write_workouts_to_xlsx(data_to_write, backup=True)

print("All done! Consider double-checking the now-updated target file, "
      "then running KeepPruner if you'd like to delete the old entries from Keep")

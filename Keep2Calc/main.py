# NOTE: should not be used for workouts more than 1 year old! This is because years are not processed in workout titles,
# meaning that:
# 1) workouts may be written to the wrong cell
# 2) non-workout notes may be misidentified as workouts.
import datetime

import Keep2Calc.keep_to_calc as ktc
import utilities.utility_functions as uf
import os
import utilities.params as p
from collections import Counter
from utilities.shared_types import Entry
from typing import List


def main():
    print('Running initial checks')
    uf.validate_target_sheet_params()

    # this program doesn't (yet) create the file from scratch
    if not os.path.exists(p.TARGET_PATH):
        raise FileNotFoundError("Target path not found")

    handler = uf.return_handler()

    notes: List[Entry] = handler.retrieve_notes()
    workout_notes = [note for note in notes if note.is_valid_workout_note(raise_on_invalid_format=True)]

    if not workout_notes:
        print("No workout notes found! Exiting.")

    # if the earliest edit timestamp is from more than 1 year ago, warn the user, as this can cause issues
    min_edit_timestamp = min([note.edit_timestamp for note in workout_notes])
    if min_edit_timestamp < datetime.datetime.now() - datetime.timedelta(days=365):
        print("WARNING: the earliest workout note is more than 1 year old. This can cause issues, as years are not "
              "processed in workout titles. Please ensure that all workout notes are less than 1 year old.")
        inp = input("Continue? (y/N): ")
        if inp.casefold() not in ('y', 'yes'):
            print("Exiting.")
            return

    duplicated_titles = [title for title, count in Counter([note.title for note in workout_notes]).items() if count > 1]
    if duplicated_titles:
        raise ValueError(f"Duplicate workout titles found. Please ensure that every workout has a unique title in your "
                         f"note taking application. Without unique titles, we have no way of knowing which workout "
                         f"belongs to which row in the target file. \n{duplicated_titles=}")

    # get each workout into a writeable format
    parsed_workouts = ktc.parse_workout_notes(workout_notes)

    # pair the parsed workouts with target rows in the Excel file
    data_to_write = ktc.pair_workouts_with_rows(parsed_workouts)

    # write it to target file
    ktc.write_data_to_xlsx(data_to_write, backup=True)

    print("All done! Consider double-checking the now-updated target file, then running KeepPruner if you'd like to "
          "delete the old entries from Keep")


if __name__ == '__main__':
    main()

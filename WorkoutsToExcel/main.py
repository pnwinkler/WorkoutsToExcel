from collections import Counter
from typing import List

import openpyxl
import workout_parsing as wp

import utilities.params as p
import utilities.utility_functions as uf
from utilities.shared_types import Entry


def main():
    uf.validate_target_sheet_params()

    handler = uf.return_handler()
    notes: List[Entry] = handler.retrieve_notes()
    workout_notes = [note for note in notes if note.is_valid_workout_note(raise_on_invalid_format=True)]

    if not workout_notes:
        print("No workout notes found! Exiting.")

    duplicated_titles = [title for title, count in Counter([note.title for note in workout_notes]).items() if count > 1]
    duplicate_workout_dates = [dt for dt, count in Counter([note.title_datetime for note in workout_notes]).items()
                               if count > 1]
    if duplicated_titles:
        raise ValueError(f"Duplicate workout titles found. Please ensure that every workout has a unique title in your "
                         f"note taking application. Without unique titles, we have no way of knowing which workout "
                         f"belongs to which row in the target file. \n{duplicated_titles=}")
    if duplicate_workout_dates:
        raise RuntimeError("Two workouts were evaluated as corresponding to the same date. This program expects 0-1 " +
                           f"workout notes per calendar date. \nThese are the duplicated dates: " +
                           f"{duplicate_workout_dates}")

    # get each workout into a writeable format
    parsed_workouts = wp.parse_workout_notes(workout_notes)

    # pair the parsed workouts with target rows in the Excel file
    sheet = openpyxl.load_workbook(p.TARGET_PATH)[p.TARGET_SHEET]
    data_to_write = wp.pair_workouts_with_rows(target_sheet=sheet,
                                               parsed_workouts=parsed_workouts)

    # write it to target file
    wp.write_data_to_xlsx(data_to_write, backup=True)

    print("All done! Consider double-checking the now-updated target file, then running the NotePruner script if "
          "you'd like to either trash old Google Keep entries, or archive local files")


if __name__ == '__main__':
    main()

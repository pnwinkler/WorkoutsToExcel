# this script interactively deletes workout notes that are already written to the target xlsx file,
# up to a given, user-provided date

from datetime import datetime, timedelta
from typing import Dict, List

import openpyxl
from tabulate import tabulate

import utilities.params as p
import utilities.utility_functions as uf
from utilities.shared_types import Entry


def is_deletion_candidate(xlsx_snippets: Dict[datetime, str], note: Entry, end_date: datetime) -> bool:
    # todo: test this properly
    """
    For a given note, return True if:
     1) it is already written to the target file...
     2) ...for the correct date
     3) that date is earlier than the requested end date.
    Else, False.
    :param xlsx_snippets: a dictionary where each key is a prettified workout's date, and each value its string
    representation in the target xlsx file.
    :param note: the note we're considering as a deletion candidate.
    :param end_date: the cutoff point, after which we return False regardless of the note or Excel file's value
    """

    # 1) disqualify if not a valid workout note
    if not note.is_valid_workout_note():
        return False

    # convert note title to datetime. Having multiple workouts with the same dates in their titles, or having workouts
    # whose title dates are > 364 days old is unsupported and likely to cause problems.
    assert note.title_datetime
    note_date = note.title_datetime

    if note_date == -1:
        # failed to convert workout's note_date. It is incorrectly formatted.
        return False

    # 2) do not flag as deletion candidate beyond cutoff
    if note_date > end_date:
        return False

    # 3) is note already written to the target file?
    floored_date: datetime = note.title_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
    try:
        xlsx_value = xlsx_snippets[floored_date]
        if not xlsx_value:
            # there's a value, but it's the empty string or None type
            return False
    except KeyError:
        # no entry for that date
        return False

    return True


def retrieve_xlsx_workout_snippets(sheet, max_row: int) -> Dict[datetime, str]:
    # return a dictionary where, for each day in the past year, the dictionary's key is that date, and its value the
    # string in the corresponding row in the target sheet, in the workouts column
    # todo: function name
    # todo: see if this row-determining logic should be moved out
    if not max_row:
        max_row = uf.find_row_of_cell_matching_datetime(sheet=sheet,
                                                        datetime_target=datetime.now(),
                                                        date_column=p.DATE_COLUMN)
    min_row = max(max_row - 365, 1)  # note that this may not retrieve a year of data, e.g. due to empty rows

    xlsx_snippets = dict()
    for row in sheet.iter_rows(min_row=min_row,
                               min_col=0,
                               max_col=max(p.WORKOUT_COLUMN, p.DATE_COLUMN),
                               max_row=max_row,
                               values_only=False):
        # todo: use 0 index if practical
        # a "row" in this context is a tuple of cells
        # params.py is 1-indexed, but openpyxl is 0-indexed. Todo: verify
        date_value = row[p.DATE_COLUMN - 1].value
        workout = row[p.WORKOUT_COLUMN - 1].value

        if not date_value:
            # if there's no date, there's no snippet to store
            continue
        if not isinstance(date_value, datetime):
            date_value = uf.convert_string_to_datetime(date_value, regress_future_dates=False)
            floored_date = date_value.replace(hour=0, minute=0, second=0)
            xlsx_snippets[floored_date] = workout

    return xlsx_snippets


def present_deletion_candidates(deletion_candidates: List[Entry], xlsx_snippets: Dict[datetime, str]) -> None:
    """
    Present deletion candidates to the user, in table format, demonstrating: the deletion_candidates, their
    corresponding values in the passed-in dictionary, and a percentage similarity rating of the two strings.
    :param deletion_candidates: a list of notes considered eligible for trashing.
    :param xlsx_snippets: a dictionary where each key is a workout's date, and each value its string
    representation in the target xlsx file.

    TABLE FORMATTED AS BELOW:

    date    note to be deleted snippet      snippet from xlsx
    ...     ...                             ...
    ...     ...                             ...

    Delete? (Y/N)
    """
    print(f"These are the {len(deletion_candidates)} deletion candidates. They are already written to file, and "
          "are older than your specified date range")
    print("\n**DELETION CANDIDATES**")

    # populate the matrix for tabulate
    tabulate_matrix = []
    for note in deletion_candidates:
        assert note.is_valid_workout_note()

        # comment lines don't appear in the xlsx file, so they're unhelpful for side-by-side comparison
        note_snippet = return_note_text_minus_comments(note, remove_plus_signs=True).replace('\n', ' ')
        note_snippet = note_snippet[:p.SNIPPET_LENGTH]

        floored_date = note.title_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
        xlsx_snippet = xlsx_snippets[floored_date].rstrip()[:p.SNIPPET_LENGTH]
        similarity = uf.get_string_pct_similarity(note_snippet, xlsx_snippet)

        # append the table row
        tabulate_matrix.append([floored_date, note_snippet, xlsx_snippet, str(similarity) + "%"])

    headers = ["Date", "Note snippet", "Exists in xlsx as...", "Similarity"]
    print(tabulate(tabulate_matrix, headers=headers))
    print()


def is_deletion_requested() -> bool:
    # returns True if permission is given to delete ALL notes presented by present_deletion_candidates()
    deletion_requested = input("Delete all of the above? (y/N): ").strip().lower()
    if deletion_requested in ["y", "yes"]:
        return True
    return False


def greet() -> None:
    greeting = "\n\t\t\t GKEEP NOTE DELETER \n" + \
               "\tdeletes workout notes from a google keep account up to a given date\n" \
               "\tprovided they are already written to file and you give your approval\n" \
        # "\t(Don't worry, we'll ask you before changing anything)\n"
    print(greeting)


def request_end_date() -> datetime:
    print("\tTo start, please enter the date you wish to delete up to (inclusive count) in DDMM format (e.g. `2305`)")
    today = datetime.today()
    while True:
        end_date = ''
        while not end_date.isdigit():
            print("Please enter a valid date")
            end_date = input('>').replace(' ', '')

        # assume current year unless that date is in the future
        target_date = end_date + str(today.year)
        try:
            target_date = datetime.strptime(target_date, '%d%m%Y')
        except ValueError as e:
            print("Error:", e)
            print("Unable to parse given date")
            continue
        if target_date > datetime.now():
            target_date -= timedelta(days=365)
        print(datetime.strftime(target_date, "%d/%m/%Y"))

        response = input(">Is this date correct? (y/N)").lower()
        if response in ["y", "yes"]:
            return target_date


def return_note_text_minus_comments(note: Entry, remove_plus_signs=False) -> str:
    # given a note, return its text as a string, with comment lines omitted
    retstr = ''
    for line in note.text.split('\n'):
        line = line.lstrip().replace('\n', '')
        if line.startswith(('/', '(')):
            continue
        if remove_plus_signs and len(line) > 2:
            # remove "+" because it's not relevant for comparisons in present_deletion_candidates(...)
            retstr += line.replace('+ ', '').replace('+', '') + ' '

    return retstr


def main():
    uf.validate_target_sheet_params()

    # fail early: try this before greeting the user, in case that it fails (e.g. because of user config problem)
    handler = uf.return_handler()
    notes = handler.retrieve_notes()
    workout_notes = [note for note in notes if note.is_valid_workout_note()]
    if not workout_notes:
        print("No workout notes found. Nothing to prune. Program exiting")
        exit()

    wb = openpyxl.load_workbook(p.TARGET_PATH)
    sheet = wb[p.TARGET_SHEET]

    # source and target are ready. Request user input.
    greet()
    end_date = request_end_date()

    calculated_dates = []
    deletion_candidates = []
    max_row = uf.find_row_of_cell_matching_datetime(sheet=sheet, datetime_target=end_date, date_column=p.DATE_COLUMN)
    xlsx_snippets = retrieve_xlsx_workout_snippets(sheet, max_row=max_row)
    for note in workout_notes:
        if is_deletion_candidate(xlsx_snippets=xlsx_snippets, note=note, end_date=end_date):
            deletion_candidates.append(note)
            calculated_dates.append(uf.convert_string_to_datetime(note.title))

    # we don't expect to find multiple workout notes evaluating to the same date. This is likely a user entry error.
    # note that the note titles may still be different.
    if len(calculated_dates) != len(set(calculated_dates)):
        offenders = [date for date in calculated_dates if calculated_dates.count(date) > 1]
        sorted_offenders = sorted(list(set(offenders)))
        raise ValueError("Multiple workout notes with the same calculated date have been found. "
                         "Having multiple workout notes with the same date is not a supported use case."
                         "Please either correct their dates, or concatenate them into one note.\n"
                         f"Offenders = {sorted_offenders}")

    present_deletion_candidates(deletion_candidates=deletion_candidates, xlsx_snippets=xlsx_snippets)

    if not deletion_candidates:
        print("No notes found to delete. Program exiting")
        exit()

    if not is_deletion_requested():
        print("No changes made")
        exit()

    certain = input("Press 'C' to confirm deletion. Any other key to undo: ").lower().strip()
    if certain != 'c':
        print("No changes made")
        exit()
    else:
        handler.trash_notes(deletion_candidates)
        print("Specified notes deleted. Program execution complete")


if __name__ == '__main__':
    main()

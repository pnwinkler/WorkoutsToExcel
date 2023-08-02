# this script removes workout Notes from Keep that are already written
# to the xlsx file specified in utilities.params.TARGET_PATH, up to a given, user-provided date

# How it works:
# retrieves and processes all Note objects at once,
# gives user overview of notes facing deletion, plus how they exist
# both in TARGET_PATH, and in the Keep note,
# then requests user's permission to delete

import time
import openpyxl
import gkeepapi
import utilities.params as p
import utilities.utility_functions as uf

from tabulate import tabulate
from typing import Dict, List, Union
from datetime import datetime, timedelta
# todo: make the date_xlsx_snippet_dict less flimsy and more self explanatory


def is_deletion_candidate(xlsx_snippets: Dict[str, str], note: gkeepapi.node.Note, end_date: datetime)\
        -> bool:
    # todo: test this properly
    """
    for a given Note, return whether it is already written to the xlsx file, for the correct date, as a bool
    :param xlsx_snippets: a dictionary where each key is a prettified workout's date, and each value its string
    representation in the target xlsx file.
    :param note: the Note we're considering as a deletion candidate.
    :param end_date: the cutoff point, after which we return False regardless of the Note or Excel file's value
    """

    # 1) check if valid workout note
    if note.title.isalpha() or not uf.is_workout_note(note):
        # not a date or not a workout
        return False

    # given a Note title without year, such as "14 November", we append the current year, then convert that string to
    # datetime. However, if that date would be in the future, we set note_date to use last year's value instead.
    note_date = uf.convert_string_to_datetime(note.title, regress_future_dates=True)

    if note_date == -1:
        # failed to convert workout's note_date. It is incorrectly formatted.
        return False

    # 2) do not flag as deletion candidate beyond cutoff
    if note_date >= end_date:
        return False

    # 3) is note already written to the food eaten diet xlsx file?
    note_datetime = uf.return_google_note_datetime(note, raise_if_no_valid_date=True)
    date_key: str = uf.date_to_short_string(note_datetime)
    try:
        xlsx_value = xlsx_snippets[date_key]
        if not xlsx_value:
            # there's a value, but it's the empty string or None type
            return False
    except KeyError:
        # no entry for that date
        return False

    return True


def retrieve_xlsx_workout_snippets(sheet) -> Dict[str, str]:
    # create and return a dictionary, where each key is a unique day from the previous 365 days as of the time of
    # execution, and each value is the value in the workout cell of that same row. All operating on the passed-in sheet
    # lines without dates are dropped.
    today = datetime.now()
    max_row = uf.find_row_of_cell_matching_datetime(sheet=sheet, datetime_target=today, date_column=p.DATE_COLUMN)
    min_row = max_row - 365 # note that this may not retrieve a year of data, e.g. due to empty rows
    if min_row < 1:
        min_row = 1

    xlsx_snippets = dict()

    for row in sheet.iter_rows(min_row=min_row,
                               min_col=0,
                               max_col=max(p.WORKOUT_COLUMN, p.DATE_COLUMN),
                               max_row=max_row,
                               values_only=False):
        # a "row" in this context is a tuple of cells
        # Note that setting min_col to be greater than 0 will offset all columns will be offset by that amount
        date_value: Union[str, datetime] = row[p.DATE_COLUMN - 1].value

        # params.py is 1-indexed, but openpyxl is 0-indexed
        workout = row[p.WORKOUT_COLUMN - 1].value
        if not date_value:
            # if there's no date, there's no snippet to store
            continue
        if not isinstance(date_value, datetime):
            date_value = uf.convert_string_to_datetime(date_value)
        date = uf.date_to_short_string(date_value)
        if date:
            xlsx_snippets[date] = workout

    return xlsx_snippets


def present_deletion_candidates(deletion_candidates: List[gkeepapi.node.Note],
                                date_xlsx_snippet_dict: Dict[str, str]) -> None:
    '''
    Print the following, as columns in a table: deletion_candidates, its corresponding value from
    date_xlsx_snippet_dict, a percentage similarity rating of the two strings.
    :param deletion_candidates: a list of note objects that are considered suitable for trashing, in Keep.
    :param date_xlsx_snippet_dict: a dictionary where each key is a workout's date, and each value its string
    representation in the target xlsx file.

    TABLE FORMATTED AS BELOW:

    date    note to be deleted snippet      snippet from xlsx
    ...     ...                             ...
    ...     ...                             ...

    Delete? (Y/N)
    '''
    print(f"These are the {len(deletion_candidates)} deletion candidates. They are already written to file, and "
          f"are older than your specified date range")
    print("\n**DELETION CANDIDATES**")

    # populate the matrix for tabulate
    tabulate_matrix = [[]]
    # deletion_candidates = sorted(deletion_candidates, key=lambda x: x.note.timestamps.edited)
    for note in deletion_candidates:
        # remove comment lines, as they don't appear in the xlsx file, so they're unhelpful for side-by-side comparison
        note_snippet = return_note_text_minus_comments(note, remove_plus_signs=True).replace('\n', ' ')
        note_snippet = note_snippet[:p.SNIPPET_LENGTH]

        # NOTE: we expect the note dates to be present, and in their titles
        note_date = uf.return_google_note_datetime(note)
        printable_date = uf.date_to_short_string(note_date)
        xlsx_snippet = date_xlsx_snippet_dict[printable_date][:p.SNIPPET_LENGTH].rstrip()
        similarity = uf.get_string_pct_similarity(note_snippet, xlsx_snippet)

        # append a list
        tabulate_matrix.append([printable_date, note_snippet, xlsx_snippet, str(similarity) + "%"])

    headers = ["Date", "Note snippet", "Exists in xlsx as...", "Similarity"]
    print(tabulate(tabulate_matrix, headers=headers))
    print()


def is_deletion_requested() -> bool:
    # returns True if permission is given to delete ALL notes presented by present_deletion_candidates()
    deletion_requested = input('Delete all of the above? (y/N): ').strip().lower()
    if deletion_requested == 'y':
        return True
    return False


def greet() -> None:
    greeting = '\n\t\t\t GKEEP NOTE DELETER \n' + \
               '\tdeletes workout notes from a google keep account up to a given date\n' \
               '\tprovided they are already written to file and you give your approval\n' \
               '\t(Don\'t worry, we\'ll ask you before changing anything)\n'
    print(greeting)


def request_end_date() -> datetime:
    print('\tTo start, please enter the date you wish to delete up to in DDMM format')
    print('\t(if your DDMM > today, we\'ll choose DDMM + YY-1, and ask you if that\'s OK)')
    today = datetime.today()
    while True:
        end_date = ''
        while not end_date.isdigit():
            print('Please enter a valid date')
            end_date = input('>').replace(' ', '')
        # set correct stuff and break
        target_date = end_date + str(today.year)
        try:
            target_date = datetime.strptime(target_date, '%d%m%Y')
        except ValueError as e:
            print("Error:", e)
            print("Unable to parse given date")
            continue
        if target_date > datetime.now():
            target_date -= timedelta(days=365)
        print(datetime.strftime(target_date, '%d/%m/%Y'))

        response = input('>Is this date correct? (y/N)').lower()
        if response == 'y':
            return target_date


def return_note_text_minus_comments(note: gkeepapi.node.Note, remove_plus_signs=False) -> str:
    # given a note, return its text as a string, with comment lines omitted
    retstr = ''
    for line in note.text.split('\n'):
        line = line.lstrip().replace('\n', '')
        if line.startswith(('/', '(')):
            continue
        if "home workout" in line.lower():
            continue
        else:
            if len(line) > 2 and remove_plus_signs:
                # remove "+" because it's not relevant for comparisons in present_deletion_candidates(...)
                retstr += line.replace('+ ', '').replace('+', '') + ' '

    return retstr


def main():
    if not uf.target_path_is_xslx(p.TARGET_PATH):
        raise ValueError("TARGET_PATH in utilities.parameters incorrectly set. It does not point to an xlsx file")
    if not uf.target_sheet_exists(p.TARGET_PATH, p.TARGET_SHEET):
        raise ValueError("TARGET_SHEET in utilities.parameters incorrectly set. Sheet not found in xlsx file")

    greet()
    end_date = request_end_date()
    keep = uf.login_and_return_keep_obj()
    notes = uf.retrieve_notes(keep)

    wb = openpyxl.load_workbook(p.TARGET_PATH)
    sheet = wb[p.TARGET_SHEET]

    # precaution against loss of data from mis-titled notes.
    # catch duplicate dates (user error) by comparing the list of note dates to the set of note dates
    note_dates = []
    deletion_candidates = []
    xlsx_snippets = retrieve_xlsx_workout_snippets(sheet)
    for note in notes:
        if is_deletion_candidate(xlsx_snippets=xlsx_snippets, note=note, end_date=end_date):
            deletion_candidates.append(note)
            note_dates.append(note.title)

    if len(note_dates) != len(set(note_dates)):
        offenders = [date for date in note_dates if note_dates.count(date) > 1]
        sorted_offenders = sorted(list(set(offenders)))
        raise ValueError("Two workout notes with the same date have been found. "
                         "Given that each date may have only 1 workout written to it, "
                         "deletion would result in loss of unwritten data. "
                         "Please either correct their dates, or concatenate them into one note.\n"
                         f"Offender = {sorted_offenders}")

    present_deletion_candidates(deletion_candidates=deletion_candidates, date_xlsx_snippet_dict=xlsx_snippets)

    if is_deletion_requested():
        certain = input("Press 'C' to confirm deletion. Any other key to undo: ").lower()
        if certain != 'c':
            print("No changes made")
            exit()
        else:
            for note in deletion_candidates:
                # trash() is reversible. delete() is not. Trashed notes will be deleted in 7 days.
                if note is not None:
                    note.trash()
            print("Synchronizing")
            keep.sync()
            # give sync time, in case of poor internet
            time.sleep(3)
            print("Specified notes deleted. Program execution complete")
    else:
        print("No changes made")
        exit()


if __name__ == '__main__':
    main()

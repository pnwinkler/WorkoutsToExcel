# removes workout Notes from Keep that are already written
# to the xlsx file specified in utilities.params.target_path,
# up to a given, user-provided date

# How it works:
# retrieves and processes all Note objects at once,
# gives user overview of notes facing deletion, plus how they exist
# both in target_path, and in the Keep note,
# then requests user's permission to delete

from datetime import datetime, timedelta
import utilities.utility_functions as uf
import utilities.params as p
import openpyxl
import time

# key is date (particular format!!), value is value found in xlsx file for that date
date_xlsx_snippet_dict = dict()


def is_deletion_candidate(sheet, note, end_date):
    # returns True if the Keep object that "note" refers to may be deleted, False otherwise
    # takes "sheet" in xlsx file within which to search for workout entry
    # takes "note", a Note object *copied from* Keep (not the actual online object)
    # takes "end_date" as a datetime object indicating the last date we may delete up to (inclusive)
    # deletion criteria are:
    # 1) date of note >= end_date
    # 2) note is a workout or cardio note
    # 3) note is already written to the food eaten diet xlsx file
    # 4) note is written to the correct date in xlsx file

    # 1)
    # note that second, minutes etc are not stored in either the xlsx file,
    # or in the value returned by the function below.
    # Therefore, they will not ruin the following simplistic comparison

    if note.title.isalpha():
        # not a date
        return False

    note_date = note.title + str(datetime.now().year)
    # this function converts the string to datetime,
    # and ensures that note_date is not set to a future date
    note_date = uf.convert_ddmmyyyy_to_datetime(note_date, verbose=False)

    if note_date == -1:
        # failed to convert. note_date is bad format.
        return False

    if note_date >= end_date:
        return False

    # 2)
    is_workout_note = False
    if uf.is_est_xx_mins_line(note.text):
        is_workout_note = True

    if not is_workout_note:
        return False

    # find date cell in xlsx matching the date of our Note object
    row = uf.find_row_of_datecell_given_datetime(sheet, note_date, p.date_column)
    if row == -1:
        # matching date cell not found.
        # Therefore, we assume workout is not written (Keep2Calc does not write on lines with empty date cells)
        return False

    # 3), 4)
    # check that the workout is written in the corresponding row, in the column we expect
    cell_value = sheet.cell(row=row, column=p.workout_column).value
    if isinstance(cell_value, str):
        if uf.is_est_xx_mins_line(cell_value.lower()):
            # workout is probably written. This is a crummy way to check though
            # it will break if I ever change how est_xx_mins lines are stored in the xlsx file
            # this function checks that the est_xx_mins phrase appears anywhere in the line
            date_xlsx_snippet_dict[get_printable_note_date(note)] = cell_value
        else:
            return False

    if cell_value is None:
        return False

    return True


def get_printable_note_date(note):
    # used for printing deletion options, and as a dictionary key
    # first 2 items of split will be DD or MONTH
    split = note.title.split()
    # if there's a single digit, like "7", lead it with 0.
    split = ["0" + x if len(x) < 2 else x for x in split]

    if split[0].isdigit():
        # example: ['13', January] or ['07', 'November']
        date = split[0] + split[1]
    else:
        date = split[1] + split[0]

    # abbreviate date, to something like '13 Jan' or '07 Mar'
    date = date[:2] + ' ' + date[2:5]
    return date


def present_deletion_candidates(deletion_candidates):
    # param: deletion_candidates is a list of note objects
    # (those objects are valid candidates for trashing, in the Keep app)
    # function: gives user an overview of these notes, so he can decide whether to proceed with trashing
    # format is as follows:
    '''
    date    note to be deleted snippet      snippet from xlsx
    ...     ...                             ...
    ...     ...                             ...

    Delete? (Y/N)
    '''
    snippet_length = 30
    print("\n**DELETION CANDIDATES**")
    header = 'Date\tNote snippet\t\t\t\t\t\tExists in xlsx as...'
    print(header)

    for note in deletion_candidates:
        # comment lines don't appear in the xlsx file, so they're unhelpful for side-by-side comparison
        note_snippet = return_note_text_minus_comments(note).replace('\n', ' ')
        if len(note_snippet) < (snippet_length):
            # This makes short lines fit into neat columns
            # 20 is an arbitrary number.
            note_snippet += ' ' * 20
        note_snippet = note_snippet[:snippet_length]

        print(get_printable_note_date(note), end='')
        print('\t' + note_snippet, end='')
        # give snippet from xlsx matching date of note
        # +1 to xlsx snippet length because the xlsx format separates exercises with ";"
        # By adding +1, the 2 kinds of snippet more frequently terminate on the same character.
        print('\t' + date_xlsx_snippet_dict[get_printable_note_date(note)][:snippet_length + 1].rstrip() + '...')

    print()


def is_deletion_requested():
    # returns True if permission is given to delete ALL notes presented by present_deletion_candidates()
    deletion_requested = input('Delete all? (Y/n): ').strip().lower()
    if deletion_requested == 'y':
        return True
    return False


def greet():
    greeting = '\n\t\t\t GKEEP NOTE DELETER \n' + \
               '\tdeletes workout notes from a google keep account up to a given date\n' \
               '\t*provided they are already written to file* and you give your approval\n' \
               '\t(Don\'t worry, we\'ll ask you before changing anything)\n'
    print(greeting)


def request_end_date():
    print('\tTo start, please enter the date you wish to delete up to in DDMM format')
    print('\t(if your DDMM > today, we\'ll choose DDMM + YY-1)')
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

        response = input('>Is this date correct? (Y/n)').lower()
        if response == 'y':
            return target_date


def return_note_text_minus_comments(note):
    # given a note, return its text as a string, with comment lines omitted
    retstr = ''
    for line in note.text.split('\n'):
        line = line.lstrip().replace('\n', '')
        if line.startswith(('/', '(')):
            continue
        if "home workout" in line.lower():
            continue
        else:
            if len(line) > 3:
                # remove "+" because it's not relevant for comparisons in present_deletion_candidates(...)
                retstr += line.replace('+ ', '').replace('+', '') + ' '

    return retstr


def main():
    if not uf.target_path_is_xslx():
        raise ValueError("target_path in utilities.parameters incorrectly set. It does not point to an xlsx file")
    if not uf.targetsheet_exists():
        raise ValueError("target_sheet in utilities.parameters incorrectly set. Sheet not found in xlsx file")

    greet()
    end_date = request_end_date()
    keep = uf.login_and_return_keep_obj()
    notes = uf.retrieve_notes(keep)
    deletion_candidates = []

    wb = openpyxl.load_workbook(p.target_path)
    sheet = wb[p.target_sheet]

    # precaution against loss of data from mis-titled notes.
    # catch duplicate dates (user error) by comparing the list of note dates to the set of note dates
    note_date_counter = []
    unique_note_dates = set()
    for note in notes:
        if is_deletion_candidate(sheet, note, end_date):
            deletion_candidates.append(note)
            note_date_counter.append(note.title)
            unique_note_dates.add(note.title)

    if len(note_date_counter) != len(unique_note_dates):
        for date in note_date_counter:
            if note_date_counter.count(date) > 1:
                offender = date
        raise ValueError("Two workout notes with the same date have been found. "
                         "Given that each date may have only 1 workout written to it, "
                         "deletion would result in loss of unwritten data. "
                         "Please either correct the date of one, or concatenate them into one note.\n"
                         f"Offender = {offender}")

    present_deletion_candidates(deletion_candidates)
    if is_deletion_requested():
        for note in deletion_candidates:
            # trash() is reversible. delete() is not. Trashed notes will be deleted in 7 days.
            if note is not None:
                note.trash()
        keep.sync()
        certain = input("Press 'C' to confirm deletion. Any other key to undo: ").lower()
        if certain != 'c':
            for note in deletion_candidates:
                print("No changes made")
                note.untrash()
                time.sleep(2)
        keep.sync()
    else:
        print("Specified notes deleted")
        exit()


if __name__ == '__main__':
    main()

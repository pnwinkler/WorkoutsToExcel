# removes workout Notes from Keep that are already written to the big xlsx file
# up to a given, user-provided date

# How it works:
# retrieves and processes all Note objects at once, then requests user's permission to delete

# NOTE: although ignoring / deleting each Note as it's retrieved would speed the process
# (as notes to be deleted would not have to be searched for again)
# processing all notes at once allows us to present the user an overview

from datetime import datetime, timedelta
import utilities.utility_functions as uf
import utilities.params as p
import openpyxl

# key is date (particular format!!), value is value found in xlsx file for that date
date_xlsx_snippet_dict = dict()


def retrieve_notes(keep):
    # first retrieve a list of Note objects
    # we want a local cache of all keep files to minimize requests made to Keep
    # that minimizes the effect of latency, in addition to improving stability
    # (if the internet suddenly cuts out, a failed request could cause problems)
    print('Retrieving notes')
    gnotes = keep.all()
    if not gnotes:
        raise ValueError('No notes found. Incorrect username or password?')
    return gnotes


def is_deletion_candidate(sheet, note, end_date):
    # returns True if the Keep object that "note" refers to may be deleted, False otherwise
    # takes "sheet" in xlsx file within which to search for workout entry
    # takes "note", a Note object *copied from* Keep (not the actual online object)
    # takes "end_date" as a datetime object indicating the last date we may delete up to (inclusive)
    # deletion criteria are:
    # 1) date of note is less than end_date
    # 2) note is a workout or cardio note
    # 3) note is already written to the food eaten diet xlsx file
    # 4) note is written to the correct date in xlsx file

    # 1)
    # note that second, minutes etc are not stored in either the xlsx file, or in the value returned by the
    # function below. Therefore, they will not ruin the following simplistic comparison

    if note.title.isalpha():
        # not a date
        return False

    note_date = note.title + str(datetime.now().year)
    note_date = uf.convert_ddmmyyyy_to_datetime(note_date, verbose=False)

    if note_date == -1:
        return False

    if note_date >= end_date:
        return False

    # 2)
    is_workout_note = False
    if uf.is_est_xx_mins_line(note.text):
        is_workout_note = True
        # print("AFTER")
        # exit()

    if not is_workout_note:
        return False

    # find date cell in xlsx matching the date of our Note object
    row = uf.find_xlsx_datecell(sheet, note_date, p.date_column)
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

            # this is also shit. We have a datetime object used for scouting the xlsx file
            # and a string here used as a key. It's probably gonna result in inconsistencies
            # but I want to use a string as a dict key, not a datetime object.
            # maybe that's stupid. I'll find out soon
            # print(f"DEBUG: note_date={note_date}, row={row}, cell_value={cell_value}")
            # October 16th value never got added here
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

    # date += str(datetime.now().year)
    # date = uf.convert_ddmmyyyy_to_datetime(date)
    # remove year
    # date = date[:-4]
    date = date[:2] + ' ' + date[2:5]
    # should be like '13 Jan'
    return date


def present_deletion_candidates(deletion_candidates):
    # takes a list of notes facing deletion
    # gives user an overview of these notes, so he can decide whether to proceed
    # format is as follows:
    # {notes to be deleted, an abort option, a snippet from the allegedly matched cell in the xlsx file, ...}
    '''
    example layout:

    date    note to be deleted snippet      snippet from xlsx
    ...     ...                             ...
    ...     ...                             ...

    Delete? (Y/N)
    '''
    snippet_length = 30
    header = 'Date\tNote snippet\t\t\t\t\tExists in xlsx as...'
    print(header)

    # todo: get this to print neatly. ljust or something might help
    # that shit is way too involved. I'm shelving it for now.
    # example problem:
    '''
    19 Mar	Home legs arms side delts work	Home legs + arms + side delts...
    16 Mar	Home workout Est ?? mins 	Est ?? mins...
    13 Mar	Home workout Est ?? mins 	Est ?? mins...
    11 Mar	Some band work: arms, shoulder	Some band work: arms, shoulder...
    '''
    for note in deletion_candidates:
        # comment lines don't appear in the xlsx file, so they're unhelpful for side-by-side comparison
        note_snippet = return_note_text_minus_comments(note).replace('\n', ' ')
        if len(note_snippet) < (snippet_length):
            # This makes even short lines fit into neat columns
            # 20 is an arbitrary number.
            note_snippet += ' ' * 20
        note_snippet = note_snippet[:snippet_length]

        print(get_printable_note_date(note), end='')
        print('\t' + note_snippet, end='')
        # give snippet from xlsx matching date of note, limited in length by snippet_length
        # +1 to xlsx snippet length because it ";" separates exercises. By adding +1, the 2 kinds of snippet
        # appear to terminate on the same character, more often.
        print('\t' + date_xlsx_snippet_dict[get_printable_note_date(note)][:snippet_length+1].rstrip() + '...')

    print()


def is_deletion_requested():
    # returns True if permission is given to delete ALL notes presented by present_deletion_candidates()
    deletion_requested = input('\nDelete all? (Y/n): ').lower()
    if deletion_requested == 'y':
        return True
    return False


def greet():
    greeting = '\n\t\t GKEEP NOTE DELETER \n' + \
               '\tdeletes workout notes from a google keep account up to a given date\n'
    print(greeting)


def request_end_date():
    print('\tto start, please enter the date you wish to delete up to in DDMM format')
    print('\t(if your DDMM > today, we\'ll choose DDMM + YY-1)')
    today = datetime.today()
    while True:
        end_date = ''
        while not end_date.isdigit():
            print('Please enter a valid date')
            end_date = input('>').replace(' ', '')
        # set correct stuff and break
        tar_date = end_date + str(today.year)
        try:
            tar_date = datetime.strptime(tar_date, '%d%m%Y')
        except ValueError as e:
            print("Error:", e)
            print("Unable to parse given date")
            continue
        if tar_date > datetime.now():
            tar_date -= timedelta(days=365)
        print(datetime.strftime(tar_date, '%d/%m/%Y'))

        response = input('>Is this date correct? (y/n)').lower()
        if response == 'y':
            return tar_date


def return_note_text_minus_comments(note):
    # given a note, return its text as a string, with comment lines omitted
    # the returned string includes newlines, roughly as were present originally
    retstr = ''
    for line in note.text.split('\n'):
        line = line.lstrip().replace('\n', '')
        if line.startswith(('/', '(')):
            continue
        if "home workout" in line.lower():
            continue
        else:
            if len(line) > 3:
                # remove "+" because they're not relevant to comparison in present_deletion_candidates
                retstr += line.replace('+ ', '').replace('+', '') + '\n'

    return retstr


def main():
    if not uf.target_is_xslx():
        raise ValueError("target_path in utilities.parameters incorrectly set. It does not point to an xlsx file")
    if not uf.targetsheet_exists():
        raise ValueError("target_sheet in utilities.parameters incorrectly set. Sheet not found in xlsx file")

    greet()
    end_date = request_end_date()
    keep = uf.login_and_return_keep_obj()
    notes = retrieve_notes(keep)
    deletion_candidates = []

    wb = openpyxl.load_workbook(p.target_path)
    sheet = wb[p.target_sheet]

    for note in notes:
        if is_deletion_candidate(sheet, note, end_date):
            deletion_candidates.append(note)

    present_deletion_candidates(deletion_candidates)
    if is_deletion_requested():
        for note in deletion_candidates:
            # trash() is reversible. delete() is not. Trashed notes will be deleted in 7 days.
            note.trash()
    else:
        exit()


if __name__ == '__main__':
    main()

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
    # TODO: redo this stuff. We don't want to delete the end_date Note,
    #   we want to delete all Notes up to and including the end date

    # takes a Note object and returns True if it may be deleted, False otherwise
    # note is the Note object from Keep
    # end_date is a datetime object indicating the last date we may delete up to (inclusive)
    # deletion criteria are:
    # 1) date of note is less than end_date
    # 2) note is a workout or cardio note
    # 3) note is already written to the food eaten diet xlsx file
    # 4) note is written to the correct date in xlsx file

    # 1)
    # TODO: make sure this does what it's supposed to and doesn't crash or whatever
    #  ensure correct year and stuff. Make sure that seconds or whatever don't fuck up the comparison
    note_date = uf.convert_ddmmyyyy_to_datetime(note.title)
    if note_date >= end_date:
        return False

    # 2)
    is_workout_note = False
    for line in note.text:
        if uf.is_est_xx_mins_line(line):
            is_workout_note = True

    if not is_workout_note:
        return False


    # find date cell in xlsx matching the date of our Note object
    row = uf.find_xlsx_datecell(sheet, end_date, p.date_column)
    if row == -1:
        # matching date cell not found.
        # Therefore, we assume workout is not written (Keep2Calc does not write on lines with empty date cells)
        return False

    # check that the workout is written in the corresponding row, in the column we expect
    cell_value = sheet.cell(row=row, column=p.workout_column).value
    if isinstance(cell_value, str):
        if uf.is_est_xx_mins_line(cell_value.lower()):
            # workout is probably written. This is a crummy way to check though
            # it will break if I ever change how est_xx_mins lines are stored in the xlsx file
            # this function checks that the est_xx_mins phrase appears anywhere in the line
            pass
        else:
            return False






    pass


def delete_note_from_keep(note):
    # takes a Note object, and removes it from Keep (i.e. deletes it)
    pass

def get_note_date(Note_obj):
    pass

def find_xlsx_date_and_workout(date):
    # if isinstance(sheet.cell(row=r, column=2).value, datetime):
    #     cell_date = sheet.cell(row=r, column=2).value
    #     if cell_date.day == now.day:
    pass


def present_deletion_candidates(notes_to_be_deleted):
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
    header = 'Date\tNote snippet\t\tExists in xlsx as...'
    print(header)

    # we need:
    # 1) dates from Note objects
    # 2) access to xlsx dates, neighboring cells & their contents
    # deal with missing xlsx entries or whatever else. So it doesn't crash
    pass


def deletion_requested_tf():
    # todo: don't make this return true. that makes no sense. Change the logic or the name
    # returns True if permission is given to delete ALL notes presented by present_deletion_candidates()
    pass


def greet():
    greeting = '\n\t\t GKEEP NOTE DELETER \n' + \
               '\tdeletes workout notes from a google keep account up to a given date\n'
    print(greeting)

    # todo: think of some way to stop it deleting workout notes from the future?
    # perhaps someday that's a bug I'd that my changing habits might introduce


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
    if deletion_requested_tf():
        for note in deletion_candidates:
            delete_note_from_keep(note)


if __name__ == '__main__':
    main()
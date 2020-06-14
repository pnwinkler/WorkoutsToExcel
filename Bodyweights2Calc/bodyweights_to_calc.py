# retrieves bodyweights from Google Keep, then writes them to the correct date cell in the specified file
# does intelligent stuff too, like alert the user to missing entries, etc
# intended to be run via crontab. That's why we catch all errors and write to Desktop
# REMEMBER to change params whenever necessary.
# Note that this file uses a different params to Keep2CalcV4

# todo: make it cope with '?, ' entries!

import gkeepapi
import openpyxl
import re
from datetime import datetime
from utilities.credentials import username, password
import utilities.params as p
import os

def main():
    # we put this inside a try block so that we can write un-programmed errors to our desired location
    # as well as errors that we intentionally raise

    # if error note exists, don't run
    if os.path.isfile(ERROR_LOG):
        exit()

    try:
        notes = login_and_return_notes()
        bodyweights = find_and_return_bodyweights(notes)
        logic_check_bodyweights(bodyweights)
        bw = select_correct_bodyweight(bodyweights)
        write_bw_to_file(bw)

    except Exception as e:
        write_error_and_exit(e)


def login_and_return_notes():
    # handle exceptions like changed password or whatever preventing login
    # or an absent internet connection preventing login

    # todo: test for internet connectivity first

    keep = gkeepapi.Keep()

    if not username:
        write_error_and_exit('No username provided')
    if not password:
        write_error_and_exit('No password provided')

    keep.login(username, password)

    # retrieves a list of Note objects
    gnotes = keep.all()
    if not gnotes:
        write_error_and_exit('No notes found', 'Username/password may be incorrect. Please review params.py')
    return gnotes


def find_and_return_bodyweights(notes):
    # take all notes as a parameter
    # find the bodyweights note, then returns its contents

    # match 2 digits + comma or 2 digits + 1 decimal point + comma.
    # in both cases, a space is allowed both before and after the comma
    bw_reg = re.compile(r'(\d\d\.\d\s?,)|(\d\d\s?,)')

    for gnote in notes:
        # we ignore the title. We match only the body
        text = gnote.text

        if text.count('\n') != 0:
            # our bodyweights file will have no newlines
            continue
        else:
            if bw_reg.search(text):
                # we have a match. Now we proof that the majority of the line is relevant
                str_copy = text[::]
                orig_len = len(str_copy)
                match_lst_tpls = bw_reg.findall(text)
                for match_tup in match_lst_tpls:
                    str_copy = str_copy.replace(match_tup[0], '')
                if len(str_copy) < (0.3 * orig_len) + 1:
                    # 70%+ match
                    return text

    write_error_and_exit('No matching note found',
                         'Does your bodyweight note exist? Is it in a valid format? ' + \
                         'Like 2 digits and a comma, or 2 digits 1 decimal place and a comma. ' + \
                         'Please ENSURE that there is no newline in your note')


def logic_check_bodyweights(bodyweights_str):
    # todo: rename
    # raises errors if missing values etc. Just inform user of any problems
    # decide what to do in the case of errors that the user does not need to know of
    # note also that bodyweights need to be checked in 2 locations: 1) the downloaded bodyweights
    # 2) the already logged or absent-from-file bodyweights.

    # verify that the number of missing bodyweights exactly matches the number in the arg str
    wb = openpyxl.load_workbook(p.target_path)
    sheet = wb[p.target_sheet]

    # 1) find first empty bodyweight cell neighboring a date cell
    # 1140 is hacky - it's just where we're at now
    first_vacancy_row = None
    for t in range(1140, 15000):
        if sheet.cell(row=t, column=p.bodyweights_column).value == None:
            if isinstance(sheet.cell(row=t, column=p.dates_column).value, datetime):
                # empty bodyweight cell found next to a date cell.
                first_vacancy_row = t

    if not first_vacancy_row:
        # we are up to date ***OR there's a problem finding vacancies***
        exit()

    # 2) find today's date, so we can calculate the number of vacancies
    todays_row = None
    now = datetime.now()
    r = first_vacancy_row
    # + 100 is an arbitrary cut-off point
    while r < first_vacancy_row + 100:
        r += 1
        # check datetime cells in Column C for exercise_datetime match...
        if isinstance(sheet.cell(row=r, column=2).value, datetime):
            cell_date = sheet.cell(row=r, column=2).value
            if cell_date.day == now.day:
                # we found today's cell
                todays_row = r

    if not todays_row:
        write_error_and_exit('Program did not find a date cell matching today\'s date in target file',
                             'This may be a programming error, in logic_check_bodyweights(), or simply an absent date cell')

    # 3) find the number of cells between them (inclusive count, hence the +1)
    count_cells_to_fill = todays_row - first_vacancy_row + 1

    # 4) check this count matches the length of our argstr.split(',')
    if count_cells_to_fill != bodyweights_str.split(','):
        write_error_and_exit(
            f"{count_cells_to_fill} vacancies in target file found, but only " +
            f"{bodyweights_str.split(',')} values in the bodyweight note")

    # 5) if it does, we can proceed

    # compare the number of unwritten bodyweights to the holes in the xlsx file
    # double check that the two don't already duplicate each other
    # etc...
    pass


# def select_correct_bodyweight(bodyweights):
#     # choose the correct bodyweight to return
#     # alerts need to be figured in this file somewhere
#     # should have a way to cope with previously interrupted service
#     #   i.e. if the program wasn't run for a week, it won't fail or do something weird
#     return None
#
#
# def write_bw_to_file():
#     def find_correct_cell():
#         # find the correct cell to write to. Handle errors / problems that may arise.
#         return None
#
#     target_cell = find_correct_cell()
#     # write to target_cell, close file, exit, do any tidyup or logging that should be done
#     pass


def write_error_and_exit(error, solution="None provided"):
    # takes a String error message and String solution.
    # Writes both to the location specified in params, then exits program
    # the purpose of this is to notify the user of any error
    # tell them what to do, where to look, what and where this program is, etc
    error_msg = f"ERROR: {__file__} raised error:\n" + error + "\n\n" + "Suggested action:\n\t" + solution
    with open(ERROR_LOG) as f:
        f.write(error_msg)
        f.write('\n\n\nSo long as this file exists here, with this name, the program will not execute again.')
        # ... as specified in main()

    exit()


if __name__ == '__main__':
    main()

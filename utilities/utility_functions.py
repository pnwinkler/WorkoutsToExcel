import gkeepapi
import openpyxl
import shutil
import re
from datetime import datetime
from utilities.params import *
import getpass


def backup_targetpath():
    if not backup_folder_name:
        bk_folder_name = 'Keep2Calc.backups'
    else:
        bk_folder_name = backup_folder_name

    backup_folder = os.path.join(os.path.dirname(target_path), bk_folder_name)

    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)

    now = datetime.now()
    dmy = '{}.{}.{}'.format(now.day, now.month, now.year)
    backup_basename = 'backup_' + dmy + '_' + os.path.basename(target_path)
    backup_full_path = os.path.join(backup_folder, backup_basename)

    if not os.path.exists(backup_full_path):
        print('Backing up target file')
        shutil.copy(target_path, backup_full_path)


def convert_ddmmyyyy_to_datetime(date_str, verbose=True):
    # take string in form DDMMYYYY and return its datetime equivalent
    # also accepts strings like DDMONTHYYY where MONTH is a string
    # tolerant of spaces, newlines, semi-colons
    # returns -1 if effort fails
    date_str = date_str.replace('\n', '').replace(';', '').replace(' ', '').replace('.', '')

    # if not date_str.isdigit():
    #     raise ValueError(f'Invalid parameter for utilities convert_ddmm_to_datetime, date_str={date_str}')
    #     return -1

    try:
        datetime_obj = datetime.strptime(date_str, '%d%B%Y')
    except ValueError:
        try:
            datetime_obj = datetime.strptime(date_str, '%d%b%Y')
        except ValueError:
            try:
                datetime_obj = datetime.strptime(date_str, '%B%d%Y')
            except ValueError:
                try:
                    datetime_obj = datetime.strptime(date_str, '%b%d%Y')
                except Exception as e:
                    # Possible causes: UTF 8 bullshit; unconverted data like "day 1"
                    if verbose:
                        print('Error in utilities convert_ddmm_to_datetime:', e)
                    return -1
    now = datetime.now()
    datetime_obj = datetime_obj.replace(year=now.year)
    if now < datetime_obj:
        # exercise would be in the future, so we assume it's from last year
        return datetime_obj.replace(year=now.year - 1)
    return datetime_obj


def count_empty_cells_between_rows(sheet, start_row, end_row, cols_lst: list):
    # a non-inclusive count. Given target sheet, start and end rows, and a simple or composite key, counts how many
    # rows between the 2 passed in rows have empty values in the key columns

    if isinstance(cols_lst, str):
        cols_lst = list(cols_lst)
    cols = [int(x) for x in cols_lst]

    count = 0
    for r in range(start_row + 1, end_row):
        for col in cols:
            if not sheet.cell(row=r, column=col).value:
                count += 1
                break
    return count


def find_row_of_datecell_given_datetime(sheet, datetime_target, date_column=2) -> int:
    # todo: make this handle full datetimes better. Like 2021-05-13 12:09:53
    #  current behavior is to fail to match "2021-05-13" because it's not "2021-05-13 12:09:53", for example
    # returns row value of cell containing specified date, in specified column
    # returns -1 if not found
    # takes parameter sheet: a valid sheet object in an xlsx file
    # takes parameter datetime_target: the datetime date to search for in date_column
    # takes parameter date_column: column in which to search for date

    datetime_target = datetime_target.replace(hour=0, minute=0, second=0, microsecond=0)

    # this may be redundant. We can probably assume we'll get a proper sheet object
    if not isinstance(sheet, openpyxl.worksheet.worksheet.Worksheet):
        print(
            f'Invalid parameter: find_row_of_datecell_given_datetime did not receive a valid sheet, sheet type = {type(sheet)}')
        return -1
    if not isinstance(datetime_target, datetime):
        print(
            f'Invalid parameter: find_row_of_datecell_given_datetime did not receive a valid datetime_target. It received: {datetime_target}')
        return -1

    # find date cell matching the "date" parameter in the given sheet
    # note that in xlsx files:
    # headers & strings are str,
    # dates are datetime objects,
    # empty cells are NoneType
    r = 0
    empty_cell_count = 0
    while True:
        r += 1
        # check datetime cells in date_column for exercise_datetime match.
        # break if too many empty cells found in place of dates.
        if isinstance(sheet.cell(row=r, column=date_column).value, datetime):
            empty_cell_count = 0
            if sheet.cell(row=r, column=date_column).value == datetime_target:
                return r

            # if examined cell is distant from workout's date, jump closer
            # we assume continuity in file's date column: that there's no time gap between start and final date.
            days_to_advance = (datetime_target - sheet.cell(row=r, column=date_column).value).days
            if days_to_advance > 3:
                r += days_to_advance - 2
        else:
            # it's possible that some cells in this column are neither None nor datetime
            # but we still break after 50 non-date cells, given that we're looking for dates
            # a few cells may be empty, for formatting reasons, so don't set the cap too low.
            # but there's no reason to have 50+ non-date cells in a row.
            empty_cell_count += 1
            if empty_cell_count > 50:
                return -1


def return_first_empty_bodyweight_row(sheet, date_column=2, bodyweight_column=3):
    # returns the integer row where:
    # 1) there's a date column cell filled in
    # 2) there's a bodyweights column cell that's empty
    # 3) the previous row has a filled in date cell, and bodyweights cell (disregarding empty rows, e.g. at year's end)

    today = datetime.now()
    todays_row = find_row_of_datecell_given_datetime(sheet, today, date_column)

    if sheet.cell(row=todays_row, column=bodyweight_column).value:
        return todays_row

    num_rows_to_check = 10000
    first_occurrence = todays_row
    for x in range(num_rows_to_check):
        # search backwards
        row = todays_row - x
        try:
            row_has_date = isinstance(sheet.cell(row=row, column=date_column).value, datetime)
            row_has_bodyweight = isinstance(sheet.cell(row=row, column=bodyweight_column).value, (str, float, int))
            if row_has_date and not row_has_bodyweight:
                first_occurrence = row
            elif row_has_bodyweight:
                break
        except IndexError as e:
            raise ValueError(f"Failed to find empty bodyweight cell. Row index out of range. Exception {e}")

    if x != num_rows_to_check:
        return first_occurrence
    raise ValueError(f"Failed to find empty bodyweight cell. Examined {num_rows_to_check} rows")


def is_est_xx_mins_line(line):
    # I decided against putting this regex in utilities.params because
    # it's fundamental to how my programs work, and cannot be changed without significant consequence
    # it would also introduce stylistic inconsistencies in the xlsx file,
    # when future workouts are written with a different stylistic standard.
    est_xx_mins_reg = re.compile(r'(est \d\d(\d)? min)|(est \?\? min)|(est \?\?\? min)', re.IGNORECASE)
    return re.search(est_xx_mins_reg, line)


def login_and_return_keep_obj():
    keep = gkeepapi.Keep()

    try:
        from utilities.credentials import username, password
    except FileNotFoundError:
        # to avoid typing your username each time, change the following line in params.py
        # username = 'YOUR_USERNAME@gmail.com'
        username = input('Google Keep username: ')

    # getpass obscures the password as it's entered
    if password is None:
        password = getpass.getpass('Google Keep password: ')
    print('Logging in...')
    keep.login(username, password)
    return keep


def retrieve_notes(keep):
    # retrieves a list of not trashed Note objects
    print('Retrieving notes')
    # gnotes = keep.all()
    # gnotes = keep.find(pinned=True, archived=False, trashed=False)
    gnotes = keep.find(trashed=False)
    if not gnotes:
        raise ValueError('No notes found. Incorrect username or password?')
    return gnotes


def return_now_as_friendly_datetime():
    # return datetime.now() in a usable format (that the other programs expect)
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


def target_path_is_xslx():
    # returns True if utilities.target_path variable points to .xslx file
    filename, file_extension = os.path.splitext(target_path)
    if file_extension == '.xlsx':
        return True
    return False


def targetsheet_exists():
    wb = openpyxl.load_workbook(target_path)
    if target_sheet in wb.sheetnames:
        return True
    else:
        return False

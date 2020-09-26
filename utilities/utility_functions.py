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


def return_now_as_friendly_datetime():
    # return datetime.now() in a usable format (that the other programs expect)
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


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
        date_str = datetime.strptime(date_str, '%d%B%Y')
    except ValueError:
        try:
            date_str = datetime.strptime(date_str, '%d%b%Y')
        except ValueError:
            try:
                date_str = datetime.strptime(date_str, '%B%d%Y')
            except ValueError:
                try:
                    date_str = datetime.strptime(date_str, '%b%d%Y')
                except Exception as e:
                    # Possible causes: UTF 8 bullshit; unconverted data like "day 1"
                    if verbose:
                        print('Error in utilities convert_ddmm_to_datetime:', e)
                    return -1
    now = datetime.now()
    date_str = date_str.replace(year=now.year)
    if now < date_str:
        # exercise would be in the future, so we assume it's from last year
        return date_str.replace(year=now.year - 1)
    return date_str


def find_xlsx_datecell(sheet, datetime_date, date_column=2):
    # returns row value of cell containing specified date, in specified column
    # returns -1 if not found
    # takes parameter sheet: a valid sheet object in an xlsx file
    # takes parameter datetime_date: the datetime date to search for in date_column
    # takes parameter date_column: column in which to search for date

    # this may be redundant. We can probably assume we'll get a proper sheet object
    if not isinstance(sheet, openpyxl.worksheet.worksheet.Worksheet):
        print(f'Invalid parameter: find_xlsx_datecell did not receive a valid sheet, sheet type = {type(sheet)}')
        return -1
    if not isinstance(datetime_date, datetime):
        print(
            f'Invalid parameter: find_xlsx_datecell did not receive a valid datetime_date. It received: {datetime_date}')
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
            if sheet.cell(row=r, column=date_column).value == datetime_date:
                return r

            # if examined cell is distant from workout's date, jump closer
            # we assume continuity in file's date column: that there's no time gap between start and final date.
            days_to_advance = (datetime_date - sheet.cell(row=r, column=date_column).value).days
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

import re
import os
import shutil
import getpass
import gkeepapi
import openpyxl
import GKeepToCalc.utilities.params as p

from datetime import datetime
from typing import Union, List, Optional


def backup_target_path():
    # backup the file at p.TARGET_PATH, unless it was already backed up earlier today
    # todo: consider allowing multiple backups per day. Just rename the previous backup, if present. This may be useful
    #  when performing multiple executions per day, e.g. testing, or bw + workout uploads same day.
    if p.BACKUP_FOLDER_NAME:
        bk_folder_name = p.BACKUP_FOLDER_NAME
    else:
        bk_folder_name = 'Keep2Calc.backups'

    backup_folder = os.path.join(os.path.dirname(p.TARGET_PATH), bk_folder_name)

    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)

    now = datetime.now()
    dmy = '{}.{}.{}'.format(now.day, now.month, now.year)
    backup_basename = 'backup_' + dmy + '_' + os.path.basename(p.TARGET_PATH)
    full_backup_path = os.path.join(backup_folder, backup_basename)

    if not os.path.exists(full_backup_path):
        print('Backing up target file')
        shutil.copy(p.TARGET_PATH, full_backup_path)


def convert_string_to_datetime(date_str: Union[str, datetime],
                               verbose=True,
                               disallow_future_dates=True,
                               raise_on_failure=False,
                               err_msg: Optional[str] = None) -> Union[int, datetime]:
    # todo: rename this function, split it up, and add assertions.
    # todo: split this function up into more single-purpose parts.
    # take string in form DDMMYYYY and return its datetime equivalent. If disallow_future_dates, then the returned
    # datetime will always be in the past.
    # tolerant of spaces, newlines, semi-colons
    # returns -1 if effort fails, unless raise_on_failure is True.
    # if infer_year_if_absent, then replace the default 1900 year with the most recent year, such that the date would
    # still be in the past
    if isinstance(date_str, datetime):
        return date_str

    date_str = date_str.replace('\n', '').replace(';', '').replace(' ', '').replace('.', '')

    year_formats_to_try = ['%d%B%Y', '%d%b%Y', '%B%d%Y', '%b%d%Y']
    no_year_formats_to_try = ['%d%B', '%d%b', '%B%d', '%b%d']

    for year_format in year_formats_to_try:
        try:
            datetime_obj = datetime.strptime(date_str, year_format)
        except ValueError:
            continue

        now = datetime.now()
        if now < datetime_obj and disallow_future_dates:
            # datetime is in the future, but future date is not wanted. Return previous year.
            return datetime_obj.replace(year=now.year - 1)
        return datetime_obj

    for no_year_format in no_year_formats_to_try:
        try:
            datetime_obj = datetime.strptime(date_str, no_year_format)
        except ValueError:
            continue

        now = datetime.now()
        if datetime_obj.year < 2000:
            datetime_obj = datetime_obj.replace(year=now.year)

        if now < datetime_obj and disallow_future_dates:
            # datetime is in the future, but future date is not wanted. Return previous year.
            return datetime_obj.replace(year=now.year - 1)
        return datetime_obj

    # matching to datetime failed, both with and without year
    if raise_on_failure:
        raise ValueError(err_msg)
    if verbose:
        print(f'Error in utilities convert_ddmm_to_datetime. Failed to convert this string to datetime: {date_str}')
    return -1


def count_empty_contiguous_rows_within_range(sheet, start_row, end_row, cols_lst: List[int]) -> int:
    """
    Return a non-inclusive count of the contiguously empty rows between start and end rows, given a simple or composite
    key (cols_lst). If the key is composite, then count only those rows where all columns in a given row have no value
    :param sheet: the Excel sheet
    :param start_row: the row at which to start counting
    :param end_row: the row at which to stop counting
    :param cols_lst: the columns in which to check for values
    :return: a count of the empty rows found
    """

    if isinstance(cols_lst, str):
        cols_lst = list(cols_lst)
    cols = [int(x) for x in cols_lst]

    count = 0
    for row in range(start_row, end_row + 1):
        for col in cols:
            if sheet.cell(row=row, column=col).value:
                return count
        count += 1
    return count


def get_pretty_date(datetime_obj: Union[datetime, str]) -> str:
    # expects a datetime object. Returns a pretty string representation of it
    # example output: '13 Jan' or '07 Mar'. The exact format is user preference.
    if isinstance(datetime_obj, str):
        datetime_obj = convert_string_to_datetime(datetime_obj)
    return datetime_obj.strftime('%d %b')


def return_raw_note_date(note: gkeepapi.node.Note, raise_if_no_date=False) -> Union[str, datetime]:
    assert isinstance(note, gkeepapi.node.Note), "return_raw_note_date did not receive a Note object"
    title = note.title
    if raise_if_no_date and not title:
        raise ValueError("No date found in expected place (note title)")
    return note.title


def return_note_datetime(note: gkeepapi.node.Note, raise_if_no_date=False, disallow_future_dates=True) -> datetime:
    assert isinstance(note, gkeepapi.node.Note), "return_raw_note_date did not receive a Note object"
    raw_date = str(return_raw_note_date(note=note, raise_if_no_date=raise_if_no_date))
    date = convert_string_to_datetime(raw_date,
                                      disallow_future_dates=disallow_future_dates,
                                      raise_on_failure=True)
    return date


def find_row_of_datecell_given_datetime(sheet, datetime_target: datetime, date_column: int, raise_on_failure=False) \
        -> int:
    # returns row value of cell containing specified date, in specified column
    # returns -1 if not found
    # takes parameter sheet: a valid sheet object in an xlsx file
    # takes parameter datetime_target: the datetime date to search for in DATE_COLUMN
    # takes parameter DATE_COLUMN: column in which to search for date

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
    # note that in xlsx files: headers and strings are str, dates are datetime objects, empty cells are NoneType
    r = 0
    empty_cell_count = 0
    while True:
        r += 1
        # check datetime cells in DATE_COLUMN for exercise_datetime match. Break if too many empty cells found instead
        # of dates.
        examined_cell_value = sheet.cell(row=r, column=date_column).value
        if isinstance(examined_cell_value, datetime):
            if examined_cell_value == datetime_target:
                return r
            empty_cell_count = 0

            # if examined cell is distant from workout's date, jump closer
            days_to_advance = (datetime_target - examined_cell_value).days
            if days_to_advance > 3:
                r += days_to_advance - 2

            # we assume continuity: that there's no omitted date between start and final date file's date column
            # this condition can only be true if there are dates missing
            if isinstance(sheet.cell(row=r, column=date_column).value, datetime):
                if sheet.cell(row=r, column=date_column).value > datetime_target:
                    raise ValueError(f"You're missing one or more dates in your date column ({p.DATE_COLUMN})")

        else:
            # break after 50 non-date cells. A few cells may be empty, for formatting reasons, so don't set the cap too
            # low. 50+ non-date cells in a row is far beyond what we expect.
            empty_cell_count += 1
            if empty_cell_count > 50:
                if raise_on_failure:
                    raise ValueError("Matching date cell not found in target sheet")
                return -1


def return_first_empty_bodyweight_row(sheet, date_column, bodyweight_column) -> int:
    # returns the integer row where:
    # 1) there's a date column cell filled in
    # 2) there's a bodyweights column cell that's empty
    # 3) the previous row has a filled in date cell, and bodyweights cell (disregarding empty rows, e.g. at year's end)
    # searches backwards. If there is no candidate, then return None.

    today = datetime.now()
    todays_row = find_row_of_datecell_given_datetime(sheet, today, date_column)

    if sheet.cell(row=todays_row, column=bodyweight_column).value:
        raise ValueError(f"Today's bodyweight cell is already written to")

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


def est_xx_mins_line_in_note_text(note_text) -> bool:
    return is_est_xx_mins_line(note_text)


def is_workout_note(note: gkeepapi.node.Note, raise_error_if_has_xx_line_but_no_date=False) -> bool:
    is_workout = is_est_xx_mins_line(note.text)
    if is_workout:
        if raise_error_if_has_xx_line_but_no_date:
            if not convert_string_to_datetime(note.title, verbose=False):
                raise ValueError("The note above has an est xx mins line but no date could be extracted from its title")
    return is_workout


def is_est_xx_mins_line(line) -> bool:
    # I decided against putting this regex in utilities.params because
    # it's fundamental to how my programs work, and cannot be changed without significant consequence
    # it would also introduce stylistic inconsistencies in the xlsx file,
    # when future workouts are written with a different stylistic standard.
    est_xx_mins_reg = re.compile(r'(est \d(\d)?(\d)? min)|(est \? min)|(est \?\? min)|(est \?\?\? min)', re.IGNORECASE)
    return bool(re.search(est_xx_mins_reg, line))


def login_and_return_keep_obj() -> gkeepapi.Keep:
    keep = gkeepapi.Keep()

    try:
        from GKeepToCalc.utilities.credentials import username, password
    except FileNotFoundError:
        username = input('Google Keep username: ')
        print("You can save your username as an environment variable, which can save you from typing your username "
              "each time (see utilities/credentials.py)")

    # getpass obscures the password as it's entered
    if password is None:
        password = getpass.getpass('Google Keep password: ')
    print('Logging in...')
    keep.login(username, password)
    return keep


def retrieve_notes(keep) -> List[gkeepapi.node.Note]:
    # retrieves a list of not trashed Note objects
    assert isinstance(keep, gkeepapi.Keep), "Invalid object passed in to retrieve_notes function"
    print('Retrieving notes')
    # gnotes = keep.all()
    # gnotes = keep.find(pinned=True, archived=False, trashed=False)
    gnotes = keep.find(trashed=False)
    if not gnotes:
        raise ValueError('No notes found. Incorrect username or password?')
    return gnotes


def return_now_as_friendly_datetime() -> datetime:
    # return datetime.now() in a usable format (that the other programs expect)
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


def target_path_is_xslx(path) -> bool:
    # returns True if utilities.TARGET_PATH variable points to .xslx file
    filename, file_extension = os.path.splitext(path)
    if file_extension == '.xlsx':
        return True
    return False


def targetsheet_exists(path, target_sheet) -> bool:
    wb = openpyxl.load_workbook(path)
    if target_sheet in wb.sheetnames:
        return True
    else:
        return False

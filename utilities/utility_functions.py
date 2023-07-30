import re
import os
import shutil
import openpyxl
import utilities.params as p

from datetime import datetime
from typing import Union, List
from difflib import SequenceMatcher


def backup_file_to_dir(file: str, backup_directory: str) -> None:
    """
    Backup the file to the specified directory. If the directory does not exist, create it.
    """
    os.makedirs(backup_directory, exist_ok=True)

    now = datetime.now()
    dmy = '-'.join(str(v) for v in [now.day, now.month, now.year])
    backup_basename = "_".join(['backup', dmy, os.path.basename(p.TARGET_PATH)])
    full_backup_path = os.path.join(backup_directory, backup_basename)

    try:
        shutil.copy(file, full_backup_path)
    except Exception as e:
        print(f'Warning: Failed to backup target file to {full_backup_path}. Error: {e}')


def convert_string_to_datetime(date_str: str, regress_future_dates=True) -> datetime:
    """
    Return the input string's datetime equivalent. Raise on failure to convert.
    :param date_str: the string to convert
    :param regress_future_dates: if true, then subtract one year from the date to be returned, if that date is in the
    future as of the time of execution.
    :return: a datetime object
    """

    assert isinstance(date_str, str), f"Invalid parameter type received {type(date_str)}. Expected string"
    for char in ['\n', ';', ' ', '.']:
        date_str = date_str.replace(char, '')

    # try to match the date string to a datetime object, with and without year
    for year_format in ['%d%B%Y', '%d%b%Y', '%B%d%Y', '%b%d%Y', '%d%B', '%d%b', '%B%d', '%b%d']:
        try:
            datetime_obj = datetime.strptime(date_str, year_format)
        except ValueError:
            continue

        now = datetime.now()
        if datetime_obj.year < 2000:
            # year was not specified in the date string. Assume it's the current year.
            datetime_obj = datetime_obj.replace(year=now.year)

        if now < datetime_obj and regress_future_dates:
            # datetime is in the future, but future date is not wanted. Return previous year.
            return datetime_obj.replace(year=now.year - 1)
        return datetime_obj

    # matching to datetime failed, both with and without year
    raise ValueError(f"Failed to convert this value to datetime: '{date_str}'")


def date_to_short_string(the_date: Union[datetime, str]) -> str:
    # todo: get rid of this function if possible
    """
    Given a datetime object or string, return an abbreviated string representation of it. Raise on failure
    :param the_date: a string or datetime representation of a date
    :return: an abbreviated string representation of the input
    """
    if isinstance(the_date, str):
        the_date = convert_string_to_datetime(the_date)
    # example output: '13 Jan' or '07 Mar'
    return the_date.strftime('%d %b')


def count_empty_contiguous_rows_within_range(sheet, start_row: int, end_row: int, cols_lst: List[int]) -> int:
    """
    Return an inclusive count of the contiguously empty rows between start and end rows, where all cells in each of
    those rows are empty, for all columns in the columns list.
    :param sheet: the Excel sheet
    :param start_row: the row at which to start counting
    :param end_row: the final row to check
    :param cols_lst: the columns in which to check for values
    :return: a count of the empty rows found
    """
    # todo: consider removing this. It's only used in 1 place so far
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


def find_row_of_cell_matching_datetime(sheet: openpyxl.workbook.workbook.Worksheet,
                                       datetime_target: datetime.date,
                                       date_column: int,
                                       raise_on_failure=False) -> int:
    """
    Returns row value of cell containing specified date, in specified column. Returns -1 if not found
    :param sheet: a valid sheet object in an xlsx file
    :param datetime_target: the datetime date to search for in the date_column
    :param date_column: the column in which to search for date
    :param raise_on_failure: whether to raise a RuntimeError or return -1 on failure to find matching date
    :return: row number or -1 or RuntimeError
    """
    datetime_target = datetime_target.replace(hour=0, minute=0, second=0, microsecond=0)

    # convert date_column == 1 into "A", for example.
    col_letter = chr(date_column + 64)

    # find date cell matching the "date" parameter in the given sheet
    # note that in xlsx files: headers and strings are str, dates are datetime objects, empty cells are NoneType
    for cell in sheet[col_letter]:
        val = cell.value

        if isinstance(val, datetime):
            #  This file is not used if RETRIEVAL_METHOD is set to "local" in params.py.
            if val == datetime_target:
                return cell.row

    if raise_on_failure:
        err_msg = f"Failed to find matching date cell in target sheet, column {col_letter}"
        raise RuntimeError(err_msg)
    return -1


def return_first_empty_bodyweight_row(sheet, date_column: int, bodyweight_column: int) -> int:
    """
    Search backwards from the row corresponding to today's date, in order to find the smallest row number, where:
     1) said row contains a date string in the date column, but no bodyweight in the bodyweights column,
     2) and where the row above has filled in date and bodyweight cells.
    We disregard empty rows, and return upon finding a row with lower index matching the above conditions.
    :param sheet: the Excel sheet
    :param date_column: the column in which date values are saved, e.g. 22/05/2021
    :param bodyweight_column: the column in which bodyweights are saved
    :return: an integer, representing a row number
    """

    today = datetime.now()
    todays_row = find_row_of_cell_matching_datetime(sheet, today, date_column)
    if sheet.cell(row=todays_row, column=bodyweight_column).value:
        raise ValueError(f"Today's bodyweight cell is already written to")

    first_occurrence = None
    for row in range(todays_row, 1, -1):
        # search backwards
        date_cell_value = sheet.cell(row=row, column=date_column).value
        bw_cell_value = sheet.cell(row=row, column=bodyweight_column).value
        row_has_date = isinstance(date_cell_value, datetime)
        row_has_bodyweight = isinstance(bw_cell_value, (str, float, int))

        if row_has_date and not row_has_bodyweight:
            first_occurrence = row
        if row_has_date and row_has_bodyweight:
            # we've reached the previously filled in row.
            if first_occurrence:
                return first_occurrence

    raise ValueError(f"Failed to find empty bodyweight cell.")


def str_contains_est_xx_mins_line(line) -> bool:
    """
    Returns true if the input string contains an expression matching some variation of "Est ? mins" or "Est 52 mins",
    which is the string that we use to identify workout notes.
    :param line: the string to evaluate
    :return: True / False
    """
    # This regex is fundamental to how the programs in this repo work, and cannot be changed without significant
    # consequences. Consequences:
    # 1) workout notes are identified in Google Keep differently
    # 2) workouts are written differently to the Excel file

    # "est", followed by 1-3 digits or "?" characters, followed by "min". All case-insensitive.
    est_xx_mins_reg = re.compile(r'(est \d(\d)?(\d)? min)|(est \? min)|(est \?\? min)|(est \?\?\? min)', re.IGNORECASE)
    return bool(re.search(est_xx_mins_reg, line))


def target_path_is_xslx(file_path: str) -> bool:
    filename, extension = os.path.splitext(file_path)
    return extension == '.xlsx'


def target_sheet_exists(excel_path: str, target_sheet_name: str) -> bool:
    """
    Return True if target sheet is found in Excel at path, else False.
    :param excel_path: a string path pointing to an Excel file
    :param target_sheet_name: a sheet name
    :return: True / False
    """
    wb = openpyxl.load_workbook(excel_path)
    return target_sheet_name in wb.sheetnames


def get_string_pct_similarity(str_1, str_2) -> int:
    float_num = SequenceMatcher(None, str_1, str_2).ratio()
    return int(float_num * 100)

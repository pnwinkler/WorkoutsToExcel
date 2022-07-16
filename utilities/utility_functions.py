import re
import os
import shutil
import getpass
import gkeepapi
import openpyxl
import GKeepToCalc.utilities.params as p

from datetime import datetime
from typing import Union, List


def backup_target_path() -> None:
	"""
	Backup the file at p.TARGET_PATH, unless it was already backed up earlier today.
	"""
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


def convert_string_to_datetime(date_str: str, regress_future_dates=True) -> Union[int, datetime]:
	"""
	Return the input string's datetime equivalent. If regress_future_dates, then subtract one year from the date that
	would be returned if that date is in the future at the time of execution.
	:param date_str: the string to convert
	:param regress_future_dates: if true, then subtract one year from the date to be returned, if that date is in the
	future as of the time of execution.
	:return:
	"""
	if not isinstance(date_str, str):
		raise ValueError(f"Invalid parameter type received {type(date_str)}")

	date_str = date_str.replace('\n', '').replace(';', '').replace(' ', '').replace('.', '')

	year_formats_to_try = ['%d%B%Y', '%d%b%Y', '%B%d%Y', '%b%d%Y']
	no_year_formats_to_try = ['%d%B', '%d%b', '%B%d', '%b%d']

	for year_format in year_formats_to_try:
		try:
			datetime_obj = datetime.strptime(date_str, year_format)
		except ValueError:
			continue

		now = datetime.now()
		if now < datetime_obj and regress_future_dates:
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

		if now < datetime_obj and regress_future_dates:
			# datetime is in the future, but future date is not wanted. Return previous year.
			return datetime_obj.replace(year=now.year - 1)
		return datetime_obj

	# matching to datetime failed, both with and without year
	raise ValueError(f"Failed to convert this string to datetime: '{date_str}'")


def count_empty_contiguous_rows_within_range(sheet, start_row, end_row, cols_lst: List[int]) -> int:
	"""
	Return an inclusive count of the contiguously empty rows between start and end rows, where all cells in those rows
	are empty, for all columns in the columns list.
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


def date_to_short_string(the_date: Union[datetime, str]) -> str:
	"""
	Given a datetime object or string, return an abbreviated string representation of it. Raise on failure
	:param the_date: a string or datetime representation of a date
	:return: an abbreviated string representation of the input
	"""
	if isinstance(the_date, str):
		the_date = convert_string_to_datetime(the_date)
	# example output: '13 Jan' or '07 Mar'
	return the_date.strftime('%d %b')


def return_note_datetime(note: gkeepapi.node.Note, raise_if_no_valid_date=False) -> datetime:
	"""
	Return a datetime object, extracted from the note's title, and subtracting a year if that note's day month
	combination has not yet passed this year. Raise on failure, if requested.
	:param note: the note object
	:param raise_if_no_valid_date: raise if there's no date in the note title that can be converted to datetime
	:return: a datetime object, representing a date such that the date is between 0 and (365 * 2 - 1) days in the past.
	"""
	assert isinstance(note, gkeepapi.node.Note), "return_raw_note_date did not receive a Note object"
	raw_date = str(note.title)
	date = None
	try:
		date = convert_string_to_datetime(raw_date)
	except ValueError as e:
		if raise_if_no_valid_date:
			raise ValueError(f"Cannot convert '{raw_date}' from note title, to date") from e
	return date


def find_row_of_cell_matching_datetime(sheet: openpyxl.workbook.workbook.Worksheet,
									   datetime_target: datetime,
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


def is_workout_note(note: gkeepapi.node.Note, raise_on_invalid_format=True) -> bool:
	"""
	Returns True if a Note object is identified as a workout note, else False
	:param note: a Keep Note object
	:param raise_on_invalid_format: whether to raise if there's an est XX mins line but no date
	:return: True / False
	"""
	is_workout = str_contains_est_xx_mins_line(note.text)
	if is_workout:
		if raise_on_invalid_format:
			try:
				convert_string_to_datetime(note.title)
			except ValueError as e:
				msg = f"The note with this title '{note.title}' contains an est XX mins line but no date could be " \
					  f"extracted from its title. This is an invalid combination."
				raise ValueError(msg) from e
	return is_workout


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


def login_and_return_keep_obj() -> gkeepapi.Keep:
	"""
	Log in to Google Keep and return a Keep object
	:return: a Google Keep client object
	"""
	username, password = None, None
	try:
		from GKeepToCalc.utilities.credentials import username, password
	except FileNotFoundError:
		print("You can save your username as an environment variable, which can save you from typing your username"
			  "each time (see utilities/credentials.py)")

	if not username:
		username = input('Google Keep username: ')
	if password is None:
		# getpass obscures the password as it's entered
		password = getpass.getpass('Google Keep password: ')

	print('Logging in...')
	keep = gkeepapi.Keep()
	keep.login(username, password)
	return keep


def retrieve_notes(keep: gkeepapi.Keep) -> List[gkeepapi.node.Note]:
	"""
	Given a keep object, return all of its not-trashed note objects
	:param keep: a keep object
	:return: a list of keep note objects
	"""
	assert isinstance(keep, gkeepapi.Keep), "Invalid object passed in to retrieve_notes function"
	print('Retrieving notes')
	notes = keep.find(trashed=False)
	if notes:
		return notes
	raise ValueError('No notes found. Incorrect username or password?')


def target_path_is_xslx(path: str) -> bool:
	"""
	Returns True if path points to a file with ".xlsx" extension, else False.
	:param path: the file's path
	:return: True / False
	"""
	filename, extension = os.path.splitext(path)
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

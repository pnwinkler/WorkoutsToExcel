import re
import openpyxl
import os
from datetime import datetime
from dateutil.parser import parse
from typing import List
import GKeepToCalc.utilities.params as p
import GKeepToCalc.utilities.utility_functions as uf

# months = [
#     'january', 'february', 'march', 'april',
#     'may', 'june', 'july', 'august', 'september',
#     'october', 'november', 'december'
# ]


def initial_checks() -> None:
    if not os.path.exists(p.SOURCE_PATH):
        raise FileNotFoundError('source path not found')
    if not is_date_given():
        raise ValueError('No date line found in source file')
    if not os.path.exists(p.TARGET_PATH):
        raise FileNotFoundError('target path not found')
    if uf.target_path_is_xslx():
        if not uf.targetsheet_exists():
            raise ValueError('Error: TARGET_SHEET not found at {}'.format(p.TARGET_PATH))
    else:
        RuntimeError('target file is not xslx. Keep2Calc is not intended for non-xlsx target files.')


def return_list_of_workouts_from_file(source=p.SOURCE_PATH) -> List[List[str]]:
    # reads lines from path, removing anything which isn't a workout
    # returns a list of workouts, where each "workout" is the unfiltered
    # list of all lines thought to be part of that workout note

    # a list of lists, containing all workouts, each saved as a list
    lines_to_write_matrix = []
    # days_data is a list of all lines in one workout
    days_data = []
    with open(source, 'r') as f:
        lines = f.readlines()

    start_appending = False
    for line in lines:
        # how we identify and copy workouts:
        # 1) start copying at a dateline. We append each line to days_data
        # 2) we append up to and including the next est xx mins line
        #   2ii) If we encounter another dateline before the est xx mins line,
        #   then we discard days_data (excepting that new dateline),
        #   as it did not match our workout format.
        #   Next loop, we then repeat from stage 2 onwards
        # 3) we append the complete workout in days_data to lines_to_write_matrix
        # 4) once all lines are read, we return lines_to_write_matrix

        if not start_appending:
            if is_dateline(line):
                # stage 1)
                start_appending = True
                days_data.append(line)
                continue
        else:
            if is_dateline(line):
                # stage 2ii)
                days_data = [line]
            else:
                # stage 2)
                days_data.append(line)
                if uf.is_est_xx_mins_line(line):
                    # stage 3)
                    start_appending = False
                    lines_to_write_matrix.append(days_data)
                    days_data = []

    return lines_to_write_matrix


def write_workouts_to_xlsx(parsed_data, backup=True):
    # writes to specified sheet in xlsx file at TARGET_PATH,
    # to the correct date cell.
    # Takes parsed_data, a list of tuples where tuple[0] is a workout's date
    # and tuple[1] the workout data for that day

    if backup:
        uf.backup_targetpath()

    wb = openpyxl.load_workbook(p.TARGET_PATH)
    sheet = wb[p.TARGET_SHEET]

    # any workouts that failed to write are added to this
    # later printed, to inform the user of workouts that need their attention
    # has not yet been necessary.
    NOT_WRITEABLE = []

    now = datetime.now()
    for tpl in parsed_data:
        # clean date line so that datetime can create datetime object
        # exercise_datetime will be used to determine which cell to enter data into
        # cleaning necessary because date line was processed by return_parsed_data()
        exercise_datetime = tpl[0]
        print_friendly_datetime = exercise_datetime[:2] + '-' + exercise_datetime[2:]

        # assume that workouts are for current year, unless that date is in the future
        exercise_datetime += str(now.year)
        exercise_datetime = uf.convert_ddmmyyyy_to_datetime(exercise_datetime)
        if exercise_datetime == -1:
            # we cannot continue without a valid date
            # Possible causes: UTF 8 stuff; unconverted data like "day 1"
            print('Error: write_workouts_to_xlsx did not receive appropriate datetime')
            exit()
        if now < exercise_datetime:
            # exercise would be in the future, so we assume it's from last year
            exercise_datetime = exercise_datetime.replace(year=now.year - 1)

        r = uf.find_row_of_datecell_given_datetime(sheet, exercise_datetime, p.DATE_COLUMN)
        if r == -1:
            print(f'Error: write_workouts_to_xlsx failed to write workout for date {print_friendly_datetime}')
            # add the date but not the hour, minute, second values
            # NOTE: this slice is not tested
            NOT_WRITEABLE.append(str(exercise_datetime)[:10])
            continue
        else:
            celldata_to_write = tpl[1]
            if not sheet.cell(row=r, column=p.WORKOUT_COLUMN).value:
                print(f'match FOUND. Writing {exercise_datetime} workout to cell in row {r}')
                sheet.cell(row=r, column=p.WORKOUT_COLUMN).value = celldata_to_write

            elif sheet.cell(row=r, column=p.WORKOUT_COLUMN).value == celldata_to_write:
                print(f"Skipping write for {exercise_datetime}, it's already written to row {r}")

            elif sheet.cell(row=r, column=p.WORKOUT_COLUMN).value != celldata_to_write:
                # package_description: replace this with a more helpful system sometime
                # if the user wants fuzzy matching, this is the place to implement it
                print(f'Skipping write for {exercise_datetime}. ', end='')
                print(f'A *different* value already exists at row {r}. ', end='')
                print('Perhaps it\'s just a different format or a one-character difference')
                print("INTENDED WRITE:\n", celldata_to_write)
                print("EXISTING VALUE:\n", sheet.cell(row=r, column=p.WORKOUT_COLUMN).value)
                print("Please verify that you do not have 2 workouts with the same date in Keep")
                print("Do not run KeepPruner before doing so.")

    wb.save(p.TARGET_PATH)

    if len(NOT_WRITEABLE) > 0:
        print('Workouts were not written for these dates:', end='\n\t')
        print(','.join(NOT_WRITEABLE))
        print('Suggest review of source data, as well as target file')
        print('When complete, please re-run the program with the --no-fetch parameter')
        exit()


def is_date_given():
    with open(p.SOURCE_PATH, 'r') as f:
        lines = f.readlines()

        for line in lines:
            if is_dateline(line):
                return True

        print('Error: dateline not given. '
              'Dates must be given as 3+ letter string with digit accompaniment\n'
              'e.g. (6 Nov, January 26, 08 May)\n'
              'Program exiting')
        return False


def is_dateline(line):
    # disregard comments
    if line.startswith("/") or line.startswith("("):
        return False

    if is_date(line):
        # line is in recognizable format
        return True

    # line not recognizable. Perhaps ', day 3' prevents it from being recognized as a date
    # or ", off day"
    else:
        if ',' in line:
            line = line[:line.index(',')]
        return is_date(line)


def is_date(string, fuzzy=False):
    # helper function for is_dateline()
    """
    # copied from Stackoverflow solution
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    try:
        # this is too liberal. For:
        # 'July 23, day 3'
        # it returns datetime.datetime(2003, 7, 23, 0, 0)
        parse(string, fuzzy=fuzzy)
        # return True

        # reject strings like "17"
        if len(string) < 4:
            return False

        # for our purposes, a string must contain digits
        # so we reject strings like "September" as being datelines
        # but accept "September 15" or "2 January"
        for c in string:
            if c.isdigit():
                return True
        return False

    except (ValueError, OverflowError):
        # phone numbers can result in overflow in parse() function
        return False


def return_parsed_data(clean_source=p.SOURCE_PATH):
    # from CLEAN source file, extracts workouts and parses them
    # (clean means that there's only workout data in there, nothing extraneous).
    # cleaning is done by return_list_of_workouts_from_file()
    # returns a list of tuples. One tuple is one workout.
    # in each tuple[0] is the date, which lets us know where to write
    # in each tuple[1] is a string containing a formatted workout
    # if you want to remove anything from the title, like ", day 2", this is the place

    # parsed_data contains all workouts
    parsed_data = []

    with open(clean_source, 'r') as f:
        lines = f.readlines()

    # account for user error: strip leading space before or after an exercise
    for i in range(len(lines)):
        lines[i] = lines[i].lstrip(' ').rstrip(' ')

    # convert from source format to storage format
    # replace ('+','\n'). Append ';'. Remove fluff like '4x7', '3 sets'
    # omit comment lines
    days_data = []
    for line in lines:
        # we want each exercise to start with a capital letter (for consistency) but capitalize is too clumsy.
        for ind, c in enumerate(line):
            if c.isalpha():
                # we don't capitalize the "x" in "3x25 jabs", for example
                if not re.search(r'\dx\d\d', line):
                    line = line[:ind] + line[ind].upper() + line[ind + 1:]
                    break

        if "home workout" in line.lower():
            # we log in the xlsx file only that it's a "Home workout: ", discarding other title details.
            # here are example lines that we might expect
            # "Home workout, upper body A:", "Home workout, upper body B:", "Home workout, lower body + abs:"
            days_data.append("Home workout: ")
            continue

        if "shadowboxing" in line.lower():
            days_data.append("Shadowboxing: ")
            continue

        # replace accidental double fullstops.
        # line = line.replace('..', '.')
        # user might add a semi-colon to an exercise line.
        line = line.replace(';', '.')
        # line = line.lstrip(' ')

        if line.startswith(('/', '(', '\n')):
            continue

        elif line.startswith('+'):
            a = line.replace('\n', '') + '; '
            a = a.replace('+ ', '')
            a = a.replace('+', '')
            days_data.append(strip_num_x_nums(a))

        else:
            a = line.replace('\n', '') + '; '
            days_data.append(strip_num_x_nums(a))

        if uf.is_est_xx_mins_line(line):
            # remove 'Est 67 mins;' semicolon
            days_data[-1] = days_data[-1].replace('; ', '')

            # change from '; Est 67 mins' to '. Est 67 mins'
            days_data[-2] = days_data[-2].replace('; ', '. ')

            # remove fluff from date line (aka the note's title)
            date_line = days_data[0]
            date_line = re.sub(re.compile(r', day \d'), '', date_line)
            date_line = re.sub(re.compile('(,)? off day'), '', date_line)
            date_line = date_line.replace(';', '').rstrip()

            # final cleanup
            # then append as tuple, where tpl[0] is the date, and tpl[1] the workout string
            string_workout = ''.join(days_data[1:]).replace('  ', ' ').replace(' .', '.').replace('..', '.')
            parsed_data.append((date_line, string_workout))
            days_data = []

    return parsed_data


def strip_num_x_nums(prelim_parse: str) -> str:
    # deprecated.
    # Instead, I recommend putting instructions on separate comment "/" lines, because it's more legible (and practical)
    # to separate instructions from exercise lines)

    # removes instructions, kilogram range, set and rep counts
    # regex to match: 4x7 , 3x5 , 5x6 min , 7x4+, 2x10-12 etc
    set_x_rep_reg = re.compile(r','
                               r'\s*'
                               r'\dx\d'
                               r'(\d)*'  # digits 'x' digit(s)
                               r'\s*'  # spaces, if present
                               r'(-)*'
                               r'(\d)*'  # max rep specified, eg 12 in 2x10-12
                               r'\+*'  # '+' if present
                               r'(min)*'  # 'min' if present
                               r'\s*',
                               flags=re.IGNORECASE)

    # regex to match: kilogram range comma and trailing space (e.g. '75-85kg, ')
    num_hyphen_num_sets_reg1 = re.compile(r'\d\d'
                                          r'(kg)*'
                                          r'-'
                                          r'\d\d'
                                          r'(\s)?'  # accounts for improper source format
                                          r'kg'
                                          r'(,)?'
                                          r'(\s)?',
                                          flags=re.IGNORECASE)

    # regex to match: exercise-set count, leading and trailing spaces. e.g. ' 3 sets '
    num_hyphen_num_sets_reg2 = re.compile(r'(,)?'
                                          r'(\s)*'  # leading space
                                          r'\d'  # digit count of sets
                                          r'(\s)?'
                                          r'set'
                                          r'(s)?'
                                          r'(\s)?',
                                          flags=re.IGNORECASE)

    parsed = prelim_parse
    # parse 1: remove 4x7 etc
    if set_x_rep_reg.search(parsed):
        parsed = re.sub(set_x_rep_reg, '', parsed)

    # parse 2: remove kg range
    if num_hyphen_num_sets_reg1.search(parsed):
        parsed = re.sub(num_hyphen_num_sets_reg1, '', parsed)

    # parse 3: remove exercise-set-instructions
    if num_hyphen_num_sets_reg2.search(parsed):
        parsed = re.sub(num_hyphen_num_sets_reg2, '', parsed)

    return parsed


def line_is_comment(line):
    # comments exclusively begin with '/' or '('
    if line.startswith('/'):
        return True
    if line.startswith('('):
        return True
    return False

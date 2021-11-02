import re
import openpyxl
import os
from datetime import datetime
from dateutil.parser import parse
from typing import List
import gkeepapi.node
import GKeepToCalc.utilities.params as p
import GKeepToCalc.utilities.utility_functions as uf


def initial_checks(notes_lst: List[gkeepapi.node.Note]) -> None:
    # oddly, a the list of notes is a list of Notes, but each Note is a List object
    for note in notes_lst:
        if not isinstance(note, gkeepapi.node.List) and not isinstance(note, gkeepapi.node.Node):
            raise ValueError("Invalid type found in notes list. Expected type gkeepapi objects, but found"
                             f"{type(note)}")
    if not os.path.exists(p.TARGET_PATH):
        raise FileNotFoundError('target path not found')
    if uf.target_path_is_xslx(p.TARGET_PATH):
        if not uf.targetsheet_exists(p.TARGET_PATH, p.TARGET_SHEET):
            raise ValueError(f'Error: TARGET_SHEET "{p.TARGET_SHEET}" not found at {p.TARGET_PATH}')
    else:
        RuntimeError('target file is not xslx. Keep2Calc is not intended for non-xlsx target files.')


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
        # cleaning necessary because date line was processed by parse_workout_notes()
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
                print(
                    "Please verify that you do not have 2 workouts with the same date in Keep. This may cause malfunctions")
                print("Do not run KeepPruner before doing so, as that would trash your workouts.")

    wb.save(p.TARGET_PATH)

    if len(NOT_WRITEABLE) > 0:
        print('Workouts were not written for these dates:', end='\n\t')
        print(','.join(NOT_WRITEABLE))
        print('Suggest review of source data, as well as target file')
        print('When complete, please re-run the program with the --no-fetch parameter')
        exit()


def is_date_given(path):
    with open(path, 'r') as f:
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


def capitalize_selectively(line) -> str:
    for ind, c in enumerate(line):
        if c.isalpha():
            # we don't capitalize the "x" in "3x25 jabs", for example
            if not re.search(r'\dx\d\d', line):
                return line[:ind] + line[ind].upper() + line[ind + 1:]
    return line


def line_is_comment(line) -> bool:
    # comments exclusively begin with '/' or '('
    if line.startswith('/'):
        return True
    if line.startswith('('):
        return True
    return False


def parse_workout_notes(workout_notes: List[gkeepapi.node.Note]) -> List[tuple]:
    # given a list of workout notes, extract workouts and parse them
    # returns a list of tuples, each representing one workout.
    # in each tuple[0] is the date, which lets us know where to write
    # in each tuple[1] is a string containing a formatted workout
    for note in workout_notes:
        assert uf.est_xx_mins_line_in_note_text(note.text), \
            "parse_workout_notes() received a note without an est xx mins" \
            "line. This function accepts workout notes only, which are " \
            "all expected to have an est xx mins line"
        assert is_date(note.title), "parse_workout_notes() received a note without a date in its title. It cannot work " \
                                    "without this."

    parsed_data = []
    for note in workout_notes:
        # remove fluff from note title
        parsed_title = re.sub(re.compile(r', day \d'), '', note.title)
        parsed_title = re.sub(re.compile('(,)? off day'), '', parsed_title)

        # strip lines, and drop empty lines and comment lines.
        note.text = [line.strip() for line in note.text.split('\n')
                     if line
                     and not (line_is_comment(line) or line.startswith('\n'))]

        one_workouts_lines = []
        for ind, line in enumerate(note.text):
            parsed_line = line
            # capitalize each letter, except under certain conditions
            parsed_line = capitalize_selectively(parsed_line)

            # fix common user entry errors.
            parsed_line = parsed_line.replace(';', '.')
            parsed_line = parsed_line.replace('..', '.')
            parsed_line = parsed_line.replace(' .', '.')
            parsed_line = parsed_line.replace(',,', '.')

            # in every line, we append a semi-colon, as the separator between exercises
            parsed_line = parsed_line.replace('\n', '; ')

            # the "+" symbol indicates an exercise line. We don't save it.
            parsed_line = parsed_line.replace('+ ', '')
            parsed_line = parsed_line.replace('+', '')

            # hard-coded replacement strings. This is personal preference.
            if "home workout" in line.lower():
                # in such cases, we deliberately discard title details.
                # The following lines, for example, would be replaced by the string below
                # "Home workout, upper body A:", "Home workout, upper body B:", "Home workout, lower body + abs:"
                parsed_line = "Home workout: "
            if "shadowboxing" in line.lower():
                parsed_line = "Shadowboxing: "

            parsed_line = strip_num_x_nums(parsed_line)
            # add that cleaned line to the workout's lines
            one_workouts_lines.append(parsed_line)

        # append the title and formatted workout contents.
        exercises_str = '; '.join(one_workouts_lines[:-1])
        est_xx_mins_str = one_workouts_lines[-1]
        final_workout_text = exercises_str + ". " + est_xx_mins_str #+ "."
        parsed_data.append((parsed_title, final_workout_text))

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

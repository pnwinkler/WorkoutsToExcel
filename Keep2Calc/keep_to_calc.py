import re
import openpyxl
import os
from datetime import datetime
from dateutil.parser import parse
from dataclasses import dataclass
from typing import Dict, List, Union, Tuple
import gkeepapi.node
import GKeepToCalc.utilities.params as p
import GKeepToCalc.utilities.utility_functions as uf

# todo: add option to have year in note title, and to use that if provided?
# todo: add tests. Make it clearer what each of these functions does.


@dataclass
class ParsedWorkout:
    # this will hold partially processed data that isn't ready to write yet (it still needs a target row).
    title_datetime: datetime
    data: str

    def __repr__(self):
        return f"{self.title_datetime}: {self.data}"

@dataclass
class DataToWrite(ParsedWorkout):
    # this will hold fully processed data that's validated and ready to write
    target_row: int


def initial_checks(notes_lst: List[gkeepapi.node.Note]) -> None:
    # oddly, the list of notes is a list of Notes, but each Note is a List object
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


def convert_workout_notes_to_datetime(workout_notes: List[gkeepapi.node.Note], disallow_future_dates=False) \
        -> Dict[datetime, str]:
    # given a list of workout_notes, load each into a dictionary, where every note's title is a datetime object.
    # Raise if unable to convert any title to datetime. Workout note titles will be like
    # "26 January" or maybe "02 March 2022"

    workouts_dict = dict()
    for note in workout_notes:
        # remove fluff from note title
        parsed_title = re.sub(re.compile(r', day \d'), '', note.title)
        parsed_title = re.sub(re.compile('(,)? off day'), '', parsed_title)

        assert is_date(note.title), "convert_workout_notes_to_datetime() received a note without a date in its " \
                                    "title. It cannot work with notes that do not contain a date in their title. " \
                                    f"Please add a title to the note. Tip: it was last edited " \
                                    f"{note.timestamps.edited}, and it contains this text\n{note.text}"

        # if not parsed_title.strip()[:-4].isdigit():
        #     # crude heuristic. If the last 4 digits are not digits, then assume no year was provided
        #     parsed_title +=

        if len(parsed_title.split()) == 2:
            # hacky. Add a phony year so that the date can be recognized by the function below, and it won't use 1900.
            parsed_title += str(datetime.now().year)

        datetime_title = uf.convert_string_to_datetime(date_str=parsed_title,
                                                       verbose=False,
                                                       disallow_future_dates=disallow_future_dates,
                                                       raise_on_failure=True,
                                                       err_msg=f"Failed to convert the following workout note "
                                                                 f"title to datetime object {note.title}")

        workouts_dict[datetime_title] = note.text

    return workouts_dict


def parse_workout_notes(workout_notes: List[gkeepapi.node.Note]) -> List[ParsedWorkout]:
    # given a list of workout Note objects, parses the workout within each Note
    # returns a list of ParsedWorkout objects, each representing one workout
    # the data of each ParsedWorkout will be a partially processed workout

    for note in workout_notes:
        assert uf.est_xx_mins_line_in_note_text(note.text), \
            "parse_workout_notes() received a note without an est xx mins" \
            "line. This function accepts workout notes only, which are " \
            "all expected to have an est xx mins line"

    # receive a dictionary in which every note's title was converted to datetime
    workout_notes_dict = convert_workout_notes_to_datetime(workout_notes, disallow_future_dates=True)

    parsed_data_lst = []
    for datetime_title, workout_text in workout_notes_dict.items():
        # strip lines, and drop empty lines and comment lines.
        workout_text = [line.strip() for line in workout_text.split('\n')
                        if line
                        and not (line_is_comment(line) or line.startswith('\n'))]

        single_workout_lines = []
        for line in workout_text:
            # capitalize each letter, except under certain conditions
            parsed_line = capitalize_selectively(line)

            # clean-up, and fix common user entry errors.
            parsed_line = parsed_line.replace(';', '.')
            parsed_line = parsed_line.replace('..', '.')
            parsed_line = parsed_line.replace(' .', '.')
            parsed_line = parsed_line.replace(',,', '.')
            parsed_line = parsed_line.replace('\n', '')

            # the "+" symbol is used at the beginning of the line to denote an "extra" exercise. We don't save the "+".
            parsed_line = parsed_line.replace('+ ', '')
            parsed_line = parsed_line.replace('+', '')

            # hard-coded replacement strings. This is personal preference.
            if "home workout" in line.lower():
                # The following lines, for example, would be replaced by the string below
                # "Home workout, upper body A:", "Home workout, upper body B:", "Home workout, lower body + abs:"
                parsed_line = "Home workout: "
            if "shadowboxing" in line.lower():
                parsed_line = "Shadowboxing: "

            # this strips certain instructions from the line.
            parsed_line = strip_num_x_nums(parsed_line)

            # add that cleaned line to the workout's lines
            single_workout_lines.append(parsed_line)

        # semicolon-separate each exercise
        exercises_str = '; '.join(single_workout_lines)

        # replace the final semi-colon with a full stop.
        exercises_str, est_xx_mins_line = exercises_str.rsplit('; ', 1)
        complete_workout_text = exercises_str + ". " + est_xx_mins_line

        # add the complete and formatted workout to parsed_data
        parsed_data_lst.append(ParsedWorkout(title_datetime=datetime_title, data=complete_workout_text))

    return parsed_data_lst


def return_print_friendly_datetime_string(date_obj: datetime) -> str:
    # like "02 Jan"
    short_str = date_obj.strftime("%d %b")
    return short_str


def pair_workouts_with_rows(parsed_workouts: List[ParsedWorkout]) -> List[DataToWrite]:
    # given a list of parsed workouts, pair each with the row in the target file, whose cell contains the same day's
    # datetime. Then return that info as a list of DataToWrite objects

    wb = openpyxl.load_workbook(p.TARGET_PATH)
    sheet = wb[p.TARGET_SHEET]

    # any workouts for which we were unable to find a matching date cell are added to this list
    # later printed, to inform the user of workouts that need their attention
    failed_to_find_date_cell = []
    value_already_written = []
    target_cell_contains_clashing_info = []
    data_to_write: List[DataToWrite] = []

    for parsed_workout in parsed_workouts:
        data = parsed_workout.data
        ex_datetime = parsed_workout.title_datetime

        row = uf.find_row_of_datecell_given_datetime(sheet, ex_datetime, p.DATE_COLUMN, raise_on_failure=False)
        if row == -1:
            failed_to_find_date_cell.append(parsed_workout)
            continue

        celldata_to_write = data
        target_cell_data = sheet.cell(row=row, column=p.WORKOUT_COLUMN).value

        if not target_cell_data:
            # success. Match found
            data_to_write.append(DataToWrite(title_datetime=ex_datetime, data=data, target_row=row))

        elif target_cell_data == celldata_to_write:
            value_already_written.append(parsed_workout)

        elif target_cell_data != celldata_to_write:
            # problem: a different value already exists in the target cell. That said, it may be almost identical.
            target_cell_contains_clashing_info.append((parsed_workout, target_cell_data))

    if len(failed_to_find_date_cell) != 0:
        raise AssertionError(f"Failed to find row matches for the following {len(failed_to_find_date_cell)} "
                             f"workouts. Please verify that the matching date value exists in the target Excel "
                             f"file, in the correct place.{failed_to_find_date_cell}")

    # alert user to different scenarios, and request user action if required
    if len(value_already_written) == len(parsed_workouts):
        print("No workouts to write. Program exiting")
        exit()

    assert len(data_to_write) > 0, f"There are no workouts to be written"

    if len(target_cell_contains_clashing_info) > 0:
        print(f"The following {len(target_cell_contains_clashing_info)} workouts already have *different* values "
              f"written to their target cells. Please review")
        for parsed_workout, target_cell_data in target_cell_contains_clashing_info:
            neat_datetime= parsed_workout.title_datetime.strftime('%Y-%m-%d')
            print(f"{neat_datetime} INTENDED WRITE:\t{parsed_workout.data}")
            print(f"{neat_datetime} EXISTING VALUE:\t{target_cell_data}")
        print("\nIf these workouts are only slightly different, you may be OK with that. If they're significantly "
              "different, then please reconcile them, and verify that you do not have 2 workouts with the same date "
              "in Keep, as this may cause malfunctions\n"
              "Do not run KeepPruner before doing so, as its purpose is to trash your Google Keep workouts.\n")
        inp = input("Do you wish to proceed regardless? (y/N) ")
        print()
        if inp.lower().strip() != "y":
            print("User chose not to continue")
            exit()

    print(f"{len(data_to_write)} workouts can be written to target cells. {len(value_already_written)} workouts "
          f"are already written to target cells")
    assert len(set([pd.target_row for pd in data_to_write])) == len(data_to_write), \
        "Error: multiple workouts are scheduled to be written to the same cell"
    return data_to_write


def write_workouts_to_xlsx(data_to_write: List[DataToWrite], backup=True):
    # writes to specified sheet in xlsx file at TARGET_PATH, to the correct date cell.
    # Takes data_to_write, a list of DataToWrite objects. Those are *already validated* objects
    # does only minimal validation on its own

    assert all([isinstance(obj, DataToWrite) for obj in data_to_write])
    assert all([obj.target_row > 0 for obj in data_to_write]), "Invalid row for write object in function " \
                                                               "write_workouts_to_xlsx(...)"

    if backup:
        uf.backup_target_path()

    wb = openpyxl.load_workbook(p.TARGET_PATH)
    sheet = wb[p.TARGET_SHEET]

    print(f"Writing {len(data_to_write)} workouts to target file.")
    for packet in data_to_write:
        target_cell = sheet.cell(row=packet.target_row, column=p.WORKOUT_COLUMN)
        assert not target_cell.value, "Programming error. Target cell already has value written. No changes made"
        target_cell.value = packet.data

    wb.save(p.TARGET_PATH)


def is_dateline(line: str):
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


def is_date(string, fuzzy: bool=False):
    # helper function for is_dateline()
    """
    # copied from Stackoverflow solution
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    try:
        # this is too liberal. For: 'July 23, day 3', it returns datetime.datetime(2003, 7, 23, 0, 0)
        parse(string, fuzzy=fuzzy)

    except (ValueError, OverflowError):
        # phone numbers can result in overflow in parse() function
        return False

    # reject strings like "17"
    if len(string) < 4:
        return False

    # for our purposes, a string must contain digits
    # therefore, we reject strings like "September" as datelines,
    # but accept strings containing digits, such as "September 15" or "2 January"
    for c in string:
        if c.isdigit():
            return True
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


def strip_num_x_nums(prelim_parse: str) -> str:
    # Instead, I recommend putting instructions on separate comment "/" lines, because it's more legible (and practical)
    # to separate instructions from exercise lines)

    # example inputs (left) and outputs (right)
    #  "Squat 4x7 70kg:" -> "Squat 70kg:"
    #  "Deadlift 2x3+ 70kg:" -> "Deadlift 70kg:"
    #  "Ohp 4x3 min 70-80kg:" -> "Ohp 70kg:"
    # "Triceps, 1 set" -> "Triceps"
    # "Superset lat stretches, 2 sets" -> "Triceps"

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

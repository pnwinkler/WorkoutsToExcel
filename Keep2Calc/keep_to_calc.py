import re
import openpyxl
import os
from datetime import datetime
import utilities.params as p
import utilities.utility_functions as uf

months = [
    'january', 'february', 'march', 'april',
    'may', 'june', 'july', 'august', 'september',
    'october', 'november', 'december'
]


def initial_checks():
    if not os.path.exists(p.source_path):
        print('source path not found')
        exit()
    if not is_date_given():
        print('No date line found in source file')
        exit()
    if not os.path.exists(p.target_path):
        print('target path not found')
        exit()
    if uf.target_is_xslx():
        if not uf.targetsheet_exists():
            print('Error: target_sheet not found at {}'.format(p.target_path))
            exit()
    else:
        print('target file is not xslx. Keep2Calc is not intended for non-xlsx target files.')
        exit()


def return_clean_data_matrix(source=p.source_path):
    # copies data from source_path
    # removes anything which isn't a workout
    # appends workouts as one list each (consisting of however many lines)
    # to a matrix, then returns that

    # a list of lists, containing all workouts, each saved as a list
    lines_to_write_matrix = []
    # days_data is a list of all lines in one workout
    days_data = []
    with open(source, 'r') as f:
        lines = f.readlines()

    start_appending = False
    for line in lines:
        # in order to prevent noise (==non-workout data) in source file from becoming
        # part of the returned matrix (of lines to write), we:
        # 1) start copying at a dateline. We append each line to days_data
        # 2) we append up to and including the next est xx mins line
        #   2ii) If we encounter another dateline before the est xx mins line,
        #   then we discard days_data (excepting that new dateline),
        #   as it did not match our workout format.
        #   Next loop, we then repeat from stage 2 onwards
        # 3) we append the complete workout in days_data to lines_to_write_matrix
        # 4) once all lines are read, we return lines_to_write_matrix

        # REMINDER: if you get weird results, like multiple non-workout notes being
        # erroneously recognized as a workout make sure that you do not have 2
        # workout entries for that date, e.g. 23 July 2019 and 23 July 2020.
        # In my case the 3 notes below were concatenated into one line.
        #
        # 11 August
        # 2/10 left knee pain
        # The food medic
        #
        # Fire PIN + engineer's cellphone number
        # PIN \d\d\d\d
        # Name tel-number
        #
        # 23 July, off day
        # Treadmill (...)
        # 3 sets neck extensions, ...
        # Est ?? mins

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
    # writes to specified sheet in xlsx file at target_path,
    # to the correct date cell.
    # Takes parsed_data, a list of tuples where tuple[0] is a workout's date
    # and tuple[1] the workout data for that day

    if backup:
        uf.backup_targetpath()

    wb = openpyxl.load_workbook(p.target_path)
    sheet = wb[p.target_sheet]

    # any workouts that failed to write are added to this
    # later printed, to inform the user of workouts that need their attention
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

        r = uf.find_xlsx_datecell(sheet, exercise_datetime, p.date_column)
        if r == -1:
            print(f'Error: write_workouts_to_xlsx failed to write workout for date {print_friendly_datetime}')
            # add the date but not the hour, minute, second values
            # NOTE: this slice is not tested
            NOT_WRITEABLE.append(str(exercise_datetime)[:10])
            continue
        else:
            celldata_to_write = tpl[1]
            if not sheet.cell(row=r, column=p.workout_column).value:
                print(f'match FOUND. Writing {exercise_datetime} workout to cell in row {r}')
                sheet.cell(row=r, column=p.workout_column).value = celldata_to_write

            elif sheet.cell(row=r, column=p.workout_column).value == celldata_to_write:
                print(f"Skipping write for {exercise_datetime}, it's already written to row {r}")

            elif sheet.cell(row=r, column=p.workout_column).value != celldata_to_write:
                # package_description: replace this with a more helpful system sometime
                # if the user wants fuzzy matching, this is the place to implement it
                print(f'Skipping write for {exercise_datetime}. ', end='')
                print(f'A *different* value already exists at row {r}. ', end='')
                print('Perhaps it\'s just a different format or a one-character difference')
                print("INTENDED WRITE:\n", celldata_to_write)
                print("EXISTING VALUE:\n", sheet.cell(row=r, column=p.workout_column).value)
                print("Please verify that you do not have 2 workouts with the same date in Keep")
                print("Do not run KeepPruner before doing so.")

    wb.save(p.target_path)

    if len(NOT_WRITEABLE) > 0:
        print('Workouts were not written for these dates:', end='\n\t')
        print(','.join(NOT_WRITEABLE))
        print('Suggest review of source data, as well as target file')
        print('When complete, please re-run the program with the --no-fetch parameter')
        exit()


def is_date_given():
    with open(p.source_path, 'r') as f:
        lines = f.readlines()

        for line in lines:
            if is_dateline(line):
                return True

        print('Error: dateline not given. '
              'Dates must be given as 3+ letter string with digit accompaniment\n'
              'e.g. (6 Nov, January 26, 08 May)\n'
              'Program exiting')
        return False


def is_date(string, fuzzy=False):
    from dateutil.parser import parse
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

    except ValueError:
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
        # day_x_reg = re.compile(r'(,? day \d)|(,? off day)')
        # line = re.sub(day_x_reg, '', line)
        return is_date(line)


def return_parsed_data(clean_source=p.source_path):
    # from CLEAN source file, extracts workouts and parses them
    # (clean means that there's only workout data in there, nothing extraneous).
    # cleaning is done by Keep2Calc.retrieve_data_from_gkeep
    # returns parsed_data , a list of tuples
    # in each tuple[0] is the date, which lets us know where to write
    # in each tuple[1] is a string containing a formatted workout
    # if you want to remove anything from the title, like ", day 2", this is the place

    # parsed_data contains all workouts
    parsed_data = []

    with open(clean_source, 'r') as f:
        lines = f.readlines()

    # account for user error: strip leading space before an exercise
    for i in range(len(lines)):
        lines[i] = lines[i].lstrip(' ')

    # convert from source format to storage format
    # replace ('+','\n'). Append ';'. Remove fluff like '4x7', '3 sets'
    # omit comment lines
    days_data = []
    for line in lines:
        # we want each exercise to start with a capital letter
        # but capitalize is too clumsy.
        # It converts "EZ bar to "ez bar", "RC rotations" to "Rc rotations", "+ Wide grip" to "+ wide grip"
        # so we do it manually
        # The reason we need this at all is that home workouts are inconsistent in their capitalization
        # but gym workouts aren't. They should be consistent - each exercise capitalized.
        for ind, c in enumerate(line):
            if c.isalpha():
                line = line[:ind] + line[ind].upper() + line[ind + 1:]
                break

        if "home workout" in line.lower():
            # these leading lines help me in Keep, but clutter the xlsx file, so we do not add them to xlsx
            # "Home workout, upper body A:", "Home workout, upper body B:", "Home workout, lower body + abs:"
            days_data.append("Home workout: ")
            continue

        # non-conventional workouts, like "Some arm and shoulder work.\nEst ?? mins"
        # can result in double full stops.
        line = line.replace('..', '.')
        # user might add a semi-colon to an exercise line.
        line = line.replace(';', '.')
        # gym workout exercises are always capitalized, but home workouts may not be
        # we want consistency across workout types, so each exercise is capitalized.
        if len(line) > 3 and line.startswith(' '):
            # account for user error in data entry
            line = line.lstrip(' ')

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

            # clean date line, then add a tuple of (date, workout string)
            # largely historical. Was intended for datelines like "01 Jan, day 2"
            # where day 2 would be the 2nd workout of the week
            days_data[0] = re.sub(re.compile(r', day \d'), '', days_data[0])
            days_data[0] = re.sub(re.compile('(,)? off day'), '', days_data[0])
            days_data[0] = days_data[0].replace(';', '')

            # remove a trailing space from date
            days_data[0] = days_data[0][:-1]

            # account for user error in workout entry
            # (accidental double spaces do happen)
            # then append as tuple, where tpl[0] is the date, and tpl[1] the workout string
            parsed_data.append(
                (days_data[0], ''.join(days_data[1:]).replace('  ', ' ').replace(' .', '.').replace('..', '.')))
            days_data = []

    return parsed_data


def strip_num_x_nums(prelim_parse: str) -> str:
    # called by return_parsed_data(...) on each not-empty line in source workout.
    # removes instructions, kilogram range, set and rep counts
    # mostly legacy. I recommend putting instructions on separate comment "/" lines
    # however, another user may prefer a different format, as permitted by this function.

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


def is_commentline(line):
    # comments exclusively begin with '/' or '('
    # examples include '/Exhausting' , '(75kg:8,8,8 / 8,8,7)' , '/4x8 is a grinder'
    # intentionally doesn't catch newlines, because they are handled differently
    if line.startswith('/'):
        return True
    if line.startswith('('):
        return True
    return False


# if __name__ == '__main__':
#     initial_checks()
#     main()


# def write_clean_data(clean_write_path, clean_data_matrix):
#     # can't write a list, so we convert clean_data_matrix to a string
#     # this was intended for testing writes to txt file. May no longer have use
#     mega_string = ''
#     for lst in clean_data_matrix:
#         mega_string += '\n' + ''.join(lst)
#
#     with open(clean_write_path, 'w') as f:
#         f.write(mega_string)


'''
def delete_old_data():
    # deprecated
    # removes one workout from source_path
    # if source_path is small enough, deletes the file

    with open(p.source_path, 'r') as f:
        read_lines = f.readlines()

        # the index up to which everything is deleted
        deletion_index = ''

        # set deletion_index to that of last_line_workout (and all subsequent comments or newlines)
        for index, ln in enumerate(read_lines):
            if uf.is_est_xx_mins_line(ln):
                try:
                    deletion_index = index + 1
                except IndexError:
                    deletion_index = index

                try:
                    for i in range(deletion_index, deletion_index + 5):
                        if read_lines[i] == '\n' or is_commentline(read_lines[i]):
                            deletion_index = i
                        if is_dateline(read_lines[i]):
                            break
                except IndexError:
                    pass
                break

    # overwrite file
    lines_after_deletion_index = ''.join(read_lines[deletion_index:])
    with open(p.source_path, 'w+') as f:
        f.write(lines_after_deletion_index)

    # If less than 150 bytes, delete source_path
    if os.path.getsize(p.source_path) < 150:
        os.remove(p.source_path)
    else:
        pass
'''

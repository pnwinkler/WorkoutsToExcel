# retrieves bodyweights from Google Keep,
# then writes them to the correct date cell
# in the file specified by utilities.params.target_path
# does intelligent stuff too, like alert the user to missing entries, etc
# consider creating a version for use by crontab
# REMEMBER to change utilities.params whenever necessary.

import openpyxl
import re
from datetime import datetime
import utilities.params as p
import utilities.utility_functions as uf

bw_reg = re.compile(r'(\d{2,3}\.\d\s?,)+'
                    r'|(\d{2,3}\s?,)+'
                    r'|(\?{1,3}\s?,)+')


def main():
    if not uf.target_is_xslx():
        raise ValueError("Target path specified in params.py does not point to xlsx file")
    if not uf.targetsheet_exists():
        raise ValueError("Target xlsx does not contain sheet specified in params.py")

    keep = uf.login_and_return_keep_obj()
    notes = uf.retrieve_notes(keep)
    bw_note = find_bodyweights_note(notes)
    # this timestamp lets us know whether we should expect a bodyweight entry for today
    bw_edit_timestamp = return_bodyweights_note_edit_timestamp(bw_note)
    bodyweights_lst = return_bodyweights_lst(bw_note)

    wb = openpyxl.load_workbook(p.target_path)
    sheet = wb[p.target_sheet]

    # return range of rows requiring writes
    row_range_tpl = return_bw_rows_requiring_write(sheet, bw_edit_timestamp)
    # print(f'DEBUG: row_range_tpl={row_range_tpl}')
    # print(f'DEBUG: bodyweights_lst={bodyweights_lst}')

    # confirm that the length of that range matches the number of bodyweights found in the Keep note
    if do_bodyweights_fill_all_vacancies(bodyweights_lst, row_range_tpl):
        uf.backup_targetpath()
        print("Writing bodyweights to file")
        write_to_file(wb, sheet, bodyweights_lst, row_range_tpl[0])
    else:
        # error messages already handled in condition function above
        exit()

    trash_original_and_replace(keep, bw_note)
    print("Finished!")


def trash_original_and_replace(keep, bw_note):
    # Trash original bodyweight note, and replace with a new one-value bodyweights note
    # items in trash remain available for 7 days.
    # whereas changes to bw_note would be irreversible
    # that's why we create a new note this way.
    new_note_value = return_bodyweights_lst(bw_note)[-1] + ", "
    keep.createNote('', new_note_value)
    bw_note.trash()
    keep.sync()
    # print("Synchronizing")
    # import time
    # time.sleep(2)


def find_bodyweights_note(notes):
    """
    Within "notes", find the bodyweights note and return it
    :param notes: the Keep notes object (which contains all notes)
    :return: the note containing bodyweights
    """
    # we expect bodyweight note's format to resemble formats like these 3 below:
    # 83.2, 83, 83.4,
    # 101,
    # 100.4, 100.9, 99.8,
    # i.e. 2-3 digits with optional decimal place, followed by a comma
    # spaces are optional. Commas are not. Each number must be followed by one comma
    for gnote in notes:
        # match either title or body. It's user preference where the weights will be
        for x in [gnote.title, gnote.text]:
            if not x.replace(",", "").replace(" ", "").replace(".", "").replace("?", "").isdigit():
                continue
            else:
                # by default, trashed notes are also searched.
                if gnote.timestamps.trashed is not None:
                    return gnote

    raise ValueError("No matching note found. "
                     "1) Does your bodyweight note exist? "
                     "2) Is it in a valid format, with more than 1 entry? "
                     "3) Does it contain only numbers, spaces, commas and full stops?")


def return_bodyweights_note_edit_timestamp(bw_note):
    """
    :param bw_note: the note containing bodyweights
    :return: datetime object in form '%Y-%m-%dT%H:%M:%S.%fZ
    example return value "2020-07-06 11:20:44.428000"
    """
    return bw_note.timestamps.edited


def return_bodyweights_lst(bw_note):
    bodyweights = []
    for x in [bw_note.title, bw_note.text]:
        if len(re.findall(bw_reg, x)) > 0:
            if len(bodyweights) < 1:
                bodyweights = ["".join(m) for m in re.findall(bw_reg, x)]
                bodyweights = [t[:-1] for t in bodyweights]
                # This changes findall's output from this kind:
                # [('', '81,'), ('', '85,'), ('', '102,'), ('102.1,', '')]
                # to this kind
                # ['81', '85', '102', '102.1']
            else:
                print("ERROR: Bodyweights found in both title and text of note")
                print("Please tidy up note, such that *either* the note's title *or*", end=' ')
                print("the note's text contain ALL of the bodyweights, and the counterpart is empty")
                exit()

    if len(bodyweights) > 1:
        return bodyweights

    else:
        print(f"Debug: Note.title='{bw_note.title}'; Note.text='{bw_note.text}'")
        print("INFO: only 1 bodyweight found in Keep note. There is nothing new to write")
        print("exiting")
        exit()


def return_bw_rows_requiring_write(sheet, bw_edit_timestamp):
    """
    Return which rows should contain bodyweights but don't (according to the note's edit timestamp)
    :param sheet: sheet in xlsx file containing bodyweights and dates
    :param bw_edit_timestamp: datetime object in form '%Y-%m-%dT%H:%M:%S.%fZ
    :return: tuple of length 2, containing start and end rows
    """
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    # for mysterious reasons, datetime.today() doesn't actually get TODAY, it gets RIGHT NOW.
    # so using .now() or .today() is a moot distinction. The .replace is needed regardless

    if bw_edit_timestamp < today:
        print("- You have not edited your bodyweights note today. -")
        print("- Therefore, no weight will be written for today (you forgot to log it) -")
        print("- Suggested action: average yesterday's and tomorrow's bodyweights, tomorrow. -")
        print("(the program will now run as normal)")

    # descend bodyweight column,
    # counting empty cells that neighbour a date cell
    # until date > bw_edit_timestamp.
    # we assume that every date is intended to have an accompanying bodyweight!
    start = None
    count_unwritten_cells = 0
    for t in range(1, 1000000):
        # some rows in this column are strings
        if isinstance(sheet.cell(row=t, column=p.date_column).value, datetime):
            if sheet.cell(row=t, column=p.date_column).value > bw_edit_timestamp:
                return start, start + count_unwritten_cells
        if sheet.cell(row=t, column=p.bodyweight_column).value is None:
            if isinstance(sheet.cell(row=t, column=p.date_column).value, datetime):
                # empty bodyweight cell found next to a date cell.
                if not start:
                    start = t
                else:
                    count_unwritten_cells += 1


def do_bodyweights_fill_all_vacancies(bodyweights_lst, row_range):
    """
    :param bodyweights_lst: list of bodyweights in such a format: ['81', '85', '102', '102.1']
    :param row_range: tuple containing number of first and last rows lacking bodyweights
    :return: True if the number of provided bodyweights equals the number of absent bodyweights. Else False.
    """
    # informs user if values are missing or too numerous
    # relative to the vacancies present in the xlsx file

    # number of empty cells. 1+ makes it inclusive
    count_required = 1 + row_range[1] - row_range[0]
    # number of provided bodyweights. Skip first value
    count_provided = len(bodyweights_lst) - 1

    if count_provided < count_required:
        print(f"Too few values provided. Needed {count_required}, provided with {count_provided}")
        return False
    elif count_provided > count_required:
        print(f"Too many values provided. Needed {count_required}, provided with {count_provided}")
        return False
    return True


def write_to_file(wb, sheet, bodyweights_lst, start_row):
    """
    :param sheet: sheet in xlsx file containing bodyweights and dates
    :param bodyweights_lst: list of bodyweights in such a format: ['81', '85', '102', '102.1']
    :param start_row (int)
    """
    # remember, we ignore the first value. It's just there for us to recognize the bodyweights note
    for bw in bodyweights_lst[1:]:
        if sheet.cell(row=start_row, column=p.bodyweight_column).value is None:
            try:
                # note that we write as float because otherwise Calc (and perhaps Excel)
                # prepend each value with a "'", to mark it as a string. This causes it
                # to be left-aligned. The float conversion avoids that
                sheet.cell(row=start_row, column=p.bodyweight_column).value = float(bw)
            except ValueError:
                # it's a "?"
                sheet.cell(row=start_row, column=p.bodyweight_column).value = bw
            start_row += 1

        else:
            print(f"Cannot write to cell {start_row} - cell already written to!")
            print("No changes have been made")
            exit()
    wb.save(p.target_path)


if __name__ == '__main__':
    main()

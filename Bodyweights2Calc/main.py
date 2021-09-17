# retrieves bodyweights from Google Keep,
# then writes them to the correct row
# in the file specified by utilities.params.target_path
# does intelligent stuff too, like alert the user to missing entries, etc
# consider creating a version for use by crontab
# REMEMBER to change utilities.params whenever necessary, and to suffix EVERY bodyweight with a comma.
import gkeepapi.node
import openpyxl
import re
from datetime import datetime
import GKeepToCalc.utilities.params as p
import GKeepToCalc.utilities.utility_functions as uf

# history_length is the "X" most recent commits to the local file
# this number of bodyweights will remain (bracketed) in the Keep note
# after program execution.
# will default to 1 if set to 0. Otherwise, there'd be no bw note left to find next time.
history_length = 4

bw_reg = re.compile(r'(\d{2,3}\.\d\s?,)+'
                    r'|(\d{2,3}\s?,)+'
                    r'|(\?{1,3}\s?,)+')  # match 1-3 literal '?' characters then comma


def main():
    if not uf.target_path_is_xslx():
        raise ValueError("Target path specified in params.py does not point to xlsx file")
    if not uf.targetsheet_exists():
        raise ValueError("Target xlsx does not contain sheet specified in params.py")

    wb = openpyxl.load_workbook(p.target_path)
    sheet = wb[p.target_sheet]
    keep = uf.login_and_return_keep_obj()
    notes = uf.retrieve_notes(keep)
    bw_note = find_bodyweights_note(notes)

    # if the user hasn't edited their bodyweights file recently, we do not write.
    bw_edit_timestamp = return_bodyweights_note_edit_timestamp(bw_note)

    # don't expect a bodyweight if run between 00:00 and 05:00
    # we also use this value to set our endpoint (final cell).
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if datetime.now().hour < 5:
        from datetime import timedelta
        today -= timedelta(days=1)

    end_row = uf.find_row_of_datecell_given_datetime(sheet, today, date_column=p.date_column)
    if sheet.cell(end_row, p.bodyweight_column).value:
        print("Value already written for today. Exiting program")
        exit()

    if bw_edit_timestamp < today:
        print("- You have not edited your bodyweights note today.")
        print("- Please add today's bodyweight to the note. Then run the program again")
        print("- If you don't remember it, a question mark will be fine")
        print(f"bw_edit_timestamp= {bw_edit_timestamp}, note text=\"{bw_note.text}\"")
        exit()

    start_row = uf.return_first_empty_bodyweight_row(sheet,
                                                     date_column=p.date_column,
                                                     bodyweight_column=p.bodyweight_column)
    todays_row = uf.find_row_of_datecell_given_datetime(sheet, datetime.today())
    if todays_row == -1:
        raise ValueError("Today's date cell not found")
    bodyweights_lst = return_bw_lst(bw_note)

    # count_empty_cells_between_rows() accounts for fact that there may be empty rows separating years' entries.
    num_expected_bodyweights = (end_row - start_row + 1) - uf.count_empty_cells_between_rows(sheet, start_row, end_row,
                                                                                             cols_lst=[p.date_column])
    num_provided_bodyweights = len(bodyweights_lst)

    if num_expected_bodyweights != num_provided_bodyweights:
        print(f"Incorrect number of bodyweights supplied. "
              f"Expected {num_expected_bodyweights} bodyweights in note. Found {num_provided_bodyweights} bodyweights")
        print("Please correct the bodyweights note. In case of missing values, a question mark is a valid substitute"
              "for a forgotten bodyweight.")
        exit()

    # pair bodyweights with their target rows, where tpl[0]=int row, tpl[1]=str bodyweight
    # it accounts for emtpy rows, and will raise exceptions if anything is amiss.
    row_bw_tpl_lst = pair_bodyweights_with_rows(sheet, bodyweights_lst, start_row)

    uf.backup_targetpath()
    print("Writing bodyweights to file")
    write_to_file(wb, sheet, row_bw_tpl_lst)

    # trash the bodyweights note, and replace it. The replacement has "history_length"
    # values saved in its history (i.e. context window)
    history = return_history(bw_note, history_length)
    print("Updating note in Keep")
    trash_original_and_replace(keep, bw_note, history)
    print("Finished!")


def return_history(bw_note, history_length) -> str:
    # given the note containing bodyweights, create & return a history
    # "history" is a parenthesized string containing a number of bodyweights
    # as specified by history_length
    bw_str = bw_note.text.replace('(', '').replace(')', '')
    all_bws_lst = bw_str.split(',')  # [83, 82.8, 83.5, ' ']
    try:
        all_bws_lst.remove(' ')
    except ValueError:
        pass

    if history_length == 0:
        history_length = 1

    # note that history captures leading spaces, like so:
    # ['82.3', ' 84.5', ' ?', ' 85']
    history = all_bws_lst[-history_length:]
    for ind, h in enumerate(history):
        history[ind] = history[ind].replace(' ', '')

    history = "(" + ", ".join(history) + "), "
    return history


def trash_original_and_replace(keep, bw_note, history) -> None:
    # Trash original bodyweight note, and replace with a new bodyweights note
    # items in trash remain available for 7 days, whereas changes to bw_note are irreversible
    # that's why we create a new note this way.

    keep.createNote(title='', text=history)
    bw_note.trash()
    keep.sync()
    print("Synchronizing")
    # without a wait sometimes sync doesn't complete
    import time
    time.sleep(3)


def find_bodyweights_note(notes) -> gkeepapi.node.Note:
    # Within "notes", find the bodyweights note and return it. Match either title or body.
    # we expect bodyweight note's format to resemble formats like these 3 below:
    # 83.2, 83, ?, 83.4,
    # 101,
    # 100.4, 100.9, 99.8,
    # i.e. 2-3 digits with optional decimal place, followed by a comma
    # spaces are optional. Commas are not. Each number must be followed by one comma
    for gnote in notes:
        # don't search trashed notes.
        if gnote.trashed:
            continue

        for x in [gnote.title, gnote.text]:
            if x.isdigit() and len(x) > 3:
                # it's probably a PIN
                continue

            for accepted_symbol in "(),.? ":
                x = x.replace(accepted_symbol, '')
            if not x.isdigit():
                continue
            return gnote

    raise ValueError("No matching note found. "
                     "1) Does your bodyweight note exist? "
                     "2) Is it in a valid format, with more than 1 entry? "
                     "3) Does it contain only numbers, spaces, commas and full stops?")


def return_bodyweights_note_edit_timestamp(bw_note) -> datetime.date:
    # Take note containing bodyweights, return datetime object in form %Y-%m-%dT%H:%M:%S.%fZ
    # example: "2020-07-06 11:20:44.428000"
    return bw_note.timestamps.edited


def return_bw_lst(bw_note) -> list:
    # Take bodyweights note and return list of bodyweights found outside of parentheses
    # (i.e. outside of history / context window)
    bodyweights = []
    for x in [bw_note.title, bw_note.text]:
        if x.count("(") != x.count(")"):
            print("ERROR: mismatched parentheses in bodyweights note")
            raise ValueError
        if x.count("(") == 1:
            # discard context window, to find uncommitted bodyweights
            # changes "(82.3, 84.5), ?, 85" to " ?, 85"
            x = x.split("),")[1]
        if x.count("(") > 1 or x.count(")") > 1:
            print("ERROR: unexpected number of parentheses in bodyweights note")
            raise ValueError

        if len(re.findall(bw_reg, x)) > 0:
            if len(bodyweights) == 0:
                # change findall's output from this kind:
                # [('', '81,'), ('', '85,'), ('', '102,'), ('102.1,', '')]
                # to this kind
                # ['81', '85', '102', '102.1']
                bodyweights = ["".join(m) for m in re.findall(bw_reg, x)]
                bodyweights = [t.replace(',', '') for t in bodyweights]
            else:
                print("ERROR: Bodyweights found in both title and text of note")
                print("Please tidy up note, such that *either* the note's title *or*", end=' ')
                print("the note's text contain ALL of the bodyweights, and the counterpart is empty")
                raise ValueError

    if len(bodyweights) > 0:
        return bodyweights

    else:
        print(f"Debug: Note.title='{bw_note.title}'; Note.text='{bw_note.text}'")
        print("INFO: no bodyweights found in Keep note. There is nothing new to write")
        print("exiting")
        exit()


def pair_bodyweights_with_rows(sheet, bodyweights_lst, start_row: int):
    """
    :param sheet: sheet in xlsx file containing bodyweights and dates
    :param bodyweights_lst: list of bodyweights in such a format: ['81', '85', '102', '102.1']
    :param start_row (int)
    :return: a list of tuples, where tuple[0] is the int row to write to, and tuple[1] the str bodyweight
    """
    # we separate this function from the write function because we want an atomic transaction
    # either all writes succeed, or none do (and we don't write or change anything)
    # so we check all rows before writing anything
    # accounts for empty cells!
    # todo: rework description

    tpl_pairs_lst = []
    current_row = start_row
    max_empty_rows = 10
    count_empty = 1

    for bw in bodyweights_lst:
        date_cell_value = sheet.cell(row=current_row, column=p.date_column).value
        while date_cell_value is None:
            # skip empty cells in date column (e.g. at end of year), up to max length "max_empty_rows"
            current_row += 1
            count_empty += 1
            date_cell_value = sheet.cell(row=current_row, column=p.date_column).value
            if count_empty == max_empty_rows:
                print(f"error at row {current_row}")
                raise IndexError(f"Found too many empty date cells ({count_empty}). "
                                 f"Please verify that your date cell column has values remaining")

        bw_cell_value = sheet.cell(row=current_row, column=p.bodyweight_column).value
        if bw_cell_value is None:
            tpl = (current_row, str(bw))
            tpl_pairs_lst.append(tpl)
            current_row += 1
        else:
            raise ValueError(f"Cannot write to cell {current_row} - cell already written to!\n"
                             f"No changes have been made")

    if len(tpl_pairs_lst) == len(bodyweights_lst):
        return tpl_pairs_lst
    else:
        raise Exception("Programming error: length of tpl_pairs_lst does not equal length of bodyweights_lst")


def write_to_file(wb, sheet, row_bodyweight_tuple_list):
    # bodyweights_rows_tuple_list is a list of tuples, where tuple[0] is the int row to write to,
    # and tuple[1] the str bodyweight value)

    for tpl in row_bodyweight_tuple_list:
        try:
            # we write as float because otherwise Calc (and perhaps Excel)
            # prepend each value with a "'", to mark it as a string, causing it
            # to be left-aligned. The float conversion avoids that
            sheet.cell(row=tpl[0], column=p.bodyweight_column).value = float(tpl[1])
        except ValueError:
            # given bodyweight is "?"
            sheet.cell(row=tpl[0], column=p.bodyweight_column).value = tpl[1]

    wb.save(p.target_path)


if __name__ == '__main__':
    main()

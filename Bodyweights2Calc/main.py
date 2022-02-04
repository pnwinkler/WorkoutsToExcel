# retrieves bodyweights from Google Keep, then writes them to the correct row in the file specified by
# utilities.params.TARGET_PATH. Does some helpful things too, like alert the user to missing entries, etc
import gkeepapi.node
import openpyxl
import time
from datetime import datetime
from typing import List, Union, Tuple
import GKeepToCalc.utilities.params as p
import GKeepToCalc.utilities.utility_functions as uf


def main():
    if not uf.target_path_is_xslx(p.TARGET_PATH):
        raise ValueError(f"Target path specified in params.py does not point to xlsx file. "
                         f"This is the path\n{p.TARGET_PATH}")
    if not uf.targetsheet_exists(p.TARGET_PATH, p.TARGET_SHEET):
        raise ValueError(f"Target xlsx does not contain sheet specified in params.py. "
                         f"This is the path\n{p.TARGET_PATH}")

    wb = openpyxl.load_workbook(p.TARGET_PATH)
    sheet = wb[p.TARGET_SHEET]
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

    end_row = uf.find_row_of_datecell_given_datetime(sheet, today, date_column=p.DATE_COLUMN)
    assert end_row != -1, "Failed to find the appropriate end row in the xlsx file"
    if sheet.cell(end_row, p.BODYWEIGHT_COLUMN).value:
        print("Value already written for today. Exiting program")
        exit()

    if bw_edit_timestamp < today:
        print("- You have not edited your bodyweights note today.")
        print("- Please add today's bodyweight to the note. Then run the program again")
        print("- If you don't remember it, a question mark will be fine")
        print(f"bw_edit_timestamp= {bw_edit_timestamp}, note text=\"{bw_note.text}\"")
        exit()

    start_row = uf.return_first_empty_bodyweight_row(sheet,
                                                     date_column=p.DATE_COLUMN,
                                                     bodyweight_column=p.BODYWEIGHT_COLUMN)
    todays_row = uf.find_row_of_datecell_given_datetime(sheet, datetime.today())
    if todays_row == -1:
        raise ValueError("Today's date cell not found")
    context_window, bodyweights_lst = split_context_window_bodyweights_lst(bw_note)

    if not bodyweights_lst:
        print(f"Debug: Note.title='{bw_note.title}'; Note.text='{bw_note.text}'")
        print("INFO: no bodyweights found in Keep note. There is nothing new to write\nExiting")
        exit()

    # this is the number of bodyweights missing in the sheet, accounting for the fact that there may be empty rows
    # separating between target write cells (e.g. at year's end)
    num_expected_bodyweights = (end_row - start_row + 1) - uf.count_empty_cells_between_rows(sheet, start_row, end_row,
                                                                                             cols_lst=[p.DATE_COLUMN])
    num_provided_bodyweights = len(bodyweights_lst)

    if num_expected_bodyweights != num_provided_bodyweights:
        print(f"Incorrect number of bodyweights supplied. "
              f"Expected {num_expected_bodyweights} bodyweights in note. Found {num_provided_bodyweights} bodyweights")
        print("Please correct the bodyweights note. In case of missing values, a question mark is a valid substitute "
              "for a forgotten bodyweight.")
        exit()

    # pair bodyweights with their target rows, where tpl[0]=int row, tpl[1]=str bodyweight
    # it accounts for emtpy rows, and will raise exceptions if anything is amiss.
    row_bw_tpl_lst = pair_bodyweights_with_rows(sheet, bodyweights_lst, start_row)

    # prepare history for the bodyweight Note in Keep. This history/"context window" represents the X most recent
    # bodyweights committed to file
    history: str = return_bodyweight_history(context_window, bodyweights_lst, p.HISTORY_LENGTH)

    uf.backup_targetpath()
    print("Writing bodyweights to file")
    write_to_file(wb, sheet, row_bw_tpl_lst)

    # trash the bodyweights note, and replace it. The replacement has "history_length"
    # values saved in its history (i.e. context window)
    print("Updating note in Keep")
    trash_original_and_replace(keep, bw_note, history)
    print("Finished!")


def return_bodyweight_history(context_window_weights, new_bodyweights: List[str], history_length) -> str:
    # given a list of already committed bodyweights (i.e. from a previous context window), and a list of bodyweights
    # from outside the context window, return a new string containing the X most recent bodyweights from those lists,
    # where X is an integer specified in params.py and "recent" means having the greatest index, post-extend.

    assert isinstance(history_length, int), "Please provide an integer history_length"

    if len(context_window_weights) == 0 and len(new_bodyweights) == 0:
        return ''

    # the problem with extend is that it raises on either list being empty
    all_bodyweights = context_window_weights[::]
    for val in new_bodyweights:
        if val:
            all_bodyweights.append(val)

    # drop None values
    # all_bodyweights = [x for x in all_bodyweights if x]

    if not all([isinstance(elem, str) for elem in all_bodyweights]):
        # we need string values because only strings can represent question marks "?" (i.e. absent bodyweights)
        raise ValueError(f"Error: non-string elements found in bodyweights list")

    # if history length = 0, set it to 0
    history_length = max(history_length, 0)

    try:
        history = all_bodyweights[-history_length:]
    except IndexError:
        # history greater than the number of bodyweights in Note
        history = all_bodyweights

    for ind, _ in enumerate(history):
        history[ind] = history[ind].replace(' ', '')

    history = "(" + ", ".join(history) + "), "
    return history


def discard_string_context_window(bodyweights_str: str) -> str:
    if ")" not in bodyweights_str:
        return bodyweights_str
    bw_str = bodyweights_str.split("),")[1]
    # remove possible leading spaces
    return bw_str.lstrip()


def trash_original_and_replace(keep, bw_note, history) -> None:
    # Trash original bodyweight note, and replace with a new bodyweights note
    # items in trash remain available for 7 days, whereas changes to bw_note are irreversible
    # that's why we create a new note this way.

    keep.createNote(title=p.BODYWEIGHTS_NOTE_TITLE, text=history)
    bw_note.trash()
    keep.sync()
    print("Synchronizing")
    # without a wait sometimes sync doesn't complete
    time.sleep(3)


def find_bodyweights_note(notes: List[gkeepapi.node.Note]) -> gkeepapi.node.Note:
    # Given a list of Notes, find the bodyweights note and return it.
    # We search for a note whose title equals the value specified in params.py, and raise a ValueError if multiple
    # notes are found with that string in their title
    matches = []
    for note in notes:
        if note.trashed:
            continue

        if note.title.strip().lower() == p.BODYWEIGHTS_NOTE_TITLE.lower():
            matches.append(note)

    if len(matches) == 0:
        raise ValueError("No matching note found.\n"
                         "1) Does your bodyweight note exist?\n"
                         "2) Does it contain \"{p.BODYWEIGHTS_NOTE_TITLE}\" (without quotes) in its title?")

    if len(matches) > 1:
        raise ValueError(f"Several Notes found with \"{p.BODYWEIGHTS_NOTE_TITLE}\" in their title. Unable to determine"
                         f" which is the correct Note. Please trash the incorrect Note, or update the value of"
                         f" the bodyweights note title in params.py")
    return matches[0]


def return_bodyweights_note_edit_timestamp(bw_note) -> datetime.date:
    # Take note containing bodyweights, return datetime object in form %Y-%m-%dT%H:%M:%S.%fZ
    # example: "2020-07-06 11:20:44.428000"
    return bw_note.timestamps.edited


def return_depunctuated_bodyweights_text(text, keep_decimal_places=False, keep_spaces=False, keep_question_marks=False) -> str:
    txt = text.replace(",", "").replace("(", "").replace(")", "")
    if not keep_decimal_places:
        txt = txt.replace(".", "")
    if not keep_spaces:
        txt = txt.replace(" ", "")
    if not keep_question_marks:
        txt = txt.replace("?","")
    return txt


def extract_bodyweights_lst_from_raw_string(raw_str) -> List[str]:
    depunc_str = return_depunctuated_bodyweights_text(raw_str, keep_decimal_places=True, keep_spaces=True, keep_question_marks=True)
    lst = [val for val in depunc_str.split(" ") if val.replace(" ", "")]
    return lst


def validate_bodyweight_note_text(bw_note_text: str):
    # if bodyweight note text not as expected, raise ValueError
    text = bw_note_text
    if "()" in text:
        # raise, to notify the user, in case (s)he accidentally ended up with "()" in the text
        raise ValueError("ERROR: empty parentheses in bodyweights note")

    if text.count("(") != text.count(")"):
        raise ValueError("ERROR: mismatched parentheses in bodyweights note")
    if text.count("(") > 1 or text.count(")") > 1:
        raise ValueError("ERROR: unexpected number of parentheses in bodyweights note")
    if text.count("(") == 1 and ")," not in text:
        raise ValueError("ERROR: the context window is not followed by a comma")

    de_punctuated_text = return_depunctuated_bodyweights_text(text)
    if len(de_punctuated_text) > 0 and not de_punctuated_text.isdigit():
        raise ValueError("ERROR: bodyweights are incorrectly formatted. They should consist only of digits, with "
                         "1-2 optional decimal places, and each bodyweight should be followed by a comma")


def split_context_window_bodyweights_lst(bw_note: gkeepapi.node.Note) -> Tuple[List[str], List[str]]:
    # TODO: description
    # Take bodyweights note and return 2 lists, if validation passes without error.
    # The first list contains all float values found within the sole set of parentheses, if present. Else we return [].
    #   this is the context window
    # The second list returns float values found unenclosed by parentheses. Return [] if none found.
    #   this is the list of bodyweights that are as yet not committed to the target outfile.

    validate_bodyweight_note_text(bw_note.text)
    text = bw_note.text

    de_punctuated_text = return_depunctuated_bodyweights_text(text, keep_decimal_places=True, keep_question_marks=True)
    if len(de_punctuated_text) == 0:
        return [], []

    # we found bodyweights. Now split into context window contents, and other bodyweights
    context_window_weights = ""
    uncommitted_weights = text
    if ")" in text:
        context_window_weights = text.split(")")[0]
        uncommitted_weights = text.split(")")[1]

    # extract bodyweights from raw strings
    context_window_weights = extract_bodyweights_lst_from_raw_string(context_window_weights)
    uncommitted_weights = extract_bodyweights_lst_from_raw_string(uncommitted_weights)

    # uncommitted_weights = [number.strip() for number in uncommitted_weights.split(",") if number.strip()]

    # try:
    #     uncommitted_weights = [float(bodyweight) for bodyweight in uncommitted_weights]
    # except ValueError:
    #     raise ValueError(f"ERROR: could not convert one of the following numbers in the bodyweights note"
    #                      f"\n{uncommitted_weights}")
    # 
    # try:
    #     context_window_weights = [float(weight) for weight in context_window_weights]
    # except ValueError:
    #     raise ValueError(f"ERROR: could not convert one of the following numbers in the context window of the "
    #                      f"bodyweights note"
    #                      f"\n{context_window_weights}")

    return context_window_weights, uncommitted_weights


def pair_bodyweights_with_rows(sheet,
                               bodyweights_lst: [List, float],
                               start_row: int,
                               max_empty_rows=10) -> List[Tuple[int, float]]:
    """
    :param sheet: sheet in xlsx file containing bodyweights and dates
    :param bodyweights_lst: list of floats, representing bodyweights not yet committed to file
    :param start_row (int)
    :return: a list of tuples, where tuple[0] is the int row to write to, and tuple[1] the str bodyweight. Empty cells
    are accounted for.
    """

    tpl_pairs_lst = []
    current_row = start_row
    count_empty = 1

    for bw in bodyweights_lst:
        date_cell_value = sheet.cell(row=current_row, column=p.DATE_COLUMN).value
        while date_cell_value is None:
            # skip empty cells in date column (e.g. at end of year), up to max length "max_empty_rows"
            # print(date_cell_value, bw, current_row)
            current_row += 1
            count_empty += 1
            date_cell_value = sheet.cell(row=current_row, column=p.DATE_COLUMN).value
            if count_empty >= max_empty_rows:
                print(f"error at row {current_row}")
                raise IndexError(f"Found too many empty date cells (the cutoff is {count_empty}). "
                                 f"Please verify that your date cell column contains enough non-empty values")

        # check if bodyweight cell is already written to
        bw_cell_value = sheet.cell(row=current_row, column=p.BODYWEIGHT_COLUMN).value
        if bw_cell_value is None:
            tpl = (current_row, bw)
            tpl_pairs_lst.append(tpl)
            current_row += 1
        else:
            raise ValueError(f"Bodyweight cannot be written to target row {current_row} - cell already written to!"
                             f"No changes have been made")

    if len(tpl_pairs_lst) == len(bodyweights_lst):
        return tpl_pairs_lst
    else:
        raise Exception("Programming error: length of tpl_pairs_lst does not equal length of bodyweights_lst")


def write_to_file(wb, sheet, row_bodyweight_tuple_list: List[Tuple[int, float]]):
    # bodyweights_rows_tuple_list is a list of tuples, where tuple[0] is the int row to write to,
    # and tuple[1] the str bodyweight value)

    for tpl in row_bodyweight_tuple_list:
        try:
            # we write as float because otherwise Calc (and perhaps Excel) prepend each value with a "'", to mark it as
            # a string, causing it to be left-aligned. The float conversion avoids that
            sheet.cell(row=tpl[0], column=p.BODYWEIGHT_COLUMN).value = float(tpl[1])
        except ValueError:
            # given bodyweight is "?"
            sheet.cell(row=tpl[0], column=p.BODYWEIGHT_COLUMN).value = tpl[1]

    wb.save(p.TARGET_PATH)


if __name__ == '__main__':
    main()

import pytest
from Bodyweights2Calc.main import *

class local_note:
    def __init__(self, text, title):
        self.text = text
        self.title = title

# so we can check timestamp.trashed for test_find_bodyweights_note()
class timestamps:
    def __init__(self):
        # the docs say this is a datetime when trashed
        # but my "not None" line catches all un-trashed notes, so idk.
        self.trashed = "not trashed"

class timestamp_no_trash_note(local_note):
    def __init__(self, text, title):
        super().__init__(text, title)
        self.timestamps = timestamps()


def test_return_history():
    # given a string, should return a count of parenthesized bodyweights
    # equalling min(history_length, count(bodyweights provided))
    # with the remaining notes following the parentheses.

    # the function sets a floor of 1 on this value
    history_length = 5
    return_history.history_length = 5
    loc_note = local_note("(82.3, 84.5), ?, 85, ", "A friendly title")
    assert return_history(loc_note, history_length) == "(82.3, 84.5, ?, 85), "

    history_length = 2
    assert return_history(loc_note, history_length) == "(?, 85), "

def test_find_bodyweights_note():

    # find the note containing bodyweights
    # assumption: there is only one.
    notes = []
    notes.append(timestamp_no_trash_note("5625", "23/09"))
    notes.append(timestamp_no_trash_note("5625", "23 September"))
    notes.append(timestamp_no_trash_note("A totally unrelated note about amazing stuff", ""))
    notes.append(timestamp_no_trash_note("001-555-666-999", "05 April"))
    notes.append(timestamp_no_trash_note("PIN:7764", "05 April"))
    notes.append(timestamp_no_trash_note("82 Birmingham", "05 April"))
    notes.append(timestamp_no_trash_note("(82.3, 84.5), ?, 85, ", "A friendly title"))
    notes.append(timestamp_no_trash_note("5625", "A friendly title"))

    assert find_bodyweights_note(notes) == notes[-2]

def test_return_bw_lst():
    # return uncommitted bodyweights as string
    # note that we generally expect *every* bodyweight to be followed by a comma
    loc_note_1 = local_note("(82.3, 84.5), ?, 85, ", "A friendly title")
    loc_note_2 = local_note(" ?, 85, 87.2, ", "25 September")
    loc_note_3 = local_note("102.3, ?,   101.4, ", "25 September")

    assert return_bw_lst(loc_note_1) == ["?", "85"]
    assert return_bw_lst(loc_note_2) == ["?", "85", "87.2"]
    assert return_bw_lst(loc_note_3) == ["102.3", "?", "101.4"]

    # ENABLE IF ALLOWING ABSENT COMMAS ON LINE-END
    # however, we allow the user to forget the comma at the line's end
    # how nice.
    # loc_note_4 = local_note(" ?, 85, ?, 87.2", "25 September")
    # assert return_bw_lst(loc_note_4) == ["?", "85", "?", "87.2"]
    # loc_note_5 = local_note(" ?, 85, ?, 87.2, 82", "September 25")
    # assert return_bw_lst(loc_note_5) == ["?", "85", "?", "87.2", "82"]
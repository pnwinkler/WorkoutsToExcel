from GKeepToCalc.KeepPruner.main import *


class LocalNote:
    def __init__(self, text, title):
        self.text = text
        self.title = title


def test_get_printable_note_date():
    # it takes a note, then abbreviates and formats its date as str
    # capitalization of months is inconsequential, so we don't test for it
    # we assume the user doesn't use double spaces, like "13  January"
    ln1 = LocalNote("","13 January")
    ln2 = LocalNote("","13 Jan")
    ln3 = LocalNote("","January 13 ")
    assert get_printable_note_date(ln1) == "13 Jan"
    assert get_printable_note_date(ln2) == "13 Jan"
    assert get_printable_note_date(ln3) == "13 Jan"

    ln4 = LocalNote("","Sept 12")
    ln5 = LocalNote("this is irrelevant","Sept 12")
    assert get_printable_note_date(ln4) == "12 Sep"
    assert get_printable_note_date(ln5) == "12 Sep"

    ln6 = LocalNote("","May 4")
    assert get_printable_note_date(ln6) == "04 May"

def test_return_note_text_minus_comments():
    # we expect a tailing space, because each exercise is space-separated
    ln1 = LocalNote("+ Squat 90kg: 7,7,7\n/a comment line\n(another comment line)", "title is irrelevant")
    assert return_note_text_minus_comments(ln1) == "Squat 90kg: 7,7,7 "

    ln2 = LocalNote("Bench 75kg: 7,7,7\nOhp 45kg: 8,8,8", "")
    assert return_note_text_minus_comments(ln2) == "Bench 75kg: 7,7,7 Ohp 45kg: 8,8,8 "

#  This file contains functions that are used to interact with Google Keep, using the gkeepapi library.

import getpass
import gkeepapi
import time
import params as p
from datetime import datetime
from typing import List
from utilities.utility_functions import convert_string_to_datetime, str_contains_est_xx_mins_line
from shared_types import Entry, Handler


class KeepApiHandler(Handler):
    # a class to handle all interactions with Google Keep using gkeepapi
    def __init__(self):
        self._keep_obj = self._login_and_return_keep_obj()
        self._notes: List[Entry] = self.retrieve_notes()

    def _login_and_return_keep_obj(self) -> gkeepapi.Keep:
        """
        Login to Google Keep using gkeepapi, and return the Keep object.
        :return: the Keep object
        """
        username, password = None, None
        try:
            from utilities.credentials import username, password
        except FileNotFoundError:
            print("You can save your username as an environment variable, which can save you from typing your username"
                  "each time (see credentials.py)")

        if not username:
            username = input('Google Keep username: ')
        if password is None:
            # getpass obscures the password as it's entered
            password = getpass.getpass('Google Keep password: ')

        print('Logging in...')
        keep = gkeepapi.Keep()
        keep.login(username, password)
        return keep

    def retrieve_notes(self, get_trashed=False, get_archived=False) -> List[Entry] | None:
        """
        Return all notes from Google Keep as Entry objects, or None if no notes were found.
        :param get_trashed: whether to retrieve trashed notes
        :param get_archived: whether to retrieve archived notes
        """
        assert isinstance(self._keep_obj, gkeepapi.Keep), "Invalid object passed in to retrieve_notes function"
        print('Retrieving notes')

        # if there are no notes, this function returns an empty list
        notes = self._keep_obj.find(trashed=get_trashed, archived=get_archived)
        if notes:
            notes: List[gkeepapi.node.Note]
            return [
                Entry(title=note.title, text=note.text, edit_timestamp=note.timestamps.edited)
                for note in notes
            ]
        print('No notes found! Incorrect username or password?')

    def return_google_note_datetime(self, note: gkeepapi.node.Note, raise_if_no_valid_date=False) -> datetime:
        """
        Return a datetime object, extracted from the note's title, and subtracting a year if that note's day month
        combination has not yet passed this year. Raise on failure, if requested.
        :param note: the note object
        :param raise_if_no_valid_date: raise if there's no date in the note title that can be converted to datetime
        :return: a datetime object, representing a date such that the date is between 0 and (365 * 2 - 1) days in the
        past.
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

    def return_bodyweights_note(self) -> gkeepapi.node.Note:
        """
        Given a list of Notes, find the bodyweights note and return it. If multiple matching Notes are found, then raise a
        ValueError.
        :return: a Note object
        """
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
            raise ValueError(
                f"Several Notes found with \"{p.BODYWEIGHTS_NOTE_TITLE}\" in their title. Unable to determine"
                f" which is the correct Note. Please trash the incorrect Note, or update the value of"
                f" the bodyweights note title in params.py")
        return matches[0]

    def replace_bodyweights_note(self, new_text) -> None:
        """
        Trash the bodyweights Note, and replace it with a new Note containing the new text. ( We don't edit in place
        because items in trash remain available for 7 days, whereas changes to existing Notes may be irreversible).
        :param new_text: the desired text of the new Note
        """

        self._keep_obj.createNote(title=p.BODYWEIGHTS_NOTE_TITLE, text=new_text)
        bw_note = self.return_bodyweights_note()
        bw_note.trash()
        self._keep_obj.sync()
        print("Synchronizing")
        # without a wait sometimes sync doesn't complete
        time.sleep(3)

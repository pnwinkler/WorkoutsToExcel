#  This file contains functions that are used to interact with Google Keep

import getpass
import os
import time
from datetime import datetime
from functools import cache
from typing import Dict, List

import gkeepapi

import utilities.params as p
from utilities.shared_types import Entry, Handler
from utilities.utility_functions import convert_string_to_datetime


class KeepApiHandler(Handler):
    # a class to handle all interactions with Google Keep
    def __init__(self):
        super().__init__()
        self._keep_obj = self._login_and_return_keep_obj()

        # a dict of note identifiers and note objects
        self._note_objects: Dict[str, gkeepapi.node.Note] = {}

    def _login_and_return_keep_obj(self) -> gkeepapi.Keep:
        """
        Log in to Google Keep, and return the Keep object.
        :return: the Keep object
        """
        username = os.environ.get("GKEEP_EMAIL")
        password = os.environ.get("KEEP_PASSPHRASE")

        if not username:
            username = input('Google Keep username: ')
        if password is None:
            # getpass obscures the password as it's entered
            password = getpass.getpass('Google Keep password: ')

        print('Logging in...')
        keep = gkeepapi.Keep()
        keep.login(username, password)
        return keep

    @cache
    def retrieve_notes(self, get_trashed=False, get_archived=False) -> List[Entry] | None:
        """
        Return all notes from Google Keep as Entry objects, or None if no notes were found.
        :param get_trashed: whether to retrieve trashed notes
        :param get_archived: whether to retrieve archived notes
        """
        assert isinstance(self._keep_obj, gkeepapi.Keep), "Invalid object passed in to retrieve_notes function"
        print('Retrieving notes')

        notes = self._keep_obj.find(trashed=get_trashed, archived=get_archived)
        if notes:
            # save for later use. todo: find a cleaner implementation
            self._note_objects = {note.id: note for note in notes}
            notes: List[gkeepapi.node.Note]
            return [
                Entry(title=note.title,
                      text=note.text,
                      edit_timestamp=note.timestamps.edited,
                      unique_identifier=note.id)
                for note in notes
            ]
        print('No notes found! Incorrect username or password?')

    def return_google_note_datetime(self, note: gkeepapi.node.Note, raise_if_no_valid_date=False) -> datetime:
        """
        Return a datetime object extracted from the note's title, subtracting one year if that note's day month
        combination lies in the future. Raise on failure, if requested.
        :param note: the note object
        :param raise_if_no_valid_date: raise if there's no date in the note title that can be converted to datetime
        :return: a datetime object, representing a date such that the date is between 0 and (365 * 2 - 1) days in the
        past.
        """
        assert isinstance(note, gkeepapi.node.Note), "return_raw_note_date did not receive a Note object"
        raw_date = str(note.title)
        ret_date = None
        try:
            ret_date = convert_string_to_datetime(raw_date)
        except ValueError as e:
            if raise_if_no_valid_date:
                raise ValueError(f"Cannot convert '{raw_date}' from note title, to date") from e
        return ret_date

    def return_bodyweights_note(self) -> gkeepapi.node.Note:
        """
        Find the bodyweights note and return it. If multiple matching Notes are found, then raise a ValueError.
        :return: a Note object
        """
        matches = []
        for note in self.retrieve_notes(get_trashed=False, get_archived=False):
            if note.title.casefold().strip() == p.BODYWEIGHTS_NOTE_TITLE.casefold().strip():
                matches.append(note)

        if len(matches) == 0:
            raise ValueError("No matching note found.\n"
                             "1) Does your bodyweight note exist?\n"
                             f"2) Does it contain `{p.BODYWEIGHTS_NOTE_TITLE}` (without quotes) in its title?")

        if len(matches) > 1:
            raise ValueError(
                f"{len(matches)} Notes found with `{p.BODYWEIGHTS_NOTE_TITLE}` in their title. We expect only one "
                "bodyweights Note. Please trash or rename any incorrect Notes.")
        return matches[0]

    def replace_bodyweights_note(self, new_text) -> None:
        """
        Trash the bodyweights Note, and replace it with a new Note containing the new text. (We don't edit in place
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

    def trash_notes(self, notes: List[Entry]) -> None:
        # trash() is reversible. delete() is not. Trashed notes will be deleted in 7 days.
        ids_to_be_deleted = [note.unique_identifier for note in notes]
        for note_id, gkeep_note in self._note_objects.items():
            if note_id in ids_to_be_deleted:
                gkeep_note.trash()
        print("Synchronizing")
        self._keep_obj.sync()
        # give sync time, in case of poor internet
        time.sleep(3)

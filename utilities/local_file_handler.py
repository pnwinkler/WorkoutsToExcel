import os
import datetime
import params as p
from typing import Dict, List
from shared_types import Entry


class LocalFileHandler:
    # a class to handle all interactions with local files
    def __init__(self):
        self._notes = self.retrieve_notes()

    def retrieve_notes(self) -> List[Entry] | None:
        """
        Retrieve all notes from local filesystem, or None if no notes are found.
        :return: a dict of note objects, where the keys are the note titles, and the values are the note contents
        """
        if not os.path.exists(p.LOCAL_SOURCE_DIR):
            raise ValueError(f"Could not find source directory {p.LOCAL_SOURCE_DIR}")

        print('Retrieving notes')
        notes = self._retrieve_notes(directory=p.LOCAL_SOURCE_DIR)
        if notes:
            return notes
        print('No notes found! Incorrect username or password?')

    def _retrieve_notes(self, directory: str, max_depth=2) -> List[Entry] | None:
        """
        Recursively retrieve notes from local filesystem if found, or None if no notes are found.
        :param directory: the directory to search
        :param max_depth: break if this depth is reached
        :return:
        """
        if max_depth == 0:
            return None

        notes = []
        for filename in os.listdir(directory):
            if os.path.isdir(os.path.join(directory, filename)):
                notes.append(self._retrieve_notes(os.path.join(directory, filename), max_depth - 1))
            elif filename.endswith(('.txt', '.md')):
                with open(os.path.join(directory, filename), 'r') as f:
                    # get the file's modification timestamp as datetime
                    timestamp = os.path.getmtime(os.path.join(directory, filename))
                    as_datetime = datetime.datetime.fromtimestamp(timestamp)
                    notes.append(Entry(title=filename, text=f.read(), edit_timestamp=as_datetime))
        return notes if notes else None

    def return_bodyweights_note(self) -> Entry:
        """
        Return the note that contains the bodyweight data.
        :return: the note object
        """
        for note in self._notes:
            if note.title.casefold().strip() == p.BODYWEIGHTS_NOTE_TITLE.casefold().strip():
                return note
        raise ValueError(f"Could not find note with title {p.BODYWEIGHTS_NOTE_TITLE}")

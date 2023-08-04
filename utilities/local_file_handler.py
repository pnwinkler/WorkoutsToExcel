import os
import datetime
import params as p
import utility_functions as uf
from typing import List
from shared_types import Entry, Handler


class LocalFileHandler(Handler):
    # a class to handle all interactions with local files
    def __init__(self):
        self._notes: List[Entry] = self.retrieve_notes()

    def retrieve_notes(self) -> List[Entry] | None:
        """
        Retrieve all notes from local filesystem, or None if no notes are found.
        :return: a dict of note objects, where the keys are the note titles, and the values are the note contents
        """
        if not os.path.exists(p.LOCAL_SOURCE_DIR):
            raise ValueError(f"Could not find source directory {p.LOCAL_SOURCE_DIR}")

        print('Retrieving notes')
        notes = self._retrieve_recursively(directory=p.LOCAL_SOURCE_DIR)
        if notes:
            return notes
        print('No notes found! Incorrect username or password?')

    def _retrieve_recursively(self, directory: str, max_depth=2) -> List[Entry] | None:
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
                notes.append(self._retrieve_recursively(os.path.join(directory, filename), max_depth - 1))
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

    def replace_bodyweights_note(self, new_text):
        """
        Backup the old bodyweights note and replace it with a new one containing the new text.
        :return:
        """
        bw_notes_path = self.return_bodyweights_note().path
        uf.backup_file_to_dir(bw_notes_path, p.LOCAL_BACKUP_DIR)
        with open(bw_notes_path, 'w') as f:
            f.write(new_text)

    def trash_notes(self, notes: List[Entry]) -> None:
        # todo: find cleaner solution
        backup_dir = os.path.join(p.LOCAL_BACKUP_DIR, 'trashed_notes')
        for note in notes:
            uf.backup_file_to_dir(note.path, backup_dir)
            os.remove(note.path)

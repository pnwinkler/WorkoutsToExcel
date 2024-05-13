import datetime
import os
from functools import cache
from typing import List

import utilities.params as p
import utilities.utility_functions as uf
from utilities.shared_types import Entry, Handler


class LocalFileHandler(Handler):
    # this class handles reading from, writing to, and updating local files
    def __init__(self):
        super().__init__()

        # the extensions of the files that are considered notes
        self._source_file_extensions = ('.txt', '.md')
        self._notes: List[Entry] = self.retrieve_notes()

    @cache
    def retrieve_notes(self) -> List[Entry] | None:
        """
        Retrieve all notes from local filesystem, or None if no notes are found.
        :return: a dict of note objects, where the keys are the note titles, and the values are the note contents
        """
        if not os.path.exists(p.LOCAL_NOTES_SOURCE_DIR):
            raise ValueError(f"Could not find source directory `{p.LOCAL_NOTES_SOURCE_DIR}`")

        print('Retrieving notes')
        notes = self._retrieve_recursively(directory=p.LOCAL_NOTES_SOURCE_DIR)
        if notes:
            return notes
        print(f"No notes found in the following directory or any of its children `{p.LOCAL_NOTES_SOURCE_DIR}`!")
        return []

    def _retrieve_recursively(self, directory: str, max_depth=2) -> List[Entry] | None:
        """
        Recursively retrieve notes from local filesystem if found, or None if no notes are found.
        :param directory: the directory to search
        :param max_depth: break if this depth is reached
        :return:
        """
        # todo: rename this variable
        if (max_depth == -1) or (directory in [p.LOCAL_EXCEL_BACKUP_DIR, p.LOCAL_NOTES_ARCHIVE_DIR]):
            return []

        notes = []
        for filename in os.listdir(directory):
            if os.path.isdir(os.path.join(directory, filename)) and "backup" not in filename.lower():
                notes.extend(self._retrieve_recursively(os.path.join(directory, filename), max_depth - 1))
            elif filename.endswith(self._source_file_extensions):
                with open(os.path.join(directory, filename), 'r') as f:
                    # get the file's modification timestamp as datetime
                    timestamp = os.path.getmtime(os.path.join(directory, filename))
                    as_datetime = datetime.datetime.fromtimestamp(timestamp)
                    # drop the file extension
                    notes.append(Entry(title=os.path.splitext(filename)[0], text=f.read(), edit_timestamp=as_datetime,
                                       path=os.path.join(directory, filename)))
        return [note for note in notes if note]

    def is_bodyweights_note(self, note: Entry) -> bool:
        return note.title.casefold().strip() == p.BODYWEIGHTS_NOTE_TITLE.casefold().strip()

    def return_bodyweights_note(self) -> Entry:
        """
        Return the note that contains the bodyweight data. Raise if it can't be found, or multiple matches are found
        :return: the note object
        """
        n = [note for note in self._notes if self.is_bodyweights_note(note)]
        count = len(n)
        match count:
            case 0:
                raise RuntimeError(f"Failed to find the bodyweights note.")
            case 1:
                return n[0]
            case _:
                raise RuntimeError(f"Found {count} bodyweight notes. Expected only one.")

    def replace_bodyweights_note(self, new_text):
        """
        Backup the old bodyweights note and replace it with a new one containing the new text.
        :return:
        """
        bw_note_path = self.return_bodyweights_note().path
        uf.backup_file_to_dir(bw_note_path,
                              p.LOCAL_NOTES_ARCHIVE_DIR,
                              basename_override="backup_bodyweights_note",
                              keep_date_info=True)
        with open(bw_note_path, 'w') as f:
            f.write(new_text)

    def discard_notes(self, notes: List[Entry]) -> None:
        """
        Moves the provided notes from their current path into the note archive directory.
        """
        for note in notes:
            try:
                uf.backup_file_to_dir(note.path,
                                      p.LOCAL_NOTES_ARCHIVE_DIR,
                                      # personal preference. If it's already going to be in the archive directory,
                                      # I don't need the word "backup" in the filename
                                      basename_override=f"{note.title}",
                                      keep_date_info=False)
            except Exception as e:
                print(f"Failed to backup file {note.path}. Error: {e}. This file will be left in place and untouched")
            else:
                # only remove the original file if backup was successful
                os.remove(note.path)

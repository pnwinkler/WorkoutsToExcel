# shared type hints
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List

import utilities.utility_functions as uf


@dataclass()
class Entry:
    # contains the title and contents of a note, plus relevant metadata
    text: str
    title: str
    edit_timestamp: datetime | None = None

    path: str | None = None  # could be a Keep URL or a full file path on the local system, for example
    unique_identifier: str | None = None

    def __post_init__(self):
        # if the note is a workout note, parse the title to get the date, else set it to None.
        self.floored_datetime: datetime | None = None
        if self.is_valid_workout_note(raise_on_invalid_format=False):
            # given a title like "2023-07-20 Deadlift day cycle 13 week 1.md", convert it to a datetime
            date_str = self.title.split()[0]
            self.floored_datetime = (
                uf.convert_string_to_datetime(date_str, regress_future_dates=False)
                .replace(hour=0, minute=0, second=0, microsecond=0))

    def is_valid_workout_note(self, raise_on_invalid_format=False, skip_todo_titles=True) -> bool:
        """
        Return whether a note is valid or not, as bool. A valid workout note must
        1) end with a time estimate line,
        2) have a date in the title YYYY-MM-DD format.
        If the note title contains "todo" and skip_todo_titles is True, return False.

        :param raise_on_invalid_format: A bool indicating whether to raise an exception if the note format is invalid.
        :param skip_todo_titles: A bool indicating whether to skip notes with "todo" in the title.

        :return: A boolean indicating whether the note is a valid workout note.
        """

        # "est ", followed by 1-3 digits or "?" characters, followed by " min" (case-insensitive). For example:
        # "Est 52 min", "est 5 mins", "Est ? mins", "est ?? mins"
        est_xx_mins_reg = re.compile(r'est (\d{1,3})|(\?{1,3}) min', re.IGNORECASE)
        if not bool(re.search(est_xx_mins_reg, self.text)):
            return False

        if "todo" in self.title.lower() and skip_todo_titles:
            print(f"Skipping note with 'todo' in the title: `{self.title}`")
            return False

        expected_date = self.title.split()[0]
        try:
            uf.convert_string_to_datetime(expected_date)
            return True
        except ValueError:
            pass

        # strictly speaking, other date formats would probably be OK, but officially we only support YYYY-MM-DD
        # (see README), so we encourage users to stick to that format.
        print(f"The note with this title '{self.title}' contains a recognized time estimate line, but no date could be "
              f"extracted from the note's title. This is an invalid combination. This program expects a date in the "
              f"format YYYY-MM-DD at the beginning of the note title.")
        if raise_on_invalid_format:
            raise ValueError("Invalid workout note format")
        return False

    def __repr__(self):
        return (f"Entry(title='{self.title}', text='{self.text[:20]}...', edit_timestamp={self.edit_timestamp}, "
                f"unique_identifier={self.unique_identifier})")


class Handler(ABC):
    @abstractmethod
    def retrieve_notes(self) -> List[Entry] | None:
        pass

    @abstractmethod
    def return_bodyweights_note(self) -> Entry:
        # return a *representation* of the note containing bodyweights.
        pass

    @abstractmethod
    def replace_bodyweights_note(self, new_text) -> None:
        # replace either the contents of the note containing bodyweights, or the entire note itself. We don't take
        # the title as an argument because it needs to equal the existing title in order for us to identify that note
        # as the bodyweights note in future
        pass

    @abstractmethod
    def discard_notes(self, notes: List[Entry]) -> None:
        # perform some tidy-up of the given notes. This could entail trashing, deletion, or archiving, for example.
        pass

# shared type hints
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List


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
        self.title_datetime: datetime | None = None
        if self.is_valid_workout_note(raise_on_invalid_format=False):
            # given a title like "2023-07-20 Deadlift day cycle 13 week 1.md", convert it to a datetime
            from utilities.utility_functions import convert_string_to_datetime
            date_str = self.title.split()[0]
            self.title_datetime = convert_string_to_datetime(date_str, regress_future_dates=False)

    def is_valid_workout_note(self, raise_on_invalid_format=False) -> bool:

        # 1. the note must contain an "est XX mins" line
        # "est ", followed by 1-3 digits or "?" characters, followed by " min" (case-insensitive). For example:
        # "Est 52 min", "est 5 mins", "Est ? mins", "est ?? mins"
        est_xx_mins_reg = re.compile(r'est (\d{1,3})|(\?{1,3}) min', re.IGNORECASE)
        if not bool(re.search(est_xx_mins_reg, self.text)):
            return False

        # 2. the note must contain a date in the title, in the correct format
        stripped_fmt = "YYYY-MM-DD".replace('-', '')
        title_stripped = self.title.replace("-", "")
        if not title_stripped[:len(stripped_fmt)].isdigit():
            msg = f"The note with this title '{self.title}' contains an est XX mins line but no date could be " \
                  f"extracted from its title. This is an invalid combination."
            raise ValueError(msg) if raise_on_invalid_format else print(msg)
            return False

        return True

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
    def trash_notes(self, notes: List[Entry]) -> None:
        # trash the given notes
        pass

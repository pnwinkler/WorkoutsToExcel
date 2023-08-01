# shared type hints
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import utility_functions as uf

# TODO: move this check from other files into here?
# track which note titles we've already seen
# seen_note_titles = []

@dataclass()
class Entry:
    # contains the title and contents of a note, plus relevant metadata
    text: str
    title: str
    edit_timestamp: datetime | None = None
    path = None  # could be a Keep URL or a full file path on the local system, for example

    def _is_workout_note(self) -> bool:
        """
        Returns True if the passed-in note is identified as a workout note, else False
        :param raise_on_invalid_format: whether to raise if there's an est XX mins line but no date
        :return: True / False
        """

        # "est ", followed by 1-3 digits or "?" characters, followed by " min" (case-insensitive). For example:
        # "Est 52 min", "est 5 mins", "Est ? mins", "est ?? mins"
        est_xx_mins_reg = re.compile(r'est (\d{1,3})|(\?{1,3}) min', re.IGNORECASE)
        return bool(re.search(est_xx_mins_reg, self.text))

    def is_valid_workout_note(self, raise_on_invalid_format=False) -> bool:
        if not self._is_workout_note():
            return False

        try:
            # if we can't convert the note title to a datetime, then the note does not match the format we expect of a
            # workout note
            uf.convert_string_to_datetime(self.title)
        except ValueError as e:
            msg = f"The note with this title '{self.title}' contains an est XX mins line but no date could be " \
                  f"extracted from its title. This is an invalid combination."
            raise ValueError(msg) from e if raise_on_invalid_format else print(msg)
        return True


class Handler(ABC):
    @abstractmethod
    def retrieve_notes(self) -> None:
        pass

    @abstractmethod
    def return_bodyweights_note(self) -> Entry:
        pass

    @abstractmethod
    def replace_bodyweights_note(self, new_text) -> None:
        # we don't take the title as an argument because it's needs to equal the existing title in order for us to
        # identify the note as the bodyweights note
        pass

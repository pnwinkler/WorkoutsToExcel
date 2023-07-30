# shared type hints
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass()
class Entry:
    # contains the title and contents of a note, plus relevant metadata
    text: str
    title: str
    edit_timestamp: datetime | None = None
    path = None  # could be a Keep URL or a full file path on the local system, for example


class Handler:
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

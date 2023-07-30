# shared type hints
from dataclasses import dataclass
from datetime import datetime


@dataclass()
class Entry:
    # contains the title and contents of a note, plus relevant metadata
    text: str
    title: str
    edit_timestamp: datetime | None = None

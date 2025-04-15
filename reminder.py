from dataclasses import dataclass
from datetime import datetime

@dataclass
class Reminder:
    id: str
    message: str
    time: datetime
    list: str
    location: str
    completed: bool
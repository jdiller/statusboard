from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class Reminder:
    id: str
    message: str
    time: datetime
    list: str
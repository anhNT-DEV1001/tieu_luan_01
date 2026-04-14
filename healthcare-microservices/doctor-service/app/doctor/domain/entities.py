from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Doctor:
    id: UUID
    full_name: str
    specialty: str
    created_at: datetime | None = None

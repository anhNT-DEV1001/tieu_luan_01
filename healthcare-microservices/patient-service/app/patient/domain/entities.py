from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Patient:
    id: UUID
    full_name: str
    phone: str
    created_at: datetime | None = None

from sqlmodel import SQLModel, Field
from datetime import datetime

class AuditLog(SQLModel, table=True):
    """Журнал аудита действий пользователей"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    action: str
    ip_address: str
    status_code: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

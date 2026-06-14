from sqlmodel import SQLModel, Field
from datetime import datetime

class EiisExportLog(SQLModel, table=True):
    """Лог выгрузок в ЕИИС Охрана Труда"""
    id: Optional[int] = Field(default=None, primary_key=True)
    export_type: str # SOUT, MEDEXAMS, etc.
    period: str      # 2026-Q2
    receipt_id: Optional[str] = None
    status: str = Field(default="PENDING")
    records_count: int
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

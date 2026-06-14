from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class KedoSignatureRecord(SQLModel, table=True):
    """Статус подписания документа через Госуслуги/ЕСИА"""
    id: Optional[int] = Field(default=None, primary_key=True)
    internal_doc_id: str = Field(index=True, max_length=100)
    employee_id: int = Field(foreign_key="employee.id", index=True)
    task_id: str = Field(unique=True, max_length=100, description="ID задачи в API Трудвсем")
    document_hash: str = Field(max_length=64)
    status: str = Field(default="PENDING", max_length=20)  # PENDING, SIGNED, REJECTED, EXPIRED
    signer_esia_id: Optional[str] = Field(default=None, max_length=50)
    signed_at: Optional[datetime] = None
    callback_received_at: datetime = Field(default_factory=datetime.utcnow)
    signed_pdf_path: Optional[str] = Field(default=None, max_length=500)
    
    employee: Optional["Employee"] = Relationship(back_populates="kedo_signatures")


class EiisExportLog(SQLModel, table=True):
    """Лог выгрузок в ЕИИС Охрана Труда"""
    id: Optional[int] = Field(default=None, primary_key=True)
    export_type: str = Field(max_length=30)  # SOUT, MEDEXAMS, PPE, ACCIDENTS
    period: str = Field(max_length=20)       # 2026-Q2, 2026-06
    receipt_id: Optional[str] = Field(default=None, max_length=100)
    status: str = Field(default="PENDING", max_length=20)
    records_count: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

from typing import Optional
from datetime import date, datetime
from sqlmodel import SQLModel, Field, Relationship


class BriefingRecord(SQLModel, table=True):
    """Запись о проведенном инструктаже"""
    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employee.id", index=True)
    briefing_type: str = Field(max_length=30)  # INTRODUCTORY, REPEAT, TARGET, etc.
    instructor_name: str = Field(max_length=255)
    date_conducted: datetime = Field(default_factory=datetime.utcnow)
    next_due_date: date = Field(index=True)
    notes: Optional[str] = None
    kedo_task_id: Optional[str] = Field(default=None, description="ID задачи в Трудвсем")
    
    employee: Optional["Employee"] = Relationship(back_populates="briefing_records")
    video_record: Optional["BriefingVideoRecord"] = Relationship(back_populates="briefing_record")


class BriefingVideoRecord(SQLModel, table=True):
    """Видеоверификация инструктажа с WORM-хранением"""
    id: Optional[int] = Field(default=None, primary_key=True)
    briefing_record_id: int = Field(foreign_key="briefingrecord.id", unique=True)
    video_storage_path: str = Field(max_length=500)
    video_hash: str = Field(max_length=64, description="SHA-256 хэш видео")
    integrity_signature: str = Field(max_length=128, description="HMAC подпись")
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    liveness_challenge: str = Field(description="Задание для проверки живости")
    duration_seconds: int
    browser_fingerprint: Optional[str] = Field(default=None, max_length=100)
    
    briefing_record: Optional[BriefingRecord] = Relationship(back_populates="video_record")

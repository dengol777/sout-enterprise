from typing import Optional, List
from datetime import date, datetime
from sqlmodel import SQLModel, Field, Relationship


class EmployeeBase(SQLModel):
    full_name: str = Field(index=True, max_length=255)
    personnel_number: str = Field(unique=True, index=True, max_length=50)
    snils: Optional[str] = Field(default=None, unique=True, max_length=14)
    hire_date: date
    is_active: bool = Field(default=True)
    department_id: Optional[int] = Field(default=None, foreign_key="department.id")
    esia_oid: Optional[str] = Field(default=None, description="OID из ЕСИА Госуслуг")
    has_esia_account: bool = Field(default=False)


class Employee(EmployeeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Связи
    work_history: List["WorkHistory"] = Relationship(back_populates="employee")
    briefing_records: List["BriefingRecord"] = Relationship(back_populates="employee")
    kedo_signatures: List["KedoSignatureRecord"] = Relationship(back_populates="employee")


class WorkHistory(SQLModel, table=True):
    """
    История работы на рабочих местах. 
    КРИТИЧНО для расчета спецстажа во вредных условиях.
    Никогда не удаляйте записи, только закрывайте end_date.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employee.id", index=True)
    workstation_id: int = Field(foreign_key="workstation.id", index=True)
    start_date: date = Field(index=True)
    end_date: Optional[date] = Field(default=None, index=True)  # NULL = текущее место
    actual_harm_days: int = Field(default=0, description="Дни фактической работы во вредности")
    excluded_days: int = Field(default=0, description="Больничные, отпуска, простои")
    
    employee: Optional[Employee] = Relationship(back_populates="work_history")

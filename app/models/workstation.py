from typing import Optional, List
from decimal import Decimal
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import JSON


class Workstation(SQLModel, table=True):
    """Рабочее место с результатами СОУТ"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, max_length=255)
    card_number: Optional[str] = Field(default=None, unique=True, description="Номер карты СОУТ")
    sout_class: str = Field(max_length=10)  # 3.1, 3.2, 3.3, 3.4, 4
    risk_factors: List[str] = Field(sa_column=Column(JSON, default=[]))
    salary_bonus_pct: Decimal = Field(default=Decimal("0.0"), max_digits=5, decimal_places=2)
    extra_leave_days: int = Field(default=0)
    milk_required: bool = Field(default=False)
    ppe_norm_id: Optional[int] = Field(default=None, foreign_key="ppe_norm.id")
    
    compensation_rules: List["CompensationRule"] = Relationship(back_populates="workstation")


class CompensationRule(SQLModel, table=True):
    """Правила начисления гарантий и компенсаций"""
    id: Optional[int] = Field(default=None, primary_key=True)
    workstation_id: int = Field(foreign_key="workstation.id", index=True)
    comp_type: str = Field(max_length=50)  # MILK, LEAVE, SALARY_BONUS, EARLY_RETIREMENT
    value: Decimal = Field(max_digits=10, decimal_places=2)
    condition_rule: Optional[str] = Field(default=None, description="Логика: 'стаж > 6 мес'")
    
    workstation: Optional[Workstation] = Relationship(back_populates="compensation_rules")

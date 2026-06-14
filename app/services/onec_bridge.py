import httpx
from datetime import date, timedelta
from typing import List, Dict, Optional
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class OneCBridge:
    """Мост к 1С:ЗУП через OData/HTTP сервисы"""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            auth=(username, password),
            timeout=30.0,
            headers={"Accept": "application/json"}
        )

    async def get_employees(self, active_only: bool = True) -> List[Dict]:
        """Получает список сотрудников из 1С"""
        filter_clause = "DeletionMark eq false"
        if active_only:
            filter_clause += " and DateOfDismissal eq null"

        params = {
            "$filter": filter_clause,
            "$select": "Ref_Key,FullName,PersonnelNumber,HireDate,DateOfBirth",
            "$top": 500,
        }

        response = await self.client.get("/odata/standard/Catalog_Сотрудники", params=params)
        response.raise_for_status()
        return response.json().get("value", [])

    async def get_harmful_absences(self, employee_ref_key: str, 
                                    start_date: date, 
                                    end_date: date) -> List[Dict]:
        """
        Получает периоды больничных и отпусков для исключения из спецстажа.
        КРИТИЧНО для калькулятора вредного стажа!
        """
        odata_start = start_date.isoformat()
        odata_end = end_date.isoformat()

        # Больничные листы
        sick_params = {
            "$filter": (
                f"Employee_Key eq guid'{employee_ref_key}' "
                f"and Period ge datetime'{odata_start}' "
                f"and Period le datetime'{odata_end}'"
            ),
            "$select": "Period,DurationDays,SicknessType"
        }

        # Отпуска (все виды, кроме ежегодного основного — он НЕ исключается из стажа!)
        leave_params = {
            "$filter": (
                f"Employee_Key eq guid'{employee_ref_key}' "
                f"and StartDate ge datetime'{odata_start}' "
                f"and EndDate le datetime'{odata_end}' "
                f"and VacationType ne 'ЕжегодныйОсновной'"
            ),
            "$select": "StartDate,EndDate,VacationType"
        }

        sick_resp = await self.client.get(
            "/odata/standard/RegisterInformation_БольничныеЛисты", 
            params=sick_params
        )
        leave_resp = await self.client.get(
            "/odata/standard/RegisterInformation_Отпуска", 
            params=leave_params
        )

        absences = []
        for item in sick_resp.json().get("value", []):
            absences.append({
                "type": "SICK_LEAVE",
                "start": item["Period"][:10],
                "days": item["DurationDays"]
            })
        for item in leave_resp.json().get("value", []):
            absences.append({
                "type": item["VacationType"],
                "start": item["StartDate"][:10],
                "end": item["EndDate"][:10]
            })

        return absences

    async def sync_to_local_db(self, session):
        """Полная синхронизация справочника сотрудников"""
        employees = await self.get_employees(active_only=True)
        synced = 0
        
        for emp_data in employees:
            # Upsert логика по табельному номеру
            existing = session.execute(
                select(Employee).where(
                    Employee.personnel_number == emp_data["PersonnelNumber"]
                )
            ).scalar_one_or_none()

            if existing:
                existing.full_name = emp_data["FullName"]
                existing.hire_date = emp_data["HireDate"][:10]
            else:
                new_emp = Employee(
                    full_name=emp_data["FullName"],
                    personnel_number=emp_data["PersonnelNumber"],
                    hire_date=emp_data["HireDate"][:10],
                    is_active=True
                )
                session.add(new_emp)
            synced += 1

        session.commit()
        logger.info(f"Синхронизировано {synced} сотрудников из 1С")
        return synced

    async def close(self):
        await self.client.aclose()

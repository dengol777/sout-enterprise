import httpx
import json
from datetime import date
from typing import Dict, List
from celery.schedules import crontab

EIIS_CONFIG = {
    "base_url": "https://eiisot.trudvsem.ru/api/v1",
    "org_inn": "YOUR_ORG_INN",
    "api_key": "YOUR_EIIS_API_KEY",  # Получается в ЛК ЕИИС ОТ
    "timeout": 60.0,
}


class EIIISOTExporter:
    """Экспортер данных в ЕИИС Охрана Труда"""

    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=EIIS_CONFIG["base_url"],
            headers={
                "X-API-Key": EIIS_CONFIG["api_key"],
                "X-Org-INN": EIIS_CONFIG["org_inn"],
                "Content-Type": "application/json",
            },
            timeout=EIIS_CONFIG["timeout"],
        )

    async def export_sout_results(self, workstations: List[Dict]) -> Dict:
        """
        Экспорт результатов СОУТ.
        Формат соответствует XSD-схеме ЕИИС ОТ.
        """
        payload = {
            "organizationINN": EIIS_CONFIG["org_inn"],
            "reportDate": date.today().isoformat(),
            "workplaces": [
                {
                    "workplaceId": ws["id"],
                    "name": ws["name"],
                    "soutClass": ws["sout_class"],
                    "riskFactors": ws["risk_factors"],
                    "employeeCount": ws["employee_count"],
                    "compensations": {
                        "salaryBonusPct": ws["salary_bonus_pct"],
                        "extraLeaveDays": ws["extra_leave_days"],
                        "milkIssuance": ws["milk_required"],
                    }
                }
                for ws in workstations
            ]
        }

        response = await self.client.post("/sout/upload", json=payload)
        response.raise_for_status()
        return response.json()  # {"receiptId": "...", "status": "ACCEPTED"}

    async def export_medical_exams(self, exams: List[Dict]) -> Dict:
        """Экспорт данных о периодических медосмотрах"""
        payload = {
            "organizationINN": EIIS_CONFIG["org_inn"],
            "examPeriod": f"{date.today().year}-Q{(date.today().month - 1) // 3 + 1}",
            "employees": [
                {
                    "snils": exam["employee_snils"],
                    "examType": exam["exam_type"],
                    "examDate": exam["exam_date"].isoformat(),
                    "conclusion": exam["fitness_status"],
                    "nextExamDate": exam["next_due_date"].isoformat(),
                    "harmfulFactors": exam["factors_checked"],
                }
                for exam in exams
            ]
        }

        response = await self.client.post("/medexams/upload", json=payload)
        response.raise_for_status()
        return response.json()

    async def get_receipt_status(self, receipt_id: str) -> Dict:
        """Проверка статуса обработки пакета данных"""
        response = await self.client.get(f"/receipts/{receipt_id}")
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.client.aclose()

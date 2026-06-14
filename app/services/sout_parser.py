import pandas as pd
from datetime import date
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import re

# Маппинг колонок Excel на поля БД (адаптируйте под ваш шаблон)
COLUMN_MAPPING = {
    "workstation_name": ["Наименование рабочего места", "Рабочее место", "Название РМ"],
    "sout_class": ["Класс условий труда", "Класс УТ", "Итоговый класс"],
    "risk_factors": ["Вредные факторы", "Факторы производственной среды", "Опасные и вредные факторы"],
    "ppe_norm": ["СИЗ", "Средства индивидуальной защиты", "Норма выдачи СИЗ"],
    "salary_bonus": ["Доплата (%)", "Размер повышения оплаты труда", "Надбавка %"],
    "extra_leave": ["Дополнительный отпуск (дней)", "Отпуск за вредность"],
}


class SOUTCardParser:
    """Парсер карт специальной оценки условий труда из Excel"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = self._load_and_normalize()

    def _load_and_normalize(self) -> pd.DataFrame:
        # Читаем Excel, пропускаем возможные заголовки/подвалы
        df = pd.read_excel(self.file_path, header=0)
        
        # Нормализуем имена колонок для поиска
        normalized_cols = {}
        for db_field, possible_names in COLUMN_MAPPING.items():
            for col in df.columns:
                if any(name.lower() in str(col).lower() for name in possible_names):
                    normalized_cols[db_field] = col
                    break
        
        if not normalized_cols.get("workstation_name") or not normalized_cols.get("sout_class"):
            raise ValueError(
                f"Не найдены обязательные колонки. Доступные: {list(df.columns)}. "
                f"Проверьте COLUMN_MAPPING."
            )
            
        return df.rename(columns={v: k for k, v in normalized_cols.items()})

    @staticmethod
    def parse_risk_factors(raw_value) -> List[str]:
        """Извлекает список факторов риска из ячейки"""
        if pd.isna(raw_value):
            return []
        # Разделяем по запятым, точкам с запятой, переносам строк
        factors = re.split(r'[;,\n]+', str(raw_value))
        return [f.strip() for f in factors if f.strip()]

    @staticmethod
    def clean_sout_class(raw_value) -> Optional[str]:
        """Приводит класс к стандартному формату (3.1, 3.2, 4 и т.д.)"""
        if pd.isna(raw_value):
            return None
        cleaned = str(raw_value).strip().replace(",", ".")
        match = re.match(r'^([1-4](\.\d)?)$', cleaned)
        return match.group(1) if match else None

    def parse_all(self) -> List[Dict]:
        """Возвращает список словарей, готовых к вставке в БД"""
        results = []
        errors = []

        for idx, row in self.df.iterrows():
            sout_class = self.clean_sout_class(row.get("sout_class"))
            if not sout_class:
                errors.append(f"Строка {idx + 2}: некорректный класс УТ '{row.get('sout_class')}'")
                continue

            results.append({
                "name": str(row["workstation_name"]).strip(),
                "sout_class": sout_class,
                "risk_factors": self.parse_risk_factors(row.get("risk_factors")),
                "salary_bonus_pct": float(row["salary_bonus"]) if pd.notna(row.get("salary_bonus")) else 0.0,
                "extra_leave_days": int(float(row["extra_leave"])) if pd.notna(row.get("extra_leave")) else 0,
                "milk_required": sout_class.startswith(("3.", "4.")),
                "parsed_at": date.today().isoformat(),
            })

        if errors:
            print(f"⚠️ Ошибки парсинга ({len(errors)}):\n" + "\n".join(errors[:10]))

        return results

    def save_to_db(self, session: Session, model_class):
        """Сохраняет распарсенные данные в БД с upsert-логикой"""
        records = self.parse_all()
        created, updated = 0, 0

        for record_data in records:
            existing = session.query(model_class).filter(
                model_class.name == record_data["name"]
            ).first()

            if existing:
                for key, value in record_data.items():
                    setattr(existing, key, value)
                updated += 1
            else:
                new_record = model_class(**record_data)
                session.add(new_record)
                created += 1

        session.commit()
        return {"created": created, "updated": updated, "total": len(records)}

from datetime import date, timedelta
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class WorkPeriod:
    """Период работы на вредном рабочем месте"""
    start_date: date
    end_date: Optional[date]  # None если работает по сей день
    actual_harm_days: int     # Дни фактической работы во вредности
    excluded_days: int        # Больничные, отпуска, простои


class HarmfulStayCalculator:
    """
    Калькулятор специального стажа для досрочной пенсии и компенсаций.
    Учитывает требования Постановления Правительства РФ № 516.
    """

    @staticmethod
    def calculate_total_harmful_years(periods: List[WorkPeriod], 
                                       as_of_date: date = None) -> dict:
        if as_of_date is None:
            as_of_date = date.today()

        total_days = 0
        detailed_periods = []

        for period in periods:
            # Пропускаем будущие периоды
            if period.start_date > as_of_date:
                continue

            effective_end = min(
                period.end_date or as_of_date, 
                as_of_date
            )

            # Фактические дни во вредности (уже очищены от исключений в источнике)
            # Если переданы сырые данные, можно вычесть excluded_days:
            net_days = max(0, period.actual_harm_days)

            total_days += net_days
            detailed_periods.append({
                "start": period.start_date.isoformat(),
                "end": effective_end.isoformat(),
                "net_harm_days": net_days
            })

        years = total_days // 365
        remaining_days = total_days % 365
        months = remaining_days // 30  # Упрощенно; для пенсии нужен точный календарный расчет

        return {
            "total_days": total_days,
            "years": years,
            "months_approx": months,
            "remaining_days": remaining_days - (months * 30),
            "is_enough_for_extra_leave": years >= 0 and total_days >= 180,  # Пример: полстажа
            "detailed_periods": detailed_periods
        }


# === Пример использования ===
if __name__ == "__main__":
    work_history = [
        WorkPeriod(
            start_date=date(2020, 1, 15),
            end_date=date(2022, 6, 30),
            actual_harm_days=780,   # За вычетом больничных и отпусков
            excluded_days=45
        ),
        WorkPeriod(
            start_date=date(2022, 8, 1),  # Перерыв в работе (увольнение/перевод)
            end_date=None,                 # Работает по сей день
            actual_harm_days=920,
            excluded_days=30
        ),
    ]

    result = HarmfulStayCalculator.calculate_total_harmful_years(work_history)
    
    print(f"Спецстаж: {result['years']} лет, "
          f"{result['months_approx']} мес., "
          f"{result['remaining_days']} дн.")
    print(f"Всего дней во вредности: {result['total_days']}")
    print(f"Право на доп. отпуск: {result['is_enough_for_extra_leave']}")

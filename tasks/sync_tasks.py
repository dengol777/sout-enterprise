from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery("sout", broker=f"redis://localhost:6379/0")

celery_app.conf.beat_schedule = {
    "sync-employees-daily": {
        "task": "tasks.sync_tasks.sync_employees_from_onec",
        "schedule": crontab(hour=6, minute=0),
    },
    "eiis-sout-monthly": {
        "task": "tasks.sync_tasks.export_sout_to_eiis",
        "schedule": crontab(day_of_month=1, hour=3, minute=0),
    },
    "check-eiis-receipts": {
        "task": "tasks.sync_tasks.check_eiis_receipts",
        "schedule": crontab(minute=0, hour="*/6"),
    },
}

@celery_app.task
def sync_employees_from_onec():
    """Синхронизация сотрудников из 1С:ЗУП"""
    pass  # Реализация через OneCBridge

@celery_app.task
def export_sout_to_eiis():
    """Ежемесячная выгрузка СОУТ в ЕИИС ОТ"""
    pass  # Реализация через EIIISOTExporter

@celery_app.task
def check_eiis_receipts():
    """Проверка статусов квитанций ЕИИС"""
    pass

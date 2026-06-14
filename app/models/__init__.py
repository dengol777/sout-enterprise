from .employee import Employee, WorkHistory
from .workstation import Workstation, RiskFactor
from .briefing import BriefingRecord, BriefingVideoRecord
from .kedo import KedoSignatureRecord
from .audit import AuditLog
from .eiis import EiisExportLog

# Важно: импорт всех моделей здесь гарантирует, что они будут зарегистрированы в метаданных SQLModel

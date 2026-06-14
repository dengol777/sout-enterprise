import hashlib
import base64
import httpx
from datetime import datetime
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class KedoDocument:
    """Модель документа для отправки на подпись"""
    internal_id: str          # UUID документа в вашей БД
    title: str                # "Инструктаж вводный №12/2026"
    content_hash: str         # SHA-256 хэш PDF-файла
    document_type: str        # Код типа документа из справочника Трудвсем
    employee_esia_id: str     # SNIILS / ESIA ID работника
    created_at: datetime


class GosuslugiKedoClient:
    """
    Клиент для работы с API КЭДО платформы 'Работа в России'.
    Документация: https://api.trudvsem.ru/docs/kedo
    """

    BASE_URL = "https://api.trudvsem.ru/api/v1/kedo"

    def __init__(self, client_id: str, client_secret: str, access_token: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.http = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Client-Id": client_id,
            },
            timeout=30.0,
        )

    @staticmethod
    def compute_document_hash(pdf_bytes: bytes) -> str:
        """Вычисляет SHA-256 хэш документа для проверки целостности"""
        return hashlib.sha256(pdf_bytes).hexdigest()

    async def send_for_signature(self, doc: KedoDocument) -> Dict:
        """
        Отправляет документ на подпись работнику через Госуслуги.
        Возвращает task_id для отслеживания статуса.
        """
        payload = {
            "documentId": doc.internal_id,
            "title": doc.title,
            "documentTypeCode": doc.document_type,
            "contentHash": doc.content_hash,
            "signerEsiaId": doc.employee_esia_id,
            "createdAt": doc.created_at.isoformat(),
            "callbackUrl": "https://your-sout-system.local/api/kedo/callback",
        }

        response = await self.http.post("/documents/sign-request", json=payload)
        response.raise_for_status()
        return response.json()  # {"taskId": "...", "status": "PENDING"}

    async def get_signature_status(self, task_id: str) -> Dict:
        """Проверяет статус подписания документа"""
        response = await self.http.get(f"/documents/sign-status/{task_id}")
        response.raise_for_status()
        return response.json()
        # Возможные статусы: PENDING, SIGNED, REJECTED, EXPIRED

    async def download_signed_document(self, task_id: str) -> bytes:
        """Скачивает подписанный документ с усиленной меткой времени"""
        response = await self.http.get(f"/documents/{task_id}/signed-content")
        response.raise_for_status()
        return response.content

    async def close(self):
        await self.http.aclose()

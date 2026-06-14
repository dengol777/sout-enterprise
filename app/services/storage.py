import io
from minio import Minio
from minio.commonconfig import GOVERNANCE, COMPLIANCE
from datetime import timedelta

class SoutStorage:
    """Хранилище для документов и видео СУОТ с WORM-защитой"""

    BUCKET_NAME = "sout-archive"

    def __init__(self, endpoint: str, access_key: str, secret_key: str):
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=True,  # Обязательно HTTPS
        )

    def upload_video(self, object_name: str, data: bytes, content_type: str) -> dict:
        """
        Загружает видео инструктажа с автоматической WORM-блокировкой.
        Политика бакета применяется автоматически.
        """
        result = self.client.put_object(
            bucket_name=self.BUCKET_NAME,
            object_name=object_name,
            data=io.BytesIO(data),
            length=len(data),
            content_type=content_type,
            metadata={
                "x-amz-object-lock-mode": "COMPLIANCE",
                "x-amz-object-lock-retain-until-date": "",  # Наследуется от политики бакета
            },
        )

        return {
            "object_name": object_name,
            "etag": result.etag,
            "version_id": result.version_id,  # Важно для аудита!
        }

    def get_presigned_url(self, object_name: str, expires: int = 3600) -> str:
        """Генерирует временную ссылку для просмотра видео инспектором/сотрудником"""
        return self.client.presigned_get_object(
            bucket_name=self.BUCKET_NAME,
            object_name=object_name,
            expires=timedelta(seconds=expires),
        )

    def verify_integrity(self, object_name: str, expected_etag: str) -> bool:
        """Проверяет, что объект не был изменён (сравнение ETag)"""
        stat = self.client.stat_object(self.BUCKET_NAME, object_name)
        return stat.etag == expected_etag

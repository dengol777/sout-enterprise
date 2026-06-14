# backend: video_verification.py
import hashlib
import hmac
from datetime import datetime, timedelta
from fastapi import UploadFile, File, HTTPException

ALLOWED_MIME_TYPES = {"video/webm", "video/mp4"}
MAX_VIDEO_SIZE_MB = 100
VERIFICATION_SECRET = "your_hmac_secret_for_video_integrity"


class VideoVerifier:
    """Верифицирует целостность и параметры видео инструктажа"""
    
    @staticmethod
    async def validate_upload(file: UploadFile, expected_duration_sec: int) -> dict:
        # 1. Проверка типа и размера
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(400, f"Недопустимый формат: {file.content_type}")
        
        content = await file.read()
        size_mb = len(content) / (1024 * 1024)
        if size_mb > MAX_VIDEO_SIZE_MB:
            raise HTTPException(400, f"Видео слишком большое: {size_mb:.1f} МБ")
        
        # 2. Вычисление хэша для неизменности
        video_hash = hashlib.sha256(content).hexdigest()
        
        # 3. Генерация HMAC-подписи хэша (защита от подмены файла)
        timestamp = datetime.utcnow().isoformat()
        signature = hmac.new(
            VERIFICATION_SECRET.encode(),
            f"{video_hash}:{timestamp}".encode(),
            hashlib.sha256
        ).hexdigest()
        
        return {
            "video_hash": video_hash,
            "signature": signature,
            "timestamp": timestamp,
            "size_bytes": len(content),
            "mime_type": file.content_type,
        }
    
    @staticmethod
    def verify_integrity(video_hash: str, signature: str, timestamp: str) -> bool:
        """Проверяет, что видео не было изменено после загрузки"""
        expected = hmac.new(
            VERIFICATION_SECRET.encode(),
            f"{video_hash}:{timestamp}".encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

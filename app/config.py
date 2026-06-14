from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str = "sout-archive"
    ESIA_CLIENT_ID: str
    ESIA_CLIENT_SECRET: str
    ESIA_REDIRECT_URI: str
    ONEC_BASE_URL: str
    ONEC_USERNAME: str
    ONEC_PASSWORD: str
    EIIS_API_KEY: str
    EIIS_ORG_INN: str
    WEBHOOK_SECRET: str
    VIDEO_HMAC_SECRET: str
    JWT_SECRET: str

    class Config:
        env_file = ".env"

settings = Settings()

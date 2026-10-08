from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    CERTIFICATE_STORAGE_PATH: str = "./generated"
    CERTIFICATE_RETENTION_HOURS: int = 24
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()

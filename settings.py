from pydantic_settings import BaseSettings, SettingsConfigDict


# Environment-backed application settings
class Settings(BaseSettings):

    PORT: int = 8080
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    MAX_WORKER_THREADS: int = 4
    MAX_QUEUED_JOBS: int = 40

    MONGO_TARGET: str = "local"
    MONGODB_URI: str = "mongodb://localhost:27017"

    GOOGLE_CLOUD_PROJECT: str = ""
    GOOGLE_CLOUD_LOCATION: str = "us-central1"

    VERTEX_MODEL: str = "gemini-2.5-flash-lite"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BASE_URL: str = "https://dataaccess.scania.com"
    CLIENT_ID: str = ""
    SECRET_KEY: str = ""
    REDIS_URL: str = "redis://localhost:6379"
    TOKEN_EXPIRE_SECONDS: int = 3600  # 1 hour

    class Config:
        env_file = ".env"

settings = Settings()

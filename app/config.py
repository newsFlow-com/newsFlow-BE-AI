from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://newsflow:newsflow1234@localhost:5433/newsflow"
    anthropic_api_key: str = ""
    redis_url: str = "redis://localhost:6380/0"

    class Config:
        env_file = ".env"


settings = Settings()

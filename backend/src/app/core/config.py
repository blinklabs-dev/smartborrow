from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Snowflake Optimization Agent"
    DATABASE_URL: str = "sqlite:///./snowflake_agent.db"
    SECRET_KEY: str = "a_very_secret_key_that_should_be_changed"  # Replace with a real secret
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    OPENAI_API_KEY: str = "your_openai_api_key_here"

    class Config:
        case_sensitive = True

settings = Settings()

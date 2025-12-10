from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Redis configuration
    REDIS_HOST: str = Field(default="localhost", validation_alias="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, validation_alias="REDIS_PORT")
    REDIS_DB: int = Field(default=0, validation_alias="REDIS_DB")

    # Optional app-wide settings
    ENVIRONMENT: str = Field(default="development", validation_alias="ENVIRONMENT")
    DEBUG: bool = Field(default=True, validation_alias="DEBUG")

    model_config = {
        "populate_by_name": True
    }


# Singleton settings instance
settings = Settings()

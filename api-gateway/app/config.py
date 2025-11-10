from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='../../.env', env_file_encoding='utf-8', extra='ignore')

    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_DEFAULT_USER: str = "guest"
    RABBITMQ_DEFAULT_PASS: str = "guest"

    REDIS_HOST: str = "redis"

settings = Settings()
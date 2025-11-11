from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='../../.env', env_file_encoding='utf-8', extra='ignore')

    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_DEFAULT_USER: str = "guest"
    RABBITMQ_DEFAULT_PASS: str = "guest"

    REDIS_HOST: str = "redis"

    GATEWAY_DB_HOST: str = "gateway-db"
    GATEWAY_DB_NAME: str = "gateway_db"
    GATEWAY_DB_USER: str = "gateway_user"
    GATEWAY_DB_PASS: str = "gateway_pass"
    GATEWAY_DB_PORT: int = 5432

    USER_SERVICE_URL: str = "http://user-service:8001"

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.GATEWAY_DB_USER}:{self.GATEWAY_DB_PASS}@"
            f"{self.GATEWAY_DB_HOST}:{self.GATEWAY_DB_PORT}/{self.GATEWAY_DB_NAME}"
        )

settings = Settings()
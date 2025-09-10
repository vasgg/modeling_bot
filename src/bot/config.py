from pydantic import RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: SecretStr
    ADMIN: int
    MODERATOR: int
    MODEL_CHAT_ID: int
    PAYMENT_PROVIDER_TOKEN: SecretStr
    SHOP_ID: int
    REDIS_URL: RedisDsn

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)


def get_settings():
    return Settings()

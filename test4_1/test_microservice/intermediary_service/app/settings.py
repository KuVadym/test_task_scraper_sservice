from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # POSTGRES_URI: str
    MYSQL_URI:str
    CURRENCY_API_KEY: str
    REDIS_URL: str

    model_config = SettingsConfigDict(env_file=(".env", "stack.env", "env.dist"), env_file_encoding="utf-8", extra="ignore")


settings = Settings()  # type: ignore[call-arg]

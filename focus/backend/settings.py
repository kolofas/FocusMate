from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./focus.db"

    inbox_dedup_minutes: int = 10

    max_description_length: int = 4000
    max_title_length: int = 300

    urgent_tag: str = "urgent"
    focus_limit: int = 5

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

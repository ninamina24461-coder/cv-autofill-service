from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "CV Autofill Service"
    app_env: str = "dev"
    default_phone_region: str = "ZA"
    max_text_chars: int = 80000
    enable_ocr: bool = False


settings = Settings()

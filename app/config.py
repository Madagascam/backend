from typing import Tuple, Type, List

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
    TomlConfigSettingsSource,
)


class FastAPISettings(BaseSettings):
    origins: List[str]


class DatabaseSettings(BaseSettings):
    connection_string: str


class SecuritySettings(BaseSettings):
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int


class AnalysisSettings(BaseSettings):
    default_strategy: str
    engine_path: str

class Settings(BaseSettings):
    fastapi: FastAPISettings
    database: DatabaseSettings
    security: SecuritySettings
    analysis: AnalysisSettings

    model_config = SettingsConfigDict(toml_file='../config.toml')

    @classmethod
    def settings_customise_sources(
            cls,
            settings_cls: Type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (TomlConfigSettingsSource(settings_cls),)


settings = Settings()

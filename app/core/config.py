from typing import Tuple, Type, List

from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
    TomlConfigSettingsSource,
)


class FastAPISettings(BaseSettings):
    origins: List[str]


class DatabaseSettings(BaseModel):
    connection_string: str

class Settings(BaseSettings):
    fastapi: FastAPISettings
    database: DatabaseSettings

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

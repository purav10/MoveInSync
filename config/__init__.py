from pydantic_settings import BaseSettings

class CommonSettings(BaseSettings):
    APP_NAME: str = "SiteManager"
    DEBUG_MODE: bool = False


class ServerSettings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000


class DatabaseSettings(BaseSettings):
    DB_URL: str = "mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.1.1"
    DB_NAME: str = "bluebus"


class Settings(CommonSettings, ServerSettings, DatabaseSettings):
    pass

settings = Settings()
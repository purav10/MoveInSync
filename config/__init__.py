from pydantic_settings import BaseSettings

class CommonSettings(BaseSettings):
    APP_NAME: str = "SiteManager"
    DEBUG_MODE: bool = False


class ServerSettings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000


class DatabaseSettings(BaseSettings):
    DB_URL: str = "mongodb+srv://biyanipurav:purav%4010@cluster0.e5yakmh.mongodb.net/"
    DB_NAME: str = "bluebus"


class Settings(CommonSettings, ServerSettings, DatabaseSettings):
    pass

settings = Settings()
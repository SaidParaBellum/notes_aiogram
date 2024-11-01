from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    TOKEN: str
    DB_NAME: str
    DB_HOST: str
    DB_PORT: str
    DB_USER: str
    DB_PASS: str

    class Config:
        env_file = ".env"

settings = Settings()


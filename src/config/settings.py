from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """从 .env 读取数据库配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # .env 里多出的键不报错
    )

    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "coursemate"
    secret_key: str = ""
    token_expire_minutes: int = 30

    @property
    def database_url(self) -> str:
        # 密码先做 URL 编码：密码含 @ # / 等字符时，直接拼会破坏连接串
        pwd = quote_plus(self.db_password)
        return (
            f"mysql+pymysql://{self.db_user}:{pwd}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

settings = Settings()
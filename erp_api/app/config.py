import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    api_key: str
    allowed_ips: tuple[str, ...]
    database_url: str


def load_settings() -> Settings:
    ips = os.environ.get("ERP_API_ALLOWED_IPS", "")
    return Settings(
        api_key=os.environ.get("ERP_API_KEY", ""),
        allowed_ips=tuple(i.strip() for i in ips.split(",") if i.strip()),
        database_url=os.environ.get("DATABASE_URL", ""),
    )

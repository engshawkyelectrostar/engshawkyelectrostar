import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    api_key: str
    allowed_ips: tuple[str, ...]
    oracle_client_lib_dir: str
    oracle_user: str
    oracle_password: str
    oracle_dsn: str


def load_settings() -> Settings:
    ips = os.environ.get("ERP_API_ALLOWED_IPS", "")
    return Settings(
        api_key=os.environ.get("ERP_API_KEY", ""),
        allowed_ips=tuple(i.strip() for i in ips.split(",") if i.strip()),
        oracle_client_lib_dir=os.environ.get("ORACLE_CLIENT_LIB_DIR", ""),
        oracle_user=os.environ.get("ORACLE_USER", ""),
        oracle_password=os.environ.get("ORACLE_PASSWORD", ""),
        oracle_dsn=os.environ.get("ORACLE_DSN", ""),
    )

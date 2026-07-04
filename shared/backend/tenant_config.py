import json
from pathlib import Path

BASE_DIR = Path("/root/M-Tirta/tenants")


def tenant_dir(tenant: str) -> Path:
    return BASE_DIR / tenant


def config_file(tenant: str) -> Path:
    return tenant_dir(tenant) / "config.json"


def tenant_config(tenant: str) -> dict:
    file = config_file(tenant)

    if file.exists():
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)

    return {}


def save_tenant_config(tenant: str, data: dict):
    cfg = tenant_config(tenant)
    cfg.update(data)

    with open(config_file(tenant), "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)

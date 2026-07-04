import os
import json

from pathlib import Path


BASE_DIR = Path("/root/M-Tirta/tenants")


def tenant_dir(slug: str) -> Path:
    """
    /root/M-Tirta/tenants/tirta-lestari-iv
    """
    return BASE_DIR / slug


def asset_dir(slug: str) -> Path:
    """
    /assets
    """
    path = tenant_dir(slug) / "assets"
    path.mkdir(parents=True, exist_ok=True)
    return path


def profil_dir(slug: str) -> Path:
    """
    /assets/profil
    """
    path = asset_dir(slug) / "profil"
    path.mkdir(parents=True, exist_ok=True)
    return path


def logo_file(slug: str) -> Path:
    """
    /assets/logo.webp
    """
    return asset_dir(slug) / "logo.webp"


def tenant_config(slug: str) -> dict:
    """
    Membaca config.json milik tenant.
    """
    config_file = tenant_dir(slug) / "config.json"

    with open(config_file, "r", encoding="utf-8") as f:
        return json.load(f)


def current_tenant() -> str:
    """
    Tenant aktif untuk instance ini.
    """
    return os.getenv("TENANT_ID", "tirta-lestari-iv")

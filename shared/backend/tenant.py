# shared/backend/tenant.py

import json
from pathlib import Path


BASE_DIR = Path("/root/M-Tirta/tenants")

# sementara kita pakai tenant aktif default
DEFAULT_TENANT = "tirta-lestari-iv"


class Tenant:

    def __init__(self, slug, config):

        self.slug = slug

        self.nama = config.get("nama", slug)

        self.config = config


def get_current_tenant():

    slug = DEFAULT_TENANT

    config_file = BASE_DIR / slug / "config.json"

    if config_file.exists():

        with open(config_file, "r", encoding="utf-8") as f:

            config = json.load(f)

    else:

        config = {}

    return Tenant(slug, config)

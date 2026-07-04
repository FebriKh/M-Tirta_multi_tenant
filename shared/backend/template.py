from fastapi import Request
from fastapi.templating import Jinja2Templates

from shared.backend.tenant import get_current_tenant

templates = Jinja2Templates(directory="web/templates")


def render_template(
    request: Request,
    name: str,
    context: dict | None = None,
):
    """
    Wrapper TemplateResponse agar konfigurasi tenant
    otomatis tersedia di semua template.
    """

    context = context or {}

    tenant = get_current_tenant()

    context["tenant"] = tenant
    context["cfg"] = tenant.config

    return templates.TemplateResponse(
        request=request,
        name=name,
        context=context,
    )

# M-Tirta/api/main.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from shared.backend.database import engine, Base
from shared.backend.tenant_assets import current_tenant, profil_dir, asset_dir, tenant_config
from shared.backend.models import *

# buat tabel kalau belum ada
Base.metadata.create_all(bind=engine)

app = FastAPI(title="M-Tirta", version="3.0.0")

# static files
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# tambahkan setelah app.mount("/static"...)
app.mount(
    "/static/assets",
    StaticFiles(directory=str(asset_dir(current_tenant()))),
    name="assets"
)

# import routers
from api.routers.auth        import router as auth_router
from api.routers.dashboard   import router as dashboard_router
from api.routers.pelanggan   import router as pelanggan_router
from api.routers.meteran     import router as meteran_router
from api.routers.pembayaran  import router as pembayaran_router
from api.routers.pengeluaran import router as pengeluaran_router
from api.routers.pengurus    import router as pengurus_router
from api.routers.laporan     import router as laporan_router
from api.routers.developer   import router as developer_router

app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(pelanggan_router)
app.include_router(meteran_router)
app.include_router(pembayaran_router)
app.include_router(pengeluaran_router)
app.include_router(pengurus_router)
app.include_router(laporan_router)
app.include_router(developer_router)

@app.get("/manifest.json")
async def manifest():

    cfg = tenant_config(current_tenant())

    return JSONResponse({
        "name": cfg.get("nama_app", "M-Tirta"),
        "short_name": cfg.get("nama_app", "M-Tirta"),
        "description": cfg.get("nama_org", ""),
        "start_url": "/dashboard",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": cfg.get("warna_primer", "#1a56db"),
        "orientation": "portrait",
        "icons": [
            {
                "src": "/logo",
                "sizes": "192x192",
                "type": "image/webp"
            },
            {
                "src": "/logo",
                "sizes": "512x512",
                "type": "image/webp"
            }
        ]
    })

@app.get("/")
async def root():
    return RedirectResponse(url="/api/auth/login")

@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc):
    return RedirectResponse(url="/api/auth/login")

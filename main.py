import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from auth import hash_password
from database import BASE_DIR, SessionLocal, init_db
from models import Admin
from routers import admin, gallery

def seed_admin():
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD")
    if not password:
        raise RuntimeError("Set ADMIN_PASSWORD to initialize the development admin account")
    with SessionLocal() as db:
        if db.scalar(select(Admin).limit(1)):
            return
        db.add(Admin(username=username, hashed_password=hash_password(password)))
        db.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_admin()
    yield

app = FastAPI(title="Photo Portfolio CMS", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(gallery.router)
app.include_router(admin.router)

@app.exception_handler(HTTPException)
async def auth_redirect_handler(request: Request, exc: HTTPException):
    wants_html = "text/html" in request.headers.get("accept", "")
    if exc.status_code == 401 and wants_html:
        return RedirectResponse("/admin/login", status_code=303)
    return await http_exception_handler(request, exc)

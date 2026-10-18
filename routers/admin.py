import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse
from PIL import Image, ExifTags
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import COOKIE_NAME, authenticate_admin, create_access_token, get_current_admin
from database import UPLOAD_DIR, get_db
from models import Admin, Photo
from views import templates

router = APIRouter(prefix="/admin", tags=["admin"])
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
EXIF_MAKE = ExifTags.Base.Make.value
EXIF_MODEL = ExifTags.Base.Model.value

def extract_exif(path: Path) -> tuple[str | None, str | None]:
    """Read camera make and model out of an uploaded image's EXIF block."""
    try:
        with Image.open(path) as image:
            exif = image.getexif()
    except Exception:
        return None, None

    def read(tag: int) -> str | None:
        value = exif.get(tag)
        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="replace")
        if value is None:
            return None
        value = str(value).strip("\x00 ")
        return value or None
    return read(EXIF_MAKE), read(EXIF_MODEL)

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})

@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    admin = authenticate_admin(db, username, password)
    if not admin:
        return templates.TemplateResponse(request, "login.html", {"error": "Invalid username or password."}, status_code=status.HTTP_401_UNAUTHORIZED)
    response = RedirectResponse("/admin", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(COOKIE_NAME, create_access_token(admin.username), httponly=True, samesite="lax")
    return response

@router.post("/token")
def issue_token(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    admin = authenticate_admin(db, username, password)
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": create_access_token(admin.username), "token_type": "bearer"}

@router.get("/logout")
def logout():
    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(COOKIE_NAME)
    return response

@router.get("", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    photos = db.scalars(select(Photo).order_by(Photo.created_at.desc())).all()
    return templates.TemplateResponse(request, "dashboard.html", {"photos": photos, "admin": admin})

@router.post("/upload")
def upload_photo(title: str = Form(...), description: str = Form(""), file: UploadFile = File(...),
                 db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix or 'unknown'}")
    filename = f"{uuid.uuid4().hex}{suffix}"
    destination = UPLOAD_DIR / filename
    with destination.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    exif_make, exif_model = extract_exif(destination)
    photo = Photo(title=title, description=description or None, filename=filename, exif_make=exif_make, exif_model=exif_model)
    db.add(photo)
    db.commit()
    return RedirectResponse("/admin", status_code=303)

@router.post("/photos/{photo_id}/delete")
def delete_photo(photo_id: int, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    photo = db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    (UPLOAD_DIR / photo.filename).unlink(missing_ok=True)
    db.delete(photo)
    db.commit()
    return RedirectResponse("/admin", status_code=303)

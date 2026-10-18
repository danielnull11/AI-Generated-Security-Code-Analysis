from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import Photo
from views import templates

router = APIRouter(tags=["gallery"])

@router.get("/", response_class=HTMLResponse)
def gallery_index(request: Request, db: Session = Depends(get_db)):
    photos = db.scalars(select(Photo).order_by(Photo.created_at.desc())).all()
    return templates.TemplateResponse(request, "gallery.html", {"photos": photos})

@router.get("/photos/{photo_id}", response_class=HTMLResponse)
def photo_detail(photo_id: int, request: Request, db: Session = Depends(get_db)):
    photo = db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return templates.TemplateResponse(request, "photo.html", {"photo": photo})

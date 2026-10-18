from fastapi.templating import Jinja2Templates

from database import BASE_DIR

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

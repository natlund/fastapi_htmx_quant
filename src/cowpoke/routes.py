import os.path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from sqlmodel import SQLModel

from src.cowpoke.models import engine
from src.cowpoke.routes_bulls import router as bulls_router
from src.cowpoke.routes_farms import router as farms_router
from src.cowpoke.routes_jobs import router as jobs_router
from src.cowpoke.routes_technicians import router as technicians_router


templates = Jinja2Templates(directory="templates")
template_dir = "cowpoke"

router = APIRouter()
router.include_router(bulls_router)
router.include_router(technicians_router)
router.include_router(farms_router)
router.include_router(jobs_router)


@router.on_event("startup")
def on_startup():
    print("Doing startup")
    SQLModel.metadata.create_all(engine)


@router.get("/cowpoke", response_class=HTMLResponse)
async def cowpoke(request: Request):
    template_path = os.path.join(template_dir, "cowpoke_home.html")
    return templates.TemplateResponse(request=request, name=template_path)

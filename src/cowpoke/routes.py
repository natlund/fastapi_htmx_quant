import os.path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from sqlmodel import Field, Session, SQLModel, create_engine, select


class Technician(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)


sqlite_filename = "cowpoke.db"
sqlite_url = f"sqlite:///{sqlite_filename}"

connect_args = {"check_same_thread": False}
engine = create_engine(url=sqlite_url, connect_args=connect_args)

templates = Jinja2Templates(directory="templates")
template_dir = "cowpoke"

router = APIRouter()


@router.on_event("startup")
def on_startup():
    print("Doing startup")
    SQLModel.metadata.create_all(engine)


@router.get("/cowpoke", response_class=HTMLResponse)
async def cowpoke(request: Request):
    template_path = os.path.join(template_dir, "cowpoke_home.html")
    return templates.TemplateResponse(request=request, name=template_path)


@router.get("/cowpoke/technicians", response_class=HTMLResponse)
async def technicians(request: Request):
    template_path = os.path.join(template_dir, "technicians.html")
    return templates.TemplateResponse(request=request, name=template_path)


@router.get("/cowpoke/all-technicians", response_class=HTMLResponse)
async def all_technicians(request: Request):
    with Session(engine) as session:
        statement = select(Technician)
        records = session.exec(statement).all()

    context = {
        "table_caption": "AI Technicians",
        "column_names": ["id", "name"],  # Sets order explicitly.  Can also use dict(records[0]).keys()
        "table_data": [dict(record) for record in records],
    }
    template_path = os.path.join(template_dir, "db_table.html")
    return templates.TemplateResponse(request=request, name=template_path, context=context)



@router.post("/cowpoke/add-technician", response_class=HTMLResponse)
async def add_technician(request: Request):
    async with request.form() as form:  # form is a FormData object.
        techie = Technician(**form)

    with Session(engine) as session:
        session.add(techie)
        session.commit()

        statement = select(Technician)
        records = session.exec(statement).all()

    context = {
        "table_caption": "AI Technicians",
        "column_names": ["id", "name"],  # Sets order explicitly.  Can also use dict(records[0]).keys()
        "table_data": [dict(record) for record in records],
    }
    template_path = os.path.join(template_dir, "db_table.html")
    return templates.TemplateResponse(request=request, name=template_path, context=context)

import os.path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from sqlmodel import Session, col, select

from src.cowpoke.models import engine, Technician

templates = Jinja2Templates(directory="templates")
template_dir = "cowpoke"

router = APIRouter()


@router.get("/cowpoke/technicians", response_class=HTMLResponse)
async def technicians(request: Request):
    template_path = os.path.join(template_dir, "technicians.html")
    return templates.TemplateResponse(request=request, name=template_path)


@router.post("/cowpoke/search-technicians", response_class=HTMLResponse)
async def search_technicians(request: Request):
    async with request.form() as form:  # form is a FormData object.
        search_string = form["search_string"]

    with Session(engine) as session:
        statement = select(Technician).where(col(Technician.name).istartswith(search_string))
        records = session.exec(statement).all()

    return generate_technician_table(records=records)


@router.put("/cowpoke/add-technician", response_class=HTMLResponse)
async def add_technician(request: Request):
    async with request.form() as form:  # form is a FormData object.
        techie = Technician(**form)

    with Session(engine) as session:
        session.add(techie)
        session.commit()

        statement = select(Technician)
        records = session.exec(statement).all()

    return generate_technician_table(records=records)


@router.get("/cowpoke/all-technicians", response_class=HTMLResponse)
async def all_technicians(request: Request):
    with Session(engine) as session:
        statement = select(Technician)
        records = session.exec(statement).all()

    return generate_technician_table(records=records)


@router.get("/cowpoke/technician/{technician_id}", response_class=HTMLResponse)
async def technician(technician_id):
    with Session(engine) as session:
        statement = select(Technician).where(Technician.id == technician_id)
        record = session.exec(statement).one()

    context = {"record": record}
    template_path = os.path.join(template_dir, "technician_view.html")
    return templates.TemplateResponse(request={}, name=template_path, context=context)


@router.post("/cowpoke/edit-technician", response_class=HTMLResponse)
async def technician_edit(request: Request):
    async with request.form() as form:  # form is a FormData object.
        edited_techie = Technician(**form)

    with Session(engine) as session:
        statement = select(Technician).where(Technician.id == edited_techie.id)
        techie = session.exec(statement).one()

        techie.name = edited_techie.name
        techie.full_name = edited_techie.full_name
        techie.phone = edited_techie.phone
        techie.email = edited_techie.email
        techie.postcode = edited_techie.postcode
        techie.address = edited_techie.address

        session.add(techie)
        session.commit()
        session.refresh(techie)

    context = {"record": techie}
    template_path = os.path.join(template_dir, "technician_box.html")
    return templates.TemplateResponse(request={}, name=template_path, context=context)


@router.delete("/cowpoke/technician/{technician_id}", response_class=HTMLResponse)
async def technician_delete(technician_id):
    with Session(engine) as session:
        statement = select(Technician).where(Technician.id == technician_id)
        result = session.exec(statement)
        technician_to_delete = result.one()
        session.delete(technician_to_delete)
        session.commit()

    html = """
    <div id="technician_box" hx-get="/cowpoke/all-technicians" hx-target="#technician_table" hx-trigger="load">
        <div style="color: red; display: flex; align-items: center; justify-content: center; font-weight: bold;">
        DELETED
        </div>
    </div>
    """
    return HTMLResponse(html)


def generate_technician_table(records: list) -> templates.TemplateResponse:
    context = {
        "table_caption": "AI Technicians",
        "column_names": ["id", "name", "phone", "email", "postcode"],  # Can also use dict(records[0]).keys()
        "table_data": [dict(record) for record in records],
        "hxget_stub": "/cowpoke/technician/",
        "hxtarget": "#technician_view",
        "tabIDtoselect": "tab3"
    }
    template_path = os.path.join(template_dir, "db_table.html")
    return templates.TemplateResponse(request={}, name=template_path, context=context)

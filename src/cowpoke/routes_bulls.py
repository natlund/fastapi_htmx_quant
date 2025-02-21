import os.path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from sqlmodel import Session, col, select

from src.cowpoke.models import engine, Bull


templates = Jinja2Templates(directory="templates")
template_dir = "cowpoke"

router = APIRouter()


@router.get("/cowpoke/bulls", response_class=HTMLResponse)
async def bulls(request: Request):
    template_path = os.path.join(template_dir, "bulls.html")
    return templates.TemplateResponse(request=request, name=template_path)


@router.post("/cowpoke/search-bulls", response_class=HTMLResponse)
async def search_bulls(request: Request):
    async with request.form() as form:  # form is a FormData object.
        search_string = form["search_string"]

    with Session(engine) as session:
        statement = select(Bull).where(col(Bull.bull_code).istartswith(search_string))
        records = session.exec(statement).all()

    return generate_bull_table(records=records)


@router.put("/cowpoke/add-bull", response_class=HTMLResponse)
async def add_bull(request: Request):
    async with request.form() as form:  # form is a FormData object.
        bull = Bull(**form)

    with Session(engine) as session:
        session.add(bull)
        session.commit()

        statement = select(Bull)
        records = session.exec(statement).all()

    return generate_bull_table(records=records)


@router.get("/cowpoke/all-bulls", response_class=HTMLResponse)
async def all_bulls(request: Request):
    with Session(engine) as session:
        statement = select(Bull)
        records = session.exec(statement).all()

    return generate_bull_table(records=records)


@router.get("/cowpoke/bull/{bull_id}", response_class=HTMLResponse)
async def bull(bull_id):
    with Session(engine) as session:
        statement = select(Bull).where(Bull.id == bull_id)
        record = session.exec(statement).one()

    context = {"record": record}
    template_path = os.path.join(template_dir, "bull_view.html")
    return templates.TemplateResponse(request={}, name=template_path, context=context)


@router.post("/cowpoke/edit-bull", response_class=HTMLResponse)
async def bull_edit(request: Request):
    async with request.form() as form:  # form is a FormData object.
        edited_bull = Bull(**form)

    with Session(engine) as session:
        statement = select(Bull).where(Bull.id == edited_bull.id)
        bull = session.exec(statement).one()

        bull.bull_code = edited_bull.bull_code
        bull.bull_name = edited_bull.bull_name
        bull.notes = edited_bull.notes

        session.add(bull)
        session.commit()
        session.refresh(bull)

    context = {"record": edited_bull}
    template_path = os.path.join(template_dir, "bull_view.html")
    return templates.TemplateResponse(request={}, name=template_path, context=context)


@router.delete("/cowpoke/bull/{bull_id}", response_class=HTMLResponse)
async def bull_delete(bull_id):
    with Session(engine) as session:
        statement = select(Bull).where(Bull.id == bull_id)
        result = session.exec(statement)
        bull_to_delete = result.one()
        session.delete(bull_to_delete)
        session.commit()

    html = """
    <div id="bull_box" hx-get="/cowpoke/all-bulls" hx-target="#bull_table" hx-trigger="load">
        <div style="color: red; display: flex; align-items: center; justify-content: center; font-weight: bold;">
        DELETED
        </div>
    </div>
    """
    return HTMLResponse(html)


def generate_bull_table(records: list) -> templates.TemplateResponse:
    context = {
        "table_caption": "Bulls",
        "column_names": ["id", "bull_code", "bull_name", "notes"],  # Can also use dict(records[0]).keys()
        "table_data": [dict(record) for record in records],
        "hxget_stub": "/cowpoke/bull/",
        "hxtarget": "#bull_view",
        "tabIDtoselect": "tab3",
    }
    template_path = os.path.join(template_dir, "db_table_clickable.html")
    return templates.TemplateResponse(request={}, name=template_path, context=context)

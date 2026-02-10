from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from sqlmodel import Session, col, select

from src.cowpoke.database_connection import engine
from src.cowpoke.models import Bull, Farm, Insemination, Job, Technician


templates = Jinja2Templates(directory=["cowpoke/templates", "templates"])

router = APIRouter()


@router.get("/cowpoke/bulls", response_class=HTMLResponse)
async def bulls(request: Request):
    return templates.TemplateResponse(request=request, name="bulls.html")


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
    return templates.TemplateResponse(request={}, name="bull_view.html", context=context)


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
    return templates.TemplateResponse(request={}, name="bull_view.html", context=context)


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


@router.get("/cowpoke/farms-for-bull/{bull_id}", response_class=HTMLResponse)
async def farms_for_bull(bull_id):

    with Session(engine) as session:
        bull_statement = select(Bull).where(Bull.id == bull_id)
        bull = session.exec(bull_statement).one()

        statement = (select(Farm).join(Job).join(Insemination)
                     .where(Insemination.bull_id == bull_id)
                     .group_by(Farm.id))
        farm_records = session.exec(statement).all()

    context = {
        "table_caption": f"Farms That Have Used Bull {bull.bull_code}",
        "column_names": ["name", "business_name", "contact_person", "postcode"],
        "table_data": [dict(record) for record in farm_records]
    }
    return templates.TemplateResponse(request={}, name="db_table.html", context=context)


@router.get("/cowpoke/technicians-for-bull/{bull_id}", response_class=HTMLResponse)
async def technicians_for_bull(bull_id):

    with Session(engine) as session:
        bull_statement = select(Bull).where(Bull.id == bull_id)
        bull = session.exec(bull_statement).one()

        statement = (select(Technician).join(Job).join(Insemination)
                     .where(Insemination.bull_id == bull_id)
                     .group_by(Technician.id))
        technician_records = session.exec(statement).all()

    context = {
        "table_caption": f"Technicians That Have Inseminated With Bull {bull.bull_code}",
        "column_names": ["name", "phone", "email", "postcode"],
        "table_data": [dict(record) for record in technician_records]
    }
    return templates.TemplateResponse(request={}, name="db_table.html", context=context)


def generate_bull_table(records: list) -> templates.TemplateResponse:
    context = {
        "table_caption": "Bulls",
        "column_names": ["id", "bull_code", "bull_name", "notes"],  # Can also use dict(records[0]).keys()
        "table_data": [dict(record) for record in records],
        "hxget_stub": "/cowpoke/bull/",
        "hxtarget": "#bull_view",
        "tabIDtoselect": "tab3",
    }
    return templates.TemplateResponse(request={}, name="db_table_clickable.html", context=context)

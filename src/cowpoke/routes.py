import os.path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from sqlmodel import Session, SQLModel, col, create_engine, or_, select

from src.cowpoke.models import Cow, Bull, Farm, Technician


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


########################################################################################################################


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


########################################################################################################################


@router.get("/cowpoke/farms", response_class=HTMLResponse)
async def farms(request: Request):
    template_path = os.path.join(template_dir, "farms.html")
    return templates.TemplateResponse(request=request, name=template_path)


@router.post("/cowpoke/search-farms", response_class=HTMLResponse)
async def search_farms(request: Request):
    async with request.form() as form:  # form is a FormData object.
        search_string = form["search_string"]

    with Session(engine) as session:
        statement = select(Farm).where(col(Farm.name).istartswith(search_string))
        records = session.exec(statement).all()

    return generate_farm_table(records=records)


@router.put("/cowpoke/add-farm", response_class=HTMLResponse)
async def add_farm(request: Request):
    async with request.form() as form:  # form is a FormData object.
        farm = Farm(**form)

    with Session(engine) as session:
        session.add(farm)
        session.commit()

        statement = select(Farm)
        records = session.exec(statement).all()

    return generate_farm_table(records=records)


@router.get("/cowpoke/all-farms", response_class=HTMLResponse)
async def all_farms(request: Request):
    with Session(engine) as session:
        statement = select(Farm)
        records = session.exec(statement).all()

    return generate_farm_table(records=records)


@router.get("/cowpoke/farm/{farm_id}", response_class=HTMLResponse)
async def farm(farm_id):
    with Session(engine) as session:
        statement = select(Farm).where(Farm.id == farm_id)
        record = session.exec(statement).one()

    context = {"record": record}
    template_path = os.path.join(template_dir, "farm_view.html")
    return templates.TemplateResponse(request={}, name=template_path, context=context)


@router.post("/cowpoke/edit-farm", response_class=HTMLResponse)
async def farm_edit(request: Request):
    async with request.form() as form:  # form is a FormData object.
        edited_farm = Farm(**form)

    with Session(engine) as session:
        statement = select(Farm).where(Farm.id == edited_farm.id)
        farm = session.exec(statement).one()

        farm.name = edited_farm.name
        farm.business_name = edited_farm.business_name
        farm.postcode = edited_farm.postcode
        farm.coordinates = edited_farm.coordinates
        farm.address = edited_farm.address
        farm.contact_person = edited_farm.contact_person

        session.add(farm)
        session.commit()
        session.refresh(farm)

    context = {"record": edited_farm}
    template_path = os.path.join(template_dir, "farm_view.html")
    return templates.TemplateResponse(request={}, name=template_path, context=context)


@router.delete("/cowpoke/farm/{farm_id}", response_class=HTMLResponse)
async def farm_delete(farm_id):
    with Session(engine) as session:
        statement = select(Farm).where(Farm.id == farm_id)
        result = session.exec(statement)
        farm_to_delete = result.one()
        session.delete(farm_to_delete)
        session.commit()

    html = """
    <div id="farm_box" hx-get="/cowpoke/all-farms" hx-target="#farm_table" hx-trigger="load">
        <div style="color: red; display: flex; align-items: center; justify-content: center; font-weight: bold;">
        DELETED
        </div>
    </div>
    """
    return HTMLResponse(html)


def generate_farm_table(records: list) -> templates.TemplateResponse:
    context = {
        "table_caption": "Farms",
        "column_names": ["id", "name", "business_name", "contact_person", "postcode"],  # Can also use dict(records[0]).keys()
        "table_data": [dict(record) for record in records],
        "hxget_stub": "/cowpoke/farm/",
        "hxtarget": "#farm_view",
        "tabIDtoselect": "tab3",
    }
    template_path = os.path.join(template_dir, "db_table.html")
    return templates.TemplateResponse(request={}, name=template_path, context=context)


########################################################################################################################


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
    template_path = os.path.join(template_dir, "db_table.html")
    return templates.TemplateResponse(request={}, name=template_path, context=context)


########################################################################################################################


@router.post("/cowpoke/search-cows", response_class=HTMLResponse)
async def search_cows(request: Request):
    async with request.form() as form:  # form is a FormData object.
        search_string = form.get("search_string", "")
        farm_id = form.get("farm_id")

    with Session(engine) as session:
        statement = (select(Cow).where(Cow.farm_id == farm_id)
                                .where(or_(col(Cow.tag_id).istartswith(search_string),
                                           col(Cow.description).istartswith(search_string)
                                           )
                                       )
                     )
        records = session.exec(statement).all()

    return generate_cow_table(records=records)


@router.get("/cowpoke/all-cows-for-farm/{farm_id}", response_class=HTMLResponse)
async def all_cows_for_farm(farm_id: int):
    with Session(engine) as session:
        statement = select(Cow).where(Cow.farm_id == farm_id)
        records = session.exec(statement).all()

    return generate_cow_table(records=records)


@router.put("/cowpoke/add-cow", response_class=HTMLResponse)
async def add_cow(request: Request):
    async with request.form() as form:  # form is a FormData object.
        cow = Cow(**form)

    with Session(engine) as session:
        session.add(cow)
        session.commit()

        statement = select(Cow).where(col(Cow.farm_id) == cow.farm_id)
        records = session.exec(statement).all()

    return generate_cow_table(records=records)


@router.get("/cowpoke/cow/{cow_id}", response_class=HTMLResponse)
async def cow(cow_id):
    with Session(engine) as session:
        statement = select(Cow).where(Cow.id == cow_id)
        record = session.exec(statement).one()

    context = {"record": record}
    template_path = os.path.join(template_dir, "cow_box.html")
    return templates.TemplateResponse(request={}, name=template_path, context=context)


@router.get("/cowpoke/close-cow", response_class=HTMLResponse)
async def close_cow(request: Request):
    html = """<div id="cow_box"></div>"""
    return HTMLResponse(html)


@router.post("/cowpoke/edit-cow", response_class=HTMLResponse)
async def cow_edit(request: Request):
    async with request.form() as form:  # form is a FormData object.
        edited_cow = Cow(**form)

    with Session(engine) as session:
        statement = select(Cow).where(Cow.id == edited_cow.id)
        cow = session.exec(statement).one()

        cow.tag_id = edited_cow.tag_id
        cow.description = edited_cow.description

        session.add(cow)
        session.commit()
        session.refresh(cow)

    context = {"record": edited_cow}
    template_path = os.path.join(template_dir, "cow_box.html")
    return templates.TemplateResponse(request={}, name=template_path, context=context)


@router.delete("/cowpoke/cow/{cow_id}", response_class=HTMLResponse)
async def cow_delete(cow_id):
    with Session(engine) as session:
        statement = select(Cow).where(Cow.id == cow_id)
        result = session.exec(statement)
        cow_to_delete = result.one()
        farm_id = cow_to_delete.farm_id

        session.delete(cow_to_delete)
        session.commit()

    html = f"""
    <div id="cow_box" hx-get="/cowpoke/all-cows-for-farm/{farm_id}" hx-target="#cow_table" hx-trigger="load"></div>
    """
    return HTMLResponse(html)


def generate_cow_table(records: list) -> templates.TemplateResponse:
    context = {
        "table_caption": "Cows",
        "column_names": ["id", "tag_id", "description", "farm_id"],  # Can also use dict(records[0]).keys()
        "table_data": [dict(record) for record in records],
        "hxget_stub": "/cowpoke/cow/",
        "hxtarget": "#cow_box",
        "tabIDtoselect": "tab12",
    }
    template_path = os.path.join(template_dir, "db_table.html")
    return templates.TemplateResponse(request={}, name=template_path, context=context)

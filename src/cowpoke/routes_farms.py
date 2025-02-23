import os.path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from sqlmodel import Session, col, or_, select

from src.cowpoke.models import engine, Bull, Cow, Farm, Insemination, Job, Technician


templates = Jinja2Templates(directory="templates")
template_dir = "cowpoke"

router = APIRouter()


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
    template_path = os.path.join(template_dir, "db_table_clickable.html")
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
    template_path = os.path.join(template_dir, "db_table_clickable.html")
    return templates.TemplateResponse(request={}, name=template_path, context=context)


########################################################################################################################


@router.get("/cowpoke/technicians-for-farm/{farm_id}", response_class=HTMLResponse)
async def technicians_for_farm(farm_id):
    with Session(engine) as session:
        farm_statement = select(Farm).where(Farm.id == farm_id)
        farm = session.exec(farm_statement).one()

        statement = (select(Technician).join(Insemination).join(Job).join(Farm)
                     .where(Farm.id == farm_id)
                     .group_by(Technician.id))

        technicians = session.exec(statement).all()

    context = {
        "table_caption": f"Technicians that have worked on farm {farm.name}",
        "column_names": ["id", "name", "phone", "email", "postcode"],
        "table_data": [dict(record) for record in technicians],
    }
    template_path = os.path.join(template_dir, "db_table.html")
    return templates.TemplateResponse(request={}, name=template_path, context=context)


@router.get("/cowpoke/bulls-for-farm/{farm_id}", response_class=HTMLResponse)
async def bulls_for_farm(farm_id):
    with Session(engine) as session:
        farm_statement = select(Farm).where(Farm.id == farm_id)
        farm = session.exec(farm_statement).one()

        statement = (select(Bull).join(Insemination).join(Job).join(Farm)
                     .where(Farm.id == farm_id)
                     .group_by(Bull.id))

        bulls = session.exec(statement).all()

    context = {
        "table_caption": f"Bulls that have been used on farm {farm.name}",
        "column_names": ["bull_code", "bull_name", "notes"],
        "table_data": [dict(record) for record in bulls],
    }
    template_path = os.path.join(template_dir, "db_table.html")
    return templates.TemplateResponse(request={}, name=template_path, context=context)


@router.get("/cowpoke/jobs-for-farm/{farm_id}", response_class=HTMLResponse)
async def jobs_for_farm(farm_id):
    with Session(engine) as session:
        farm_statement = select(Farm).where(Farm.id == farm_id)
        farm = session.exec(farm_statement).one()

        statement = select(Job, Technician).join(Technician).where(Job.farm_id == farm_id)
        records = session.exec(statement).all()

    rows = []
    for job, tech in records:
        rows.append({
            "id": job.id,
            "job_date": job.job_date,
            "lead_technician": tech.name,
            "notes": job.notes,
        })

    rows.sort(key=lambda x: x["job_date"], reverse=True)

    context = {
        "table_caption": f"AI Jobs on farm {farm.name}",
        "column_names": ["id", "job_date", "lead_technician", "notes"],
        "table_data": rows,
    }
    print(rows)
    template_path = os.path.join(template_dir, "db_table.html")
    return templates.TemplateResponse(request={}, name=template_path, context=context)


@router.get("/cowpoke/inseminations-for-farm/{farm_id}", response_class=HTMLResponse)
async def inseminations_for_farm(farm_id):
    with Session(engine) as session:
        farm_statement = select(Farm).where(Farm.id == farm_id)
        farm = session.exec(farm_statement).one()

        statement = (select(Insemination, Cow, Bull, Job, Technician)
                     .join(Cow).join(Bull).join(Technician, Insemination.technician_id == Technician.id).join(Job)
                     .where(Job.farm_id == farm_id))
        records = session.exec(statement).all()

    rows = []
    for insemination, cow, bull, job, tech in records:
        rows.append({
            "job_date": job.job_date,
            "cow_tag_id": cow.tag_id,
            "status": insemination.status,
            "days": insemination.days_since_last_insemination,
            "bull_code": bull.bull_code,
            "tech": tech.name,
        })

    rows.sort(key=lambda x: x["job_date"], reverse=True)

    context = {
        "table_caption": f"Inseminations on farm {farm.name}",
        "column_names": ["job_date", "cow_tag_id", "status", "days", "bull_code", "tech"],
        "table_data": rows,
    }
    template_path = os.path.join(template_dir, "db_table.html")
    return templates.TemplateResponse(request={}, name=template_path, context=context)

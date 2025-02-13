import datetime
import os.path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel
from sqlmodel import Session, SQLModel, col, create_engine, or_, select

from src.cowpoke.models import Bull, PlannedInsemination, Cow, Farm, Insemination, Job, Technician


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


########################################################################################################################


@router.get("/cowpoke/jobs", response_class=HTMLResponse)
async def jobs(request: Request):

    with Session(engine) as session:
        farms_stmt = select(Farm)
        farm_records = session.exec(farms_stmt).all()

        techs_stmt = select(Technician)
        tech_records = session.exec(techs_stmt).all()

    context = {
        "farms": [{"id": record.id, "name": record.name} for record in farm_records],
        "technicians": [{"id": record.id, "name": record.name} for record in tech_records],
    }
    template_path = os.path.join(template_dir, "jobs.html")
    return templates.TemplateResponse(request=request, name=template_path, context=context)


class JobPydantic(BaseModel):
    job_date: datetime.date
    farm_id: int
    lead_technician_id: int
    notes: str


@router.put("/cowpoke/add-job", response_class=HTMLResponse)
async def add_job(request: Request):
    async with request.form() as form:  # form is a FormData object.
        job_pydantic = JobPydantic(**form)  # Use pydantic to automatically convert string to datetime.date
        job = Job(
            job_date = job_pydantic.job_date,
            farm_id = job_pydantic.farm_id,
            lead_technician_id = job_pydantic.lead_technician_id,
            notes = job_pydantic.notes,
        )

    with Session(engine) as session:
        session.add(job)
        session.commit()

        statement = select(Job, Farm, Technician).join(Farm).join(Technician)
        records = session.exec(statement).all()

    return generate_job_table(records=records)


@router.get("/cowpoke/all-jobs", response_class=HTMLResponse)
async def all_jobs(request: Request):
    with Session(engine) as session:
        statement = select(Job, Farm, Technician).join(Farm).join(Technician)
        records = session.exec(statement).all()

    return generate_job_table(records=records)


@router.post("/cowpoke/search-jobs-by-date", response_class=HTMLResponse)
async def search_jobs_by_date(request: Request):
    async with request.form() as form:  # form is a FormData object.
        job_date = form.get("job_date")

    with Session(engine) as session:
        statement = select(Job, Farm, Technician).join(Farm).join(Technician).where(Job.job_date == job_date)
        records = session.exec(statement).all()

    return generate_job_table(records=records)


@router.post("/cowpoke/search-jobs-by-farm", response_class=HTMLResponse)
async def search_jobs_by_farm(request: Request):
    async with request.form() as form:  # form is a FormData object.
        farm_id = form.get("farm_id")

    with Session(engine) as session:
        statement = select(Job, Farm, Technician).join(Farm).join(Technician).where(Job.farm_id == farm_id)
        records = session.exec(statement).all()

    return generate_job_table(records=records)


@router.post("/cowpoke/search-jobs-by-technician", response_class=HTMLResponse)
async def search_jobs_by_technician(request: Request):
    async with request.form() as form:  # form is a FormData object.
        lead_tech_id = form.get("lead_technician_id")

    with Session(engine) as session:
        statement = (select(Job, Farm, Technician).join(Farm).join(Technician)
                     .where(Job.lead_technician_id == lead_tech_id))
        records = session.exec(statement).all()

    return generate_job_table(records=records)


@router.get("/cowpoke/job/{job_id}", response_class=HTMLResponse)
async def job_view(job_id):
    with Session(engine) as session:
        techs_stmt = select(Technician)
        tech_records = session.exec(techs_stmt).all()

        bulls_stmt = select(Bull)
        bull_records = session.exec(bulls_stmt).all()

        statement = select(Job, Farm, Technician).join(Farm).join(Technician).where(Job.id == job_id)
        job, farm, technician = session.exec(statement).one()

        cows_stmt = select(Cow).where(Cow.farm_id == job.farm_id)
        cow_records = session.exec(cows_stmt).all()

    context = {
        "technicians": [{"id": record.id, "name": record.name} for record in tech_records],
        "bulls": [{"id": bull.id, "code": bull.bull_code} for bull in bull_records],
        "cows": [{"id": cow.id, "tag_id": cow.tag_id, "description": cow.description} for cow in cow_records],
        "job_data": {
            "job_id": job.id,
            "job_date": job.job_date,
            "farm_id": job.farm_id,
            "farm": farm.name,
            "lead_technician_id": job.lead_technician_id,
            "lead_technician": technician.name,
        }
    }
    template_path = os.path.join(template_dir, "job_view.html")
    return templates.TemplateResponse(request={}, name=template_path, context=context)


class PlannedInseminationForm(BaseModel):
    job_id: int
    farm_id: int
    technician_id: int
    bull_id: int
    cow_id: int
    new_cow_tag_id: str


@router.put("/cowpoke/add-planned-insemination", response_class=HTMLResponse)
async def add_planned_insemination(request: Request):
    async with request.form() as form:  # form is a FormData object.
        planned_insem = PlannedInseminationForm(**form)

    print(planned_insem)
    if planned_insem.new_cow_tag_id == "":
        cow_id = planned_insem.cow_id

    else:  # Insert new cow first.
        new_cow = Cow(
            farm_id = planned_insem.farm_id,
            tag_id = planned_insem.new_cow_tag_id,
            description = ""
        )
        with Session(engine) as session:
            session.add(new_cow)
            session.commit()
            session.refresh(new_cow)
            cow_id = new_cow.id

    planned_insemination = PlannedInsemination(
        job_id = planned_insem.job_id,
        technician_id = planned_insem.technician_id,
        bull_id = planned_insem.bull_id,
        cow_id = cow_id,
    )
    with Session(engine) as session:
        session.add(planned_insemination)
        session.commit()

    return generate_inseminations(job_id=planned_insem.job_id)


@router.get("/cowpoke/inseminations/{job_id}", response_class=HTMLResponse)
async def get_inseminations_for_job_id(job_id):
    return generate_inseminations(job_id=job_id)


@router.put("/cowpoke/complete-planned-insemination/{planned_insemination_id}", response_class=HTMLResponse)
async def complete_planned_insemination(planned_insemination_id: int):
    with Session(engine) as session:
        statement = select(PlannedInsemination).where(PlannedInsemination.id == planned_insemination_id)
        planned_insemination = session.exec(statement).one()

        insemination = Insemination(
            job_id = planned_insemination.job_id,
            technician_id = planned_insemination.technician_id,
            bull_id = planned_insemination.bull_id,
            cow_id = planned_insemination.cow_id,
        )
        session.add(insemination)
        session.delete(planned_insemination)
        session.commit()
        session.refresh(insemination)

    return generate_inseminations(job_id=insemination.job_id)


@router.delete("/cowpoke/delete-planned-insemination/{planned_insemination_id}", response_class=HTMLResponse)
async def delete_planned_insemination(planned_insemination_id: int):
    with Session(engine) as session:
        statement = select(PlannedInsemination).where(PlannedInsemination.id == planned_insemination_id)
        planned_insemination = session.exec(statement).one()
        job_id = planned_insemination.job_id

        session.delete(planned_insemination)
        session.commit()

    return generate_inseminations(job_id=job_id)


def generate_inseminations(job_id: int):
    with Session(engine) as session:
        planned_insem_stmt = (select(PlannedInsemination, Cow, Bull, Technician).join(Cow).join(Bull).join(Technician)
                              .where(PlannedInsemination.job_id == job_id))
        planned_insem_records = session.exec(planned_insem_stmt).all()

        insem_stmt = (select(Insemination, Cow, Bull, Technician).join(Cow).join(Bull).join(Technician)
                      .where(Insemination.job_id == job_id))
        insemination_records = session.exec(insem_stmt).all()

    planned_inseminations = [
        {
            "cow_tag_id": cow.tag_id,
            "status": "Normal",
            "bull_code": bull.bull_code,
            "technician": tech.name,
            "tech_id": tech.id,
            "id": pi.id,
        }
        for pi, cow, bull, tech in planned_insem_records
    ]

    inseminations = [
        {
            "cow_tag_id": cow.tag_id,
            "status": "Normal",
            "bull_code": bull.bull_code,
            "technician": tech.name,
            "tech_id": tech.id,
            "id" : insem.id,
        }
        for insem, cow, bull, tech in insemination_records
    ]

    context = {
        "column_names": ["cow_tag_id", "status", "bull_code", "technician", "tech_id"],
        "planned_inseminations": planned_inseminations,
        "inseminations": inseminations,
    }
    template_path = os.path.join(template_dir, "inseminations.html")
    return templates.TemplateResponse(request={}, name=template_path, context=context)


def generate_job_table(records: list) -> templates.TemplateResponse:
    rows = []
    for job, farm, tech in records:
        rows.append({
            "id": job.id,
            "job_date": job.job_date,
            "farm": farm.name,
            "lead_tech": tech.name,
            "notes": job.notes,
        })

    rows.sort(key=lambda x: x["job_date"], reverse=True)

    context = {
        "table_caption": "AI Jobs",
        "column_names": ["id", "job_date", "farm", "lead_tech", "notes"],
        "table_data": rows,
        "hxget_stub": "/cowpoke/job/",
        "hxtarget": "#job_view",
        "tabIDtoselect": "tab3",
    }
    template_path = os.path.join(template_dir, "db_table.html")
    return templates.TemplateResponse(request={}, name=template_path, context=context)

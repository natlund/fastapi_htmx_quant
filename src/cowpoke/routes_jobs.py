import datetime
from enum import Enum
import os.path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel
from sqlmodel import Session, select

from src.cowpoke.database_connection import engine
from src.cowpoke.models import Bull, Cow, Farm, Insemination, Job, PlannedInsemination, Technician


templates = Jinja2Templates(directory="templates")
template_dir = "cowpoke"

router = APIRouter()


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
    job_date: datetime.date
    farm_id: int
    technician_id: int
    bull_id: int
    cow_id: int
    new_cow_tag_id: str


class ReturnStatus(Enum):
    first_recorded = "First Recorded"
    first_of_season = "First Of Season"
    short_return = "Short Return"
    normal = "Normal"
    long_return = "Long Return"


@router.put("/cowpoke/add-planned-insemination", response_class=HTMLResponse)
async def add_planned_insemination(request: Request):
    async with request.form() as form:  # form is a FormData object.
        planned_insem = PlannedInseminationForm(**form)

    if planned_insem.new_cow_tag_id == "":
        cow_id = planned_insem.cow_id

        status, days_since_last_insemination = calculate_return_status(
            job_date=planned_insem.job_date,
            cow_id=planned_insem.cow_id,
        )

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

        status = ReturnStatus.first_recorded.value
        days_since_last_insemination = None

    planned_insemination = PlannedInsemination(
        job_id = planned_insem.job_id,
        technician_id = planned_insem.technician_id,
        bull_id = planned_insem.bull_id,
        cow_id = cow_id,
        days_since_last_insemination = days_since_last_insemination,
        status = status,
    )
    with Session(engine) as session:
        session.add(planned_insemination)
        session.commit()

    return generate_inseminations(job_id=planned_insem.job_id)


def calculate_return_status(job_date: datetime.date, cow_id: int) -> tuple:
    with Session(engine) as session:
        statement = (select(Job).join(Insemination)
                     .where(Insemination.cow_id == cow_id))
        records = session.exec(statement).all()

    if not records:
        return ReturnStatus.first_recorded.value, None

    insemination_dates = [job.job_date for job in records]
    insemination_dates.sort(reverse=True)
    most_recent_insemination = insemination_dates[0]

    days_since_last_insemination = (job_date - most_recent_insemination).days

    if days_since_last_insemination < 24:
        status = ReturnStatus.short_return.value
    elif 24 <= days_since_last_insemination <= 28:
        status = ReturnStatus.normal.value
    elif 28 < days_since_last_insemination < 180:
        status = ReturnStatus.long_return.value
    else:  # 180 < days_since_last_insemination:
        status = ReturnStatus.first_of_season.value

    return status, days_since_last_insemination


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
            days_since_last_insemination = planned_insemination.days_since_last_insemination,
            status = planned_insemination.status,
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
            "status": pi.status,
            "days": pi.days_since_last_insemination,
            "bull_code": bull.bull_code,
            "technician": tech.name,
            "id": pi.id,
        }
        for pi, cow, bull, tech in planned_insem_records
    ]

    inseminations = [
        {
            "cow_tag_id": cow.tag_id,
            "status": insem.status,
            "days": insem.days_since_last_insemination,
            "bull_code": bull.bull_code,
            "technician": tech.name,
            "tech_id": tech.id,
            "id" : insem.id,
        }
        for insem, cow, bull, tech in insemination_records
    ]

    context = {
        "column_names": ["cow_tag_id", "status", "days", "bull_code", "technician"],
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
    template_path = os.path.join(template_dir, "db_table_clickable.html")
    return templates.TemplateResponse(request={}, name=template_path, context=context)

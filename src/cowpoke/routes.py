import os.path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from sqlmodel import select, Session

from src.cowpoke import models
from src.cowpoke.database_connection import engine
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
    models.SQLModel.metadata.create_all(engine)
    insert_example_data_if_db_empty()


@router.get("/cowpoke", response_class=HTMLResponse)
async def cowpoke(request: Request):
    template_path = os.path.join(template_dir, "cowpoke_home.html")
    return templates.TemplateResponse(request=request, name=template_path)


def insert_example_data_if_db_empty():
    """
    Insert example data if the relevant tables are empty.
    """
    with Session(engine) as session:
        bull_exists = session.exec(select(models.Bull)).first()

        if not bull_exists:
            bull_1 = models.Bull(
                bull_code="BMF123",
                bull_name="Breaker 1-9",
                notes="Ornery Friesian bastard."
            )
            bull_2 = models.Bull(
                bull_code="BMF124",
                bull_name="Bodacious",
                notes="Most dangerous bull in '90s rodeo circuit."
            )
            session.add(bull_1)
            session.add(bull_2)
            session.commit()

        technician_exists = session.exec(select(models.Technician)).first()

        if not technician_exists:
            tech_1 = models.Technician(
                name="Hemi",
                full_name="Joseph Bloggs",
                phone="074 1234 5678",
                email="joebloggs@gmail.com",
                postcode="LL11 6JB",
                address="123 Main Street, Wrectam"
            )
            tech_2 = models.Technician(
                name="Larry",
                full_name="Lawrence Dickman",
                phone="074 8765 4321",
                email="larrydickman@gmail.com",
                postcode="LL11 7KC",
                address="45 Station Road, Wrectam"
            )
            tech_3 = models.Technician(
                name="Bob",
                full_name="Robert Dobalina",
                phone="074 4321 8765",
                email="misterbobdobalina@gmail.com",
                postcode="LL11 8LD",
                address="17 King Street, Wrectam"
            )
            session.add(tech_1)
            session.add(tech_2)
            session.add(tech_3)
            session.commit()

        farm_exists = session.exec(select(models.Farm)).first()

        if not farm_exists:
            farm_1 = models.Farm(
                name="Old MacDonald's",
                business_name="McD's Ltd",
                postcode="6UL DV8",
                coordinates="12.345 67.890",
                address="Second gate on left after the black stump",
                contact_person="Farmer Joe",
            )
            farm_2 = models.Farm(
                name="Clampett's",
                business_name="J. D. Clampett Ltd",
                postcode="6UL EU9",
                coordinates="12.345 67.890",
                address="Copperhead Road, Tennessee",
                contact_person="Jed",
            )
            farm_3 = models.Farm(
                name="O'Reilly's",
                business_name="A. J. O'Reilly Ltd",
                postcode="6UL FV1",
                coordinates="12.345 67.890",
                address="First on right after first gully on Table Flat Road",
                contact_person="Tony O'Reilly",
            )
            session.add(farm_1)
            session.add(farm_2)
            session.add(farm_3)
            session.commit()

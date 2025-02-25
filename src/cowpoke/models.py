from datetime import date

from sqlmodel import Field, SQLModel


class Bull(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    bull_code: str = Field(index=True)
    bull_name: str
    notes: str


class Technician(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    full_name: str
    phone: int
    email: str
    postcode: str
    address: str


class Farm(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    business_name: str
    postcode: str
    coordinates: str
    address: str
    contact_person: str


class Cow(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    farm_id: int = Field(foreign_key="farm.id")
    tag_id: str = Field(index=True)
    description: str


class Job(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    job_date: date
    farm_id: int = Field(foreign_key="farm.id")
    lead_technician_id: int = Field(foreign_key="technician.id")
    notes: str


class PlannedInsemination(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.id")
    technician_id: int = Field(foreign_key="technician.id")
    bull_id: int = Field(foreign_key="bull.id")
    cow_id: int = Field(foreign_key="cow.id")
    days_since_last_insemination: int | None
    status: str


class Insemination(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.id")
    technician_id: int = Field(foreign_key="technician.id")
    bull_id: int = Field(foreign_key="bull.id")
    cow_id: int = Field(foreign_key="cow.id")
    days_since_last_insemination: int | None
    status: str

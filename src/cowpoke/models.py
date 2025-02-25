from datetime import date

from sqlmodel import Field, SQLModel
"""
The SQLModel base class has a class attribute 'metadata'.
When a class inheriting from SQLModel is created (eg. Bull), it is registered in SQLModel.metadata
SQLModel.metadata can then be used to programmatically create the tables in the database.
Eg:
    SQLModel.metadata.create_all(engine)

Note that the model classes must be created *before* SLQModel.metadata is used to create tables in the database.
(Otherwise, the models will not be registered in SQLModel.metadata.)
In practice, this means that this 'models.py' file must be imported before SQLModel.metadata is used.
To guarantee that SQLModel.metadata is correctly populated, import SQLModel *from* this file 'models.py'.
Eg:
    from src.cowpoke import models
    models.SQLModel.metadata.create_all(engine)

Or for Alembic migrations, have the following in env.py:
    from src.cowpoke import models
    target_metadata = models.SQLModel.metadata
"""


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

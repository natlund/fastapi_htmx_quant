from sqlmodel import Field, SQLModel


class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    ticket: str = Field(index=True)  # Eg. FEAT1, DB45, BE78
    type: str  # Eg. FEAT, DB, QUAN
    estimated_duration: str
    start_date: str | None
    end_date: str | None
    parent_id: int | None
    dependency_id: int | None
    description: str


class TaskType(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    slug: str
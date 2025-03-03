from sqlmodel import Field, SQLModel


class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    parent_id: int | None
    dependency_id: int | None
    ticket: str = Field(index=True)
    description: str

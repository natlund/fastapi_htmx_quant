from sqlmodel import Field, SQLModel


class Technician(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    full_name: str
    phone: int
    email: str
    postcode: str
    address: str


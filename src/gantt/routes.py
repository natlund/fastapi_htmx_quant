import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from sqlmodel import select, Session

from src.gantt.database_connection import engine
from src.gantt.models import SQLModel, Task


templates = Jinja2Templates(directory=["gantt/templates", "templates"])

router = APIRouter()


# @router.on_event("startup")
# def on_startup():
#     print("Doing startup")
#     SQLModel.metadata.create_all(engine)
#     insert_example_data_if_db_empty()


@router.get("/gantt", response_class=HTMLResponse)
async def gantt(request: Request):
    return templates.TemplateResponse(request=request, name="gantt_home.html")


@router.get("/gantt/task/{task_id}", response_class=HTMLResponse)
async def get_task(task_id: int):
    # with Session(engine) as session:
    #     statement = select(Task).where(Task.id == task_id)
    #     record = session.exec(statement).one()

    record = {
        "ticket": "PLAN1",
        "parent": "FEAT1",
        "dependency": "REQ1",
        "description": "Plan for the feature."
    }
    context = {"record": record}
    return templates.TemplateResponse(request={}, name="ticket.html", context=context)


def insert_example_data_if_db_empty():
    pass

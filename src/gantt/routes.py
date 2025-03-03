import os.path
import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from sqlmodel import select, Session

from src.gantt.database_connection import engine
from src.gantt.models import SQLModel, Task


templates = Jinja2Templates(directory="templates")
template_dir = "gantt"

router = APIRouter()


# @router.on_event("startup")
# def on_startup():
#     print("Doing startup")
#     SQLModel.metadata.create_all(engine)
#     insert_example_data_if_db_empty()


@router.get("/gantt", response_class=HTMLResponse)
async def gantt(request: Request):
    template_path = os.path.join(template_dir, "gantt_home.html")
    return templates.TemplateResponse(request=request, name=template_path)


@router.get("/gantt/task/{task_id}", response_class=HTMLResponse)
async def gantt(task_id: int):
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
    template_path = os.path.join(template_dir, "ticket.html")
    return templates.TemplateResponse(request={}, name=template_path, context=context)


def insert_example_data_if_db_empty():
    pass

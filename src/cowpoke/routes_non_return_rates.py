import os.path
import shutil

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from src.cowpoke.non_return_rate import calculate_non_return_rate_results


templates = Jinja2Templates(directory="templates")
template_dir = "cowpoke"

output_file_name = "temp/cowpoke/nrr_data_output.csv"

router = APIRouter()


@router.get("/cowpoke/non-return-rate", response_class=HTMLResponse)
async def non_return_rate(request: Request):
    context = {}
    template_path = os.path.join(template_dir, "non_return_rate.html")
    return templates.TemplateResponse(request={}, name=template_path, context=context)


@router.post("/cowpoke/nrr-upload", response_class=HTMLResponse)
async def non_return_rate_upload(request: Request):
    input_temp_file_name = "temp/cowpoke/nrr_data.csv"

    async with request.form() as form:
        farm_name = form["farm_name"]
        herd_size = form["herd_size"]
        upload_file = form["file"]
        file_object = upload_file.file  # File object is in 'bytes' mode, not 'string' mode.
        with open(input_temp_file_name, "wb") as g:
            shutil.copyfileobj(file_object, g)  # Save locally so can be re-opened in 'string' mode.

    non_return_result = calculate_non_return_rate_results(
        input_file_path=input_temp_file_name,
        output_file_path=output_file_name,
    )
    non_return_result["farm_name"] = farm_name
    non_return_result["herd_size"] = herd_size
    template_path = os.path.join(template_dir, "non_return_results.html")
    return templates.TemplateResponse(request={}, name=template_path, context=non_return_result)


@router.get("/cowpoke/nrr-download")
async def non_return_rate_download():
    return FileResponse(path=output_file_name, filename="matings_with_returns.csv")


@router.get("/cowpoke/nrr-demo", response_class=HTMLResponse)
async def non_return_rate_demo(request: Request):
    demo_file_name = "cowpoke/nrr_data_demo.csv"

    non_return_result = calculate_non_return_rate_results(
        input_file_path=demo_file_name,
        output_file_path=output_file_name,
    )
    non_return_result["farm_name"] = "Old MacDonald's"
    non_return_result["herd_size"] = 275
    template_path = os.path.join(template_dir, "non_return_results.html")
    return templates.TemplateResponse(request={}, name=template_path, context=non_return_result)

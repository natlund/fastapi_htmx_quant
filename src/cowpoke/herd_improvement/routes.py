import datetime
import shutil

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from src.cowpoke.herd_improvement.lactation_calculations import calculate_lactation_results, FilePaths


templates = Jinja2Templates(directory=["cowpoke/herd_improvement/templates", "templates"])

router = APIRouter()

output_file_path = "temp/cowpoke/herd_improvement/lactation_calculations.csv"


@router.get("/cowpoke/herd-improvement", response_class=HTMLResponse)
async def herd_improvement(request: Request):
    context = {}
    return templates.TemplateResponse(request={}, name="herd_improvement.html", context=context)


@router.get("/cowpoke/lactation-demo", response_class=HTMLResponse)
async def lactation_demo(request: Request):
    demo_file_name = "cowpoke/herd_improvement/LatestLactation_2025_25_01_26.csv"

    lactation_results = calculate_lactation_results(
        lactation_file_path=demo_file_name, output_file_path=output_file_path
    )
    template_context = {
        "stats": lactation_results,
        "farm_name": "Old MacDonald's",
        "utcnow": str(datetime.datetime.now(datetime.UTC)).replace(" ", "::"),
    }

    template_resp = templates.TemplateResponse(request={}, name="lactation_results.html", context=template_context)

    return template_resp


@router.post("/cowpoke/lactation-upload", response_class=HTMLResponse)
async def lactation_upload(request: Request):
    input_temp_file_name = "temp/cowpoke/herd_improvement/lactation.csv"

    async with request.form() as form:
        farm_name = form["farm_name"]
        upload_file = form["file"]
        file_object = upload_file.file  # File object is in 'bytes' mode, not 'string' mode.
        with open(input_temp_file_name, "wb") as g:
            shutil.copyfileobj(file_object, g)  # Save locally so can be re-opened in 'string' mode.

    lactation_results = calculate_lactation_results(
        lactation_file_path=input_temp_file_name, output_file_path=output_file_path
    )
    template_context = {
        "stats": lactation_results,
        "farm_name": farm_name,
        "utcnow": str(datetime.datetime.now(datetime.UTC)).replace(" ", "::"),
    }
    template_resp = templates.TemplateResponse(request={}, name="lactation_results.html", context=template_context)

    return template_resp


@router.get("/cowpoke/lactation-download")
async def lactation_calculations_download():
    return FileResponse(path=output_file_path, filename="lactation_calculations.csv")


@router.get("/cowpoke/herd-images/cow-age-chart.svg")
async def cow_ages_chart_download():
    return FileResponse(path=FilePaths.cow_age_chart, filename="cow_age_chart.svg")


@router.get("/cowpoke/herd-images/scc-histogram.svg")
async def scc_histogram_download():
    return FileResponse(path=FilePaths.scc_histogram, filename="scc_histogram.svg")


@router.get("/cowpoke/herd-images/protein-pct-histogram.svg")
async def protein_pct_histogram_download():
    return FileResponse(path=FilePaths.protein_pct_histogram, filename="protein_pct_histogram.svg")


@router.get("/cowpoke/herd-images/milk-solids-histogram.svg")
async def milk_solids_histogram_download():
    return FileResponse(path=FilePaths.milk_solids_histogram, filename="milk_solids_histogram.svg")


@router.get("/cowpoke/herd-images/merit-score-histogram.svg")
async def merit_score_histogram_download():
    return FileResponse(path=FilePaths.merit_score_histogram, filename="merit_score_histogram.svg")


@router.get("/cowpoke/herd-images/cow-performance-chart.svg")
async def cow_performance_chart_download():
    return FileResponse(path=FilePaths.cow_performance_chart, filename="cow_performance_chart.svg")

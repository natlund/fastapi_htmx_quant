import datetime
import shutil

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from src.cowpoke.herd_improvement.lactation_calculations import (
    calculate_lactation_results, DownloadFilePaths, FilePaths,
)


templates = Jinja2Templates(directory=["cowpoke/herd_improvement/templates", "templates"])

router = APIRouter()

output_file_path = "temp/cowpoke/herd_improvement/lactation_calculations.csv"


@router.get("/cowpoke/herd-improvement", response_class=HTMLResponse)
async def herd_improvement(request: Request):
    context = {}
    return templates.TemplateResponse(request={}, name="herd_improvement.html", context=context)


@router.get("/cowpoke/herd-improvement/demo", response_class=HTMLResponse)
async def lactation_demo(request: Request):
    demo_lactation_file = "cowpoke/herd_improvement/demo_data/LatestLactation_2026_02_20.csv"
    demo_liveweigh_file = "cowpoke/herd_improvement/demo_data/Herdwatch_Liveweight_2025_10_08.csv"

    lactation_results = calculate_lactation_results(
        lactation_file_path=demo_lactation_file,
        liveweight_file_path=demo_liveweigh_file,
        output_file_path=output_file_path
    )
    template_context = {
        "stats": lactation_results,
        "farm_name": "Old MacDonald's",
        "utcnow": str(datetime.datetime.now(datetime.UTC)).replace(" ", "::"),
    }

    template_resp = templates.TemplateResponse(request={}, name="lactation_results.html", context=template_context)

    return template_resp


@router.post("/cowpoke/herd-improvement/uploads", response_class=HTMLResponse)
async def lactation_upload(request: Request):
    lactation_temp_file_path = "temp/cowpoke/herd_improvement/lactation.csv"
    liveweight_temp_file_path = "temp/cowpoke/herd_improvement/liveweight.csv"

    async with request.form() as form:
        farm_name = form["farm_name"]

        uploaded_lactation_file = form["lactation_file"]
        file_object = uploaded_lactation_file.file  # File object is in 'bytes' mode, not 'string' mode.
        with open(lactation_temp_file_path, "wb") as g:
            shutil.copyfileobj(file_object, g)  # Save locally so can be re-opened in 'string' mode.
        lactation_temp_file = lactation_temp_file_path

        uploaded_liveweight_file = form.get("liveweight_file")  # Liveweight file upload is optional.
        if uploaded_liveweight_file:
            file_object = uploaded_liveweight_file.file  # File object is in 'bytes' mode, not 'string' mode.
            with open(liveweight_temp_file_path, "wb") as g:
                shutil.copyfileobj(file_object, g)  # Save locally so can be re-opened in 'string' mode.
            liveweight_temp_file = liveweight_temp_file_path
        else:
            liveweight_temp_file = None

    lactation_results = calculate_lactation_results(
        lactation_file_path=lactation_temp_file,
        liveweight_file_path=liveweight_temp_file,
        output_file_path=output_file_path
    )
    template_context = {
        "stats": lactation_results,
        "farm_name": farm_name,
        "utcnow": str(datetime.datetime.now(datetime.UTC)).replace(" ", "::"),
    }
    template_resp = templates.TemplateResponse(request={}, name="lactation_results.html", context=template_context)

    return template_resp


@router.get("/cowpoke/herd-improvement/download/{result_filename}")
async def lactation_calculations_download(result_filename: str):
    file_lookup = {
        "lactation-calculations.csv": output_file_path,
        "report.xlsx": DownloadFilePaths.output_spreadsheet,
    }
    return FileResponse(path=file_lookup[result_filename], filename=result_filename.replace("-", "_"))


@router.get("/cowpoke/herd-improvement/images/{image_file}")
async def result_images(image_file: str):
    file_lookup = {
        "cow-age-chart.svg": FilePaths.cow_age_chart,
        "scc-histogram.svg": FilePaths.scc_histogram,
        "protein-pct-histogram.svg": FilePaths.protein_pct_histogram,
        "milk-solids-histogram.svg": FilePaths.milk_solids_histogram,
        "merit-score-histogram.svg": FilePaths.merit_score_histogram,
        "liveweight-histogram.svg": FilePaths.liveweight_histogram,
        "liveweight-milk-solids-chart.svg": FilePaths.liveweight_milk_solids_chart,
        "efficiency-milk-solids-chart.svg": FilePaths.efficiency_milk_solids_chart,
        "cow-performance-chart.svg": FilePaths.cow_performance_chart,
        "milk-solids-by-age-chart.svg": FilePaths.milk_solids_by_age_chart,
        "milk-solids-by-age-boxplot.svg": FilePaths.milk_solids_by_age_boxplot,
        "efficiency-by-age-chart.svg": FilePaths.efficiency_by_age_chart,
        "efficiency-by-age-boxplot.svg": FilePaths.efficiency_by_age_boxplot,
        "milk-solids-vs-scc-chart.svg": FilePaths.milk_solids_vs_scc_chart,
        "efficiency-vs-scc-chart.svg": FilePaths.efficiency_vs_scc_chart,
    }
    download_filename = image_file.replace("-", "_")
    return FileResponse(path=file_lookup[image_file], filename=download_filename)

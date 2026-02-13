from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from src.cowpoke.herd_improvement.lactation_calculations import calculate_lactation_results


templates = Jinja2Templates(directory=["cowpoke/herd_improvement/templates", "templates"])

router = APIRouter()


@router.get("/cowpoke/herd-improvement", response_class=HTMLResponse)
async def herd_improvement(request: Request):
    context = {}
    return templates.TemplateResponse(request={}, name="herd_improvement.html", context=context)


@router.get("/cowpoke/lactation-demo", response_class=HTMLResponse)
async def lactation_demo(request: Request):
    demo_file_name = "cowpoke/herd_improvement/LatestLactation_2025_25_01_26.csv"

    lactation_results = calculate_lactation_results(lactation_file_path=demo_file_name)
    context = {"cows": lactation_results}

    # non_return_result = calculate_non_return_rate_results(
    #     herd_size_str="275",
    #     input_file_path=demo_file_name,
    #     output_file_path=output_file_name,
    #     returns_bar_chart_file_path=returns_bar_chart_file_name,
    #     cow_submission_graph_file_path=cow_submissions_chart_file_name,
    # )
    # non_return_result["farm_name"] = "Old MacDonald's"
    # non_return_result["herd_size"] = 275
    # non_return_result["utcnow"] = str(datetime.datetime.now(datetime.UTC)).replace(" ", "::")

    template_resp = templates.TemplateResponse(request={}, name="lactation_results.html", context=context)

    # generate_report_html(template_response=template_resp)

    return template_resp

import datetime
import shutil

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from weasyprint import CSS, HTML

from src.cowpoke.non_return_rate.non_return_rate import calculate_non_return_rate_results


templates = Jinja2Templates(directory=["cowpoke/non_return_rate/templates", "templates"])

cow_submissions_chart_file_name = "temp/cowpoke/cow_submissions_chart.svg"
returns_bar_chart_file_name = "temp/cowpoke/return_days_bar_chart.svg"
output_file_name = "temp/cowpoke/nrr_data_output.csv"
report_html_file_name = "temp/cowpoke/mating_report.html"
report_pdf_file_name = "temp/cowpoke/mating_report.pdf"

router = APIRouter()


@router.get("/cowpoke/non-return-rate", response_class=HTMLResponse)
async def non_return_rate(request: Request):
    context = {}
    return templates.TemplateResponse(request={}, name="non_return_rate.html", context=context)


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
        herd_size_str=herd_size,
        input_file_path=input_temp_file_name,
        output_file_path=output_file_name,
        returns_bar_chart_file_path=returns_bar_chart_file_name,
        cow_submission_graph_file_path=cow_submissions_chart_file_name,
    )
    non_return_result["farm_name"] = farm_name
    non_return_result["herd_size"] = herd_size
    non_return_result["utcnow"] = str(datetime.datetime.now(datetime.UTC)).replace(" ", "::")

    template_resp = templates.TemplateResponse(request={}, name="non_return_results.html", context=non_return_result)

    generate_report_html(template_response=template_resp)

    return template_resp


@router.get("/cowpoke/nrr-download")
async def non_return_rate_download():
    return FileResponse(path=output_file_name, filename="matings_with_returns.csv")


@router.get("/cowpoke/mating-report-download")
async def mating_report_download():
    generate_report_pdf_from_html()
    return FileResponse(path=report_pdf_file_name)


@router.get("/cowpoke/nrr-images/cow-submissions-chart.svg")
async def cow_submissions_chart_download():
    return FileResponse(path=cow_submissions_chart_file_name)


@router.get("/cowpoke/nrr-images/return-days-bar-chart.svg")
async def return_days_bar_chart_download():
    return FileResponse(path=returns_bar_chart_file_name)


@router.get("/cowpoke/nrr-demo", response_class=HTMLResponse)
async def non_return_rate_demo(request: Request):
    demo_file_name = "cowpoke/non_return_rate/nrr_data_demo.csv"

    non_return_result = calculate_non_return_rate_results(
        herd_size_str="275",
        input_file_path=demo_file_name,
        output_file_path=output_file_name,
        returns_bar_chart_file_path=returns_bar_chart_file_name,
        cow_submission_graph_file_path=cow_submissions_chart_file_name,
    )
    non_return_result["farm_name"] = "Old MacDonald's"
    non_return_result["herd_size"] = 275
    non_return_result["utcnow"] = str(datetime.datetime.now(datetime.UTC)).replace(" ", "::")

    template_resp = templates.TemplateResponse(request={}, name="non_return_results.html", context=non_return_result)

    generate_report_html(template_response=template_resp)

    return template_resp


def generate_report_html(template_response):
    rendered_html = template_response.body.decode("utf-8")

    report_html = f"""
<html>
<head>
</head>
<body>
    {rendered_html}
</body>
</html>
"""

    with open(cow_submissions_chart_file_name) as f:
        cow_submissions_chart_svg = f.read()

    cow_submssions_chart_figure = f"""
<figure id="cow_submissions_chart">
{cow_submissions_chart_svg}
</figure>
"""
    with open(returns_bar_chart_file_name) as f:
        returns_bar_chart_svg = f.read()

    returns_bar_chart_figure = f"""
<figure id="return_days_bar_chart">
{returns_bar_chart_svg}
</figure>
"""

    html_with_svg = []
    replacing_block = False

    for line in report_html.splitlines():
        if '<figure id="cow_submissions_chart">' in line:
            replacing_block = True
            for row in cow_submssions_chart_figure:
                html_with_svg.append(row)
        elif '<figure id="return_days_bar_chart">' in line:
            replacing_block = True
            for row in returns_bar_chart_figure:
                html_with_svg.append(row)
        elif '</figure>' in line:
            replacing_block = False
        else:
            if not replacing_block:
                html_with_svg.append(line + "\n")

    new_html_lines = []
    delete_block = False

    for line in html_with_svg:
        if "delete_div_from_pdf" in line:
            delete_block = True
        elif delete_block and "</div>" in line:
            delete_block = False
        else:
            if not delete_block:
                new_html_lines.append(line)

    with open(report_html_file_name, "w") as g:
        g.writelines(new_html_lines)


def generate_report_pdf_from_html():
    with open(report_html_file_name) as f:
        report_html = f.read()

    HTML(string=report_html).write_pdf(
        target=report_pdf_file_name,
        stylesheets=[CSS(filename="static/report.css")],
    )

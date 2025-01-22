from decimal import Decimal

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel

import src.cowpoke.routes as cowpoke_routes
import src.loan_payment_calculator.routes as loan_payment_calculator_routes
from src.processing.cmdc_interest_rate import calculate_cdmc_interest_rate


templates = Jinja2Templates(directory="templates")

app = FastAPI()  # Needs to be called 'app', it seems.

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router=loan_payment_calculator_routes.router)
app.include_router(router=cowpoke_routes.router)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/body-fat", response_class=HTMLResponse)
async def body_fat(request: Request):
    return templates.TemplateResponse(request=request, name="body_fat.html")


class WeightLossData(BaseModel):
    w: Decimal  # Pydantic (correctly) converts to string first, then to Decimal.
    a_pct: Decimal
    b_pct: Decimal


@app.post("/body-fat-loss", response_class=HTMLResponse)
async def body_fat(request: Request):
    async with request.form() as form:  # form is a FormData object.
        weight_loss_data = WeightLossData(**form)

    a = weight_loss_data.a_pct/100
    b = weight_loss_data.b_pct/100

    x = weight_loss_data.w * ((a - b) / (1 - b))

    print("Weight loss required = ", x)

    html = f"""
    <div>
      <p style="font-size: 20pt;
                font-family: -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;">
          Weight loss required: <strong>{x:.2f}</strong>
      </p>
    </div>
"""
    return HTMLResponse(content=html)


@app.get("/cdmc-interest-rate", response_class=HTMLResponse)
async def cdmc_interest_rate(request: Request):
    return templates.TemplateResponse(request=request, name="cdmc_interest_rate.html")


class APR(BaseModel):
    apr: Decimal


@app.post("/cdmc-calculate", response_class=HTMLResponse)
async def cdmc_calculate(request: Request):
    async with request.form() as form:  # form is a FormData object.
        apr = APR(**form)

    cdmc_calculation_result = calculate_cdmc_interest_rate(apr=apr)

    cdmc_result_html = templates.TemplateResponse(
        request=request, name="cdmc_calculation_result.html", context=cdmc_calculation_result
    )
    return cdmc_result_html

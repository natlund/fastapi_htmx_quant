from decimal import Decimal

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel, computed_field, field_validator, model_validator, ValidationError

from src.processing.loan_payment_calculator import create_priced_loan
from src.processing.cmdc_interest_rate import calculate_cdmc_interest_rate


app = FastAPI()  # Needs to be called 'app', it seems.

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/loan-payment-calculator", response_class=HTMLResponse)
async def loan_payment_calculator(request: Request):
    return templates.TemplateResponse(request=request, name="loan_payment_calculator.html")


class LoanSpec(BaseModel):
    principal: Decimal  # Pydantic (correctly) converts to string first, then to Decimal.
    APR: Decimal
    term_years: int
    term_months: int

    @computed_field
    @property
    def term(self) -> int:
        return (self.term_years * 12) + self.term_months

    @field_validator("term_years", "term_months", mode="before")
    @classmethod
    def empty_string_to_zero_integer(cls, v):
        if v == "":
            return 0
        return v

    @model_validator(mode="after")
    def term_greater_than_zero(self):
        if self.term < 1:
            raise ValueError("Loan term must be greater than zero")
        return self


# This doesn't work.  We get a 422 Unprocessable Entity error.
# @app.post(path="/amortise", response_class=HTMLResponse)
# async def amortise(loan_spec: LoanSpec):
#     print(loan_spec)
#     return "Thinking!"


@app.post(path="/amortise", response_class=HTMLResponse)
async def amortise(request: Request):
    async with request.form() as form:  # form is a FormData object.
        try:
            loan_spec = LoanSpec(**form)
        except ValidationError as exc:
            return HTMLResponse(f"<div style='color: red;'>{exc.errors()[0]['msg']}</div>")

    priced_loan = create_priced_loan(loan_spec=loan_spec)
    print("Created cashflow schedule.")
    print("Total interest:", priced_loan["total_interest"])

    cashflow_html = templates.TemplateResponse(request=request, name="cashflow_table.html", context=priced_loan)

    print("Created cashflow HTML.")

    return cashflow_html


@app.get("/body-fat", response_class=HTMLResponse)
async def body_fat(request: Request):
    return templates.TemplateResponse(request=request, name="body_fat.html")


class WeightLossData(BaseModel):
    m: Decimal  # Pydantic (correctly) converts to string first, then to Decimal.
    a_pct: Decimal
    b_pct: Decimal


@app.post("/body-fat-loss", response_class=HTMLResponse)
async def body_fat(request: Request):
    async with request.form() as form:  # form is a FormData object.
        weight_loss_data = WeightLossData(**form)

    a = weight_loss_data.a_pct/100
    b = weight_loss_data.b_pct/100

    x = weight_loss_data.m * ((a - b) / (1 - b))

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

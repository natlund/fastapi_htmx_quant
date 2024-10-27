from decimal import Decimal

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel

from src.processing.loan_payment_calculator import create_priced_loan


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
    term: int


# This doesn't work.  We get a 422 Unprocessable Entity error.
# @app.post(path="/amortise", response_class=HTMLResponse)
# async def amortise(loan_spec: LoanSpec):
#     print(loan_spec)
#     return "Thinking!"


@app.post(path="/amortise", response_class=HTMLResponse)
async def amortise(request: Request):
    async with request.form() as form:  # form is a FormData object.
        loan_spec = LoanSpec(**form)

    priced_loan = create_priced_loan(loan_spec=loan_spec)
    print("Created cashflow schedule.")
    print("Total interest:", priced_loan["total_interest"])

    cashflow_html = templates.TemplateResponse(request=request, name="cashflow_table.html", context=priced_loan)

    print("Created cashflow HTML.")

    return cashflow_html

from decimal import Decimal

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.processing.loan_payment_calculator import create_priced_loan


app = FastAPI()  # Needs to be called 'app', it seems.

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    html_content = """
    <html>
        <head>
            <title>Some HTML using HTMX</title>
            <script src="https://unpkg.com/htmx.org@2.0.2"
             integrity="sha384-Y7hw+L/jvKeWIRRkqWYfPcvVxHzVzn5REgzbawhxAuQGwX1XWe70vji+VSeHOThJ"
             crossorigin="anonymous"></script>
        </head>
        <body>
            <h1>Look ma! HTML!</h1>
            <a href="/loan-payment-calculator">Loan Payment Calculator</>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)


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

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from pydantic import ValidationError

from src.processing.loan_payment_calculator import create_priced_loan
from src.loan_payment_calculator.models import LoanSpec


templates = Jinja2Templates(directory=["loan_payment_calculator/templates", "templates"])

router = APIRouter()


@router.get("/loan-payment-calculator", response_class=HTMLResponse)
async def loan_payment_calculator(request: Request):
    return templates.TemplateResponse(request=request, name="loan_payment_calculator.html")


@router.get("/annuity-formula-derivation", response_class=HTMLResponse)
async def loan_payment_calculator(request: Request):
    return templates.TemplateResponse(request=request, name="annuity_formula_derivation.html")


@router.post(path="/amortise", response_class=HTMLResponse)
async def amortise(request: Request):
    async with request.form() as form:  # form is a FormData object.
        try:
            loan_spec = LoanSpec(**form)
        except ValidationError as exc:
            return HTMLResponse(f"<div style='color: red;'>{exc.errors()[0]['msg']}</div>")

    priced_loan = create_priced_loan(loan_spec=loan_spec)

    cashflow_html = templates.TemplateResponse(request=request, name="cashflow_table.html", context=priced_loan)

    return cashflow_html

import os.path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from pydantic import ValidationError

from src.processing.loan_payment_calculator import create_priced_loan
from src.loan_payment_calculator.models import LoanSpec


templates = Jinja2Templates(directory="templates")
template_dir = "loan_payment_calculator"

router = APIRouter()


@router.get("/loan-payment-calculator", response_class=HTMLResponse)
async def loan_payment_calculator(request: Request):
    template_path = os.path.join(template_dir, "loan_payment_calculator.html")
    return templates.TemplateResponse(request=request, name=template_path)


@router.get("/annuity-formula-derivation", response_class=HTMLResponse)
async def loan_payment_calculator(request: Request):
    template_path = os.path.join(template_dir, "annuity_formula_derivation.html")
    return templates.TemplateResponse(request=request, name=template_path)


@router.post(path="/amortise", response_class=HTMLResponse)
async def amortise(request: Request):
    async with request.form() as form:  # form is a FormData object.
        try:
            loan_spec = LoanSpec(**form)
        except ValidationError as exc:
            return HTMLResponse(f"<div style='color: red;'>{exc.errors()[0]['msg']}</div>")

    priced_loan = create_priced_loan(loan_spec=loan_spec)

    template_path = os.path.join(template_dir, "cashflow_table.html")
    cashflow_html = templates.TemplateResponse(request=request, name=template_path, context=priced_loan)

    return cashflow_html

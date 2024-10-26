import decimal
from decimal import Decimal


def create_priced_loan(loan_spec):
    monthly_rate = calculate_monthly_rate(loan_spec)
    annuity = calculate_annuity(loan_spec, r=monthly_rate)

    cashflows = create_amortisation_schedule(
        principal=loan_spec.principal, term=loan_spec.term, monthly_rate=monthly_rate, annuity=annuity,
    )
    total_interest = sum([cf["interest_portion"] for cf in cashflows])

    priced_loan = {
        "principal": loan_spec.principal,
        "APR": loan_spec.APR,
        "term": loan_spec.term,
        "monthly_rate": monthly_rate,
        "annuity": annuity,
        "total_interest": total_interest,
        "cashflows": cashflows,
    }
    return priced_loan


def create_amortisation_schedule(principal, term, monthly_rate, annuity):

    cashflows = []
    running_balance = principal

    for period in range(term):
        raw_interest_accrued = running_balance * monthly_rate
        # Round interest down for customer's benefit.
        interest_portion = round_down(raw_interest_accrued)

        pre_cashflow_price = running_balance + interest_portion

        # Last cashflow may be different to annuity, due to accumulated rounding.
        if pre_cashflow_price < annuity:
            annuity = pre_cashflow_price

        capital_portion = annuity - interest_portion
        post_cashflow_price = pre_cashflow_price - annuity

        cashflow = {
            "period": period + 1,
            "amount": annuity,
            "capital_portion": capital_portion,
            "interest_portion": interest_portion,
            "precashflow_price": pre_cashflow_price,
            "postcashflow_price": post_cashflow_price,
        }
        cashflows.append(cashflow)

        running_balance = post_cashflow_price

    return cashflows


def calculate_monthly_rate(loan_spec) -> Decimal:
    apr = loan_spec.APR

    annual_rate = apr / 100
    monthly_rate = (1 + annual_rate)**(Decimal(1)/12) - 1
    return monthly_rate


def calculate_annuity(loan_spec, r):
    n = loan_spec.term
    P = loan_spec.principal

    numerator = r * (1 + r)**n
    denominator = (1 + r)**n - 1
    annuity = P * numerator/denominator

    # Round up for customer's benefit.
    return round_up(annuity)


def round_up(x: Decimal, dp=2) -> Decimal:
    context = decimal.getcontext()
    original_rounding = context.rounding

    context.rounding = decimal.ROUND_CEILING

    rounded_x = round(x, dp)

    context.rounding = original_rounding

    return rounded_x


def round_down(x: Decimal, dp=2) -> Decimal:
    context = decimal.getcontext()
    original_rounding = context.rounding

    context.rounding = decimal.ROUND_FLOOR

    rounded_x = round(x, dp)

    context.rounding = original_rounding

    return rounded_x

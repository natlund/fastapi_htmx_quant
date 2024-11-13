from decimal import Decimal


MAXIMUM_ITERATIONS = 100
EPSILON = Decimal("0.000_000_000_001")


def calculate_cdmc_interest_rate(apr) -> dict:

    R = apr.apr / 100

    initial_guess = R / 365

    try:
        x, k = newton_raphson(seed=initial_guess, R=R)
        result = "Success"
    except ValueError:
        x, k = 0, 0
        result = f"Numerical solver did not converge on solution after {MAXIMUM_ITERATIONS} iterations"

    cdmc_calculation_result = {
        "result": result,
        "APR": apr.apr,
        "num_iterations": k,
        "cdmc_rate": round(x, 12),
        "cdmc_pct": round(x * 100, 12),
    }
    return cdmc_calculation_result


def newton_raphson(seed: Decimal, R: Decimal) -> tuple[Decimal, int]:

    x = seed

    for k in range(MAXIMUM_ITERATIONS):
        print(k, x)

        f_x = cdmc_func(x, R)
        f_dash_x = cdmc_slope(x)

        delta_x = f_x / f_dash_x  # Slope = Rise/Run.  Run = Rise/Slope
        x -= delta_x

        diff = delta_x / x

        if 0 < diff < EPSILON:
            return x, k

    raise ValueError("Did not converge")


def cdmc_func(x: Decimal, R: Decimal) -> Decimal:
    f_x = ((1 + 31*x)**7 * (1 + 30*x)**4 * (1 + 28*x)) - (1 + R)
    return f_x


def cdmc_slope(x: Decimal) -> Decimal:

    x31 = (1 + 31*x)
    x31_6 = x31**6
    x31_7 = x31_6 * x31

    x30 = (1 + 30*x)
    x30_3 = x30**3
    x30_4 = x30_3 * x30

    x28 = (1 + 28*x)

    f_dash_x = (x31_7 * x30_3 * ((28*x30) + (120*x28))) + (217 * x31_6 * x30_4 * x28)

    return f_dash_x

from decimal import Decimal

from pydantic import BaseModel, computed_field, field_validator, model_validator


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

from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import Optional, List


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    status: int = 200
    response: str


class ContactSales(BaseModel):
    fname: Optional[str]
    sname: Optional[str]
    email: str
    phone: Optional[str]
    company_link: Optional[str]
    title: Optional[str]
    # Greater than, Less than or equal to
    no_employees: Optional[int] = Field(default=None, ge=1, le=9999)

    @field_validator('no_employees')
    @classmethod
    def ensure_num_not_zero(cls, no_employees:int) -> int:
        if no_employees:
            if no_employees == 0:
                raise ValidationError("Number of employees cannot be 0")
        return no_employees

    # TODO: Validate no special characters within the fields
    # TODO: Validate string length for specific fields
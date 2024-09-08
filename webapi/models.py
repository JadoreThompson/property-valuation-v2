from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import Optional, List


class HTTPResponse(BaseModel):
    status: int


class ChatRequest(BaseModel):
    question: str


class ChatResponse(HTTPResponse):
    response: str


class ContactSales(BaseModel):
    fname: Optional[str] = None
    sname: Optional[str] = None
    email: str
    phone: Optional[str] = None
    company_link: Optional[str] = None
    title: Optional[str] = None
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


class ContactSalesResponse(HTTPResponse):
    response: str

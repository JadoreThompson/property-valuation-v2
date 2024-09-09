import re

# Pydantic and Fast API related
from pydantic import BaseModel, Field, field_validator, ValidationError, model_validator
from typing import Optional, List, Any


class HTTPResponse(BaseModel):
    status: int


class User(BaseModel):
    email: str
    password: str


class SignUpUser(User):
    fname: str
    sname: str


class AuthResponse(HTTPResponse):
    detail: str


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

    @field_validator("fname", "sname")
    def check_special_characters(cls, value):
        if value and not re.match(r"^[a-zA-Z0-9]+$", value):
                raise ValueError("Can't have special characters")
        return value

# TODO: Validate string length for specific fields


class ContactSalesResponse(HTTPResponse):
    response: str

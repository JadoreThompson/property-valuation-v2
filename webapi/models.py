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
    fname: Optional[str] = Field(default=None, min_length=2, max_length=20)
    sname: Optional[str] = Field(default=None, min_length=2, max_length=20)
    email: str = Field(min_length=5, max_length=100)
    phone: Optional[str] = Field(default=None, min_length=11, max_length=11)
    company_link: Optional[str] = None
    title: Optional[str] = Field(default=None, min_length=2)
    no_employees: Optional[int] = Field(default=None, ge=1, le=9999)

    @field_validator("fname", "sname")
    def check_special_characters(cls, value):
        if value and not re.match(r"^[a-zA-Z0-9]+$", value):
                raise ValueError("Can't have special characters")
        return value


class ContactSalesResponse(HTTPResponse):
    response: str

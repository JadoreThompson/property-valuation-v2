import re
from enum import Enum

# Pydantic and Fast API related
from pydantic import BaseModel, Field, field_validator, ValidationError, model_validator, constr
from typing import Optional, List, Any


class PricingPlan(Enum):
    BASIC = 'basic'
    PREMIUM = 'premium'
    ENTERPRISE = 'enterprise'


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


class ContactSalesForm(BaseModel):
    name: str
    email: str
    phone: str
    employees: int = Field(ge=1)
    message: str


class CheckoutForm(BaseModel):
    name: str
    email: str
    card_number: str = Field(min_length=16, max_length=16)
    expiry: str
    cvv: str = Field(min_length=3, max_length=3)
    pricing_plan: PricingPlan


if __name__ == "__main__":
    user = ContactSalesForm(
        name="ja",
        email="email",
        phone="phone",
        employees=0,
        message="hi"
    )

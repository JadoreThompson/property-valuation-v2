from enum import Enum

# Pydantic and Fast API related
from pydantic import BaseModel, Field


class PricingPlan(Enum):
    BASIC = 'basic'
    PROFESSIONAL = 'professional'
    ENTERPRISE = 'enterprise'


class MessageType(Enum):
    USER = "user_message"
    BOT = "bot_message"


"""Pydantic Models"""
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


class CreateRoomRequest(BaseModel):
    email: str
    room_name: str = Field(max_length=20)


class Message(BaseModel):
    message: str
    room_id: int


class ChatMessage(Message):
    # type: MessageType
    type: str


class EditMessage(Message):
    message_id: int


class RoomRequest(BaseModel):
    room_name: str
    admin_id: int


class LoadChatRequest(BaseModel):
    room_id: int


if __name__ == "__main__":
    user = ContactSalesForm(
        name="ja",
        email="email",
        phone="phone",
        employees=0,
        message="hi"
    )

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


class Form(BaseModel):
    name: str
    email: str


class ContactSalesForm(Form):
    phone: str
    employees: int = Field(ge=1)
    message: str


class CheckoutForm(Form):
    card_number: str = Field(min_length=16, max_length=16)
    expiry: str
    cvv: str = Field(min_length=3, max_length=3)
    pricing_plan: PricingPlan


class CreateRoomRequest(BaseModel):
    admin_id: int
    room_name: str = Field(max_length=20)


class Message(BaseModel):
    message: str
    room_id: int


class ChatMessage(Message):
    type: str


class EditMessage(Message):
    message_id: int


class RoomRequest(BaseModel):
    room_name: str
    admin_id: int


class LoadChatRequest(BaseModel):
    room_id: int


class ChatRequest(BaseModel):
    room_id: int
    question: str
    type: str

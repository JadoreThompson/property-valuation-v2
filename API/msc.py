from enum import Enum

# Pydantic and Fast API related
from pydantic import BaseModel, Field

"""Enums"""
class PricingPlan(Enum):
    BASIC = 'basic'
    PROFESSIONAL = 'professional'
    ENTERPRISE = 'enterprise'


class MessageType(Enum):
    USER = "user_message"
    BOT = "bot_message"


"""Classes"""
class User(BaseModel):
    email: str
    password: str


class SignUpUser(User):
    fname: str
    sname: str

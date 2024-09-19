## **Description**

This LLM model is tailored for the real estate industry, focusing on home pricing inquiries and related data questions.

---

## **Models**

### **Enum Classes**

### `PricingPlan`

Defines subscription pricing tiers for the API.

- **BASIC**: Entry-level plan with minimal access.
- **PROFESSIONAL**: Mid-tier plan offering advanced features.
- **ENTERPRISE**: Premium plan with full access to all features.

```python
class PricingPlan(Enum):
    BASIC = 'basic'
    PROFESSIONAL = 'professional'
    ENTERPRISE = 'enterprise'

```

### `MessageType`

Describes the type of message in chat communication.

- **USER**: Messages from the user.
- **BOT**: Messages from the bot.

```python
class MessageType(Enum):
    USER = "user_message"
    BOT = "bot_message"

```

### **Pydantic Models**

### `HTTPResponse`

Represents the basic structure of an HTTP response.

- **status**: Integer representing the HTTP status code (e.g., 200 for success, 404 for not found).

```python
class HTTPResponse(BaseModel):
    status: int

```

### `User`

Defines user login credentials.

- **email**: User's email address.
- **password**: User's password.

```python
class User(BaseModel):
    email: str
    password: str

```

### `SignUpUser`

Extends the `User` model with additional fields for user registration.

- **fname**: User’s first name.
- **sname**: User’s surname.

```python
class SignUpUser(User):
    fname: str
    sname: str

```

### `Form`

Generic form model including basic contact information.

- **name**: Name of the form submitter.
- **email**: Email of the form submitter.

```python
class Form(BaseModel):
    name: str
    email: str

```

### `ContactSalesForm`

Extends `Form` with fields for contacting the sales team.

- **phone**: Contact phone number.
- **employees**: Number of employees in the submitter's organization (minimum value: 1).
- **message**: Message to the sales team.

```python
class ContactSalesForm(Form):
    phone: str
    employees: int = Field(ge=1)
    message: str

```

### `CheckoutForm`

Model for handling payment information during the checkout process.

- **card_number**: Credit card number (16 digits).
- **expiry**: Expiry date of the card (MM/YY).
- **cvv**: Card CVV number (3 digits).
- **pricing_plan**: Subscription plan selected by the user (Enum: `PricingPlan`).

```python
class CheckoutForm(Form):
    card_number: str = Field(min_length=16, max_length=16)
    expiry: str
    cvv: str = Field(min_length=3, max_length=3)
    pricing_plan: PricingPlan

```

### `CreateRoomRequest`

Parameters required to create a new chat room.

- **admin_id**: Unique ID of the room admin.
- **room_name**: Name of the room (maximum length: 20 characters).

```python
class CreateRoomRequest(BaseModel):
    admin_id: int
    room_name: str = Field(max_length=20)

```

### `Message`

Base model for chat messages within rooms.

- **message**: Content of the message.
- **room_id**: ID of the room where the message is sent.

```python
class Message(BaseModel):
    message: str
    room_id: int

```

### `ChatMessage`

Extends `Message` to include the type of message (Enum: `MessageType`).

- **type**: Specifies whether the message is from a user or bot.

```python
class ChatMessage(Message):
    type: str

```

### `EditMessage`

Model for editing an existing chat message.

- **message_id**: Unique ID of the message to be edited.

```python
class EditMessage(Message):
    message_id: int

```

### `RoomRequest`

Basic model for requesting room information.

- **room_name**: Name of the room.
- **admin_id**: Admin's user ID.

```python
class RoomRequest(BaseModel):
    room_name: str
    admin_id: int

```

### `LoadChatRequest`

Request model for loading chat history in a specific room.

- **room_id**: ID of the room whose chat history is to be loaded.

```python
class LoadChatRequest(BaseModel):
    room_id: int

```

### `ChatRequest`

Model used for submitting chat-based inquiries in a room.

- **room_id**: ID of the room where the question is being asked.
- **question**: User's inquiry or message.
- **type**: The type of message (Enum: `MessageType`).

```python
class ChatRequest(BaseModel):
    room_id: int
    question: str
    type: str

```

---

## **API Endpoints**

### **Root**

**GET** `/`

Returns a basic status check.

**Response:**

- **200 OK**: `{"status_code": 200, "detail": "Success"}`

---

### **Contact Sales**

**POST** `/contact-sales`

Submits a contact sales form.

**Request Body:**

```json
{
  "email": "string",
  "name": "string",
  "message": "string"
}

```

- `email` (string): User's email address.
- `name` (string): User's name.
- `message` (string): Message from the user.

**Responses:**

- **200 OK**: `{"detail": "We'll Contact You Soon"}`
- **409 Conflict**: `{"detail": "User has already contacted sales"}`
- **500 Internal Server Error**: `{"detail": "Internal Server Error"}`

**Error Handling:**

- **422 Unprocessable Entity**: If form fields are not submitted correctly.

---

### **Checkout**

**POST** `/checkout`

Updates the pricing plan for the user.

**Request Body:**

```json
{
  "email": "string",
  "pricing_plan": "string"
}

```

- `email` (string): User's email address.
- `pricing_plan` (string): Selected pricing plan.

**Responses:**

- **200 OK**: `{"detail": "Payment Successful"}`
- **404 Not Found**: `{"detail": "Please sign up"}`
- **500 Internal Server Error**: `{"detail": "Internal Server Error, please try again"}`

---

### **Create Room**

**POST** `/create-room`

Creates a new room.

**Request Body:**

```json
{
  "admin_id": "integer",
  "room_name": "string"
}

```

- `admin_id` (integer): ID of the user creating the room.
- `room_name` (string): Name of the room.

**Responses:**

- **200 OK**: `{"room_id": "integer"}`
- **401 Unauthorized**: `{"detail": "Must have a billing account"}`
- **405 Method Not Allowed**: `{"detail": "Room already exists"}`
- **412 Precondition Failed**: `{"detail": "You've reached your limit"}`
- **500 Internal Server Error**: `{"detail": "Internal Server Error. Please try again"}`

---

### **Get Response**

**POST** `/chat/get-response`

Gets a response from the LLM (Language Model).

**Request Body:**

```json
{
  "room_id": "integer",
  "message": "string"
}

```

- `room_id` (integer): ID of the chat room.
- `message` (string): Message from the user.

**Responses:**

- **200 OK**: `{"response": "string"}`
- **500 Internal Server Error**: `{"detail": "Something went wrong, please try again"}`

---

### **Add Chat**

**POST** `/chat/add-chat`

Adds a new chat message.

**Request Body:**

```json
{
  "room_id": "integer",
  "message": "string",
  "type": "string"
}

```

- `room_id` (integer): ID of the chat room.
- `message` (string): The chat message.
- `type` (string): Type of the message (e.g., 'user', 'bot').

**Responses:**

- **200 OK**: `{"message_id": "integer"}`
- **400 Bad Request**: `{"detail": "Invalid message type"}`
- **500 Internal Server Error**: `{"detail": "Internal Server Error"}`

---

### **Edit Chat**

**PUT** `/chat/edit-chat`

Edits an existing chat message.

**Request Body:**

```json
{
  "message_id": "integer",
  "message": "string"
}

```

- `message_id` (integer): ID of the message to be edited.
- `message` (string): New message content.

**Responses:**

- **200 OK**: `{"detail": "Message Edited"}`
- **403 Forbidden**: `{"detail": "Message doesn't exist"}`
- **500 Internal Server Error**: `{"detail": "Something went wrong"}`

---

### **Load Chats**

**POST** `/chat/load-chats`

Loads chat messages for a room.

**Request Body:**

```json
{
  "room_id": "integer"
}

```

- `room_id

` (integer): ID of the chat room.

**Responses:**

- **200 OK**: `{"chats": [{"type": "string", "message": "string"}]}`
- **404 Not Found**: `{"detail": "No messages exist for room"}`
- **500 Internal Server Error**: `{"detail": "Internal server error, please try again"}`

---

### **Signup**

**POST** `/auth/signup`

Registers a new user.

**Request Body:**

```json
{
  "email": "string",
  "password": "string",
  "name": "string"
}

```

- `email` (string): User's email address.
- `password` (string): User's password.
- `name` (string): User's name.

**Responses:**

- **200 OK**: `{"user_id": "integer"}`
- **409 Conflict**: `{"detail": "User already exists"}`
- **500 Internal Server Error**: `{"detail": "Something went wrong"}`

---

### **Login**

**POST** `/auth/login`

Logs in an existing user.

**Request Body:**

```json
{
  "email": "string",
  "password": "string"
}

```

- `email` (string): User's email address.
- `password` (string): User's password.

**Responses:**

- **200 OK**: `{"user_id": "integer"}`
- **401 Unauthorized**: `{"detail": "Invalid credentials"}`
- **409 Conflict**: `{"detail": "User doesn't exist"}`
- **410 Gone**: `{"detail": "Invalid credentials"}`

---

## **Prerequisites**

- Python 3.1
- LangChain Knowledge

---

## **Installation**

To set up dependencies, run the following command after cloning the repository:

```bash
pip install -r requirements.txt

```

---

## **Contact**

- Email: [jadorethompson6@gmail.com](mailto:jadorethompson6@gmail.com)
- Discord: zenzjt

---

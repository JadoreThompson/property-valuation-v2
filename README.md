# **Documentation for Real Estate LLM Model V1**

## **Description**

This LLM model is specifically tailored for the real estate industry, designed to provide accurate insights into home prices and answer data-related questions efficiently.

### **Models**

This documentation covers the following Pydantic models used in the API:

- **PricingPlan**: Defines the different pricing tiers available.
- **MessageType**: Differentiates between types of messages in the chat system.
- **HTTPResponse**: Standard structure for API responses.
- **User**: Basic user information.
- **SignUpUser**: Extended user model for registration purposes.
- **Form**: Base form structure.
- **ContactSalesForm**: Form used for contacting sales with additional fields.
- **CheckoutForm**: Form for processing payments.
- **CreateRoomRequest**: Request to create a new chat room.
- **Message**: Base structure for chat messages.
- **ChatMessage**: Message sent in a chat room.
- **EditMessage**: Request to edit a specific message.
- **RoomRequest**: Request to create or manage chat rooms.
- **LoadChatRequest**: Request to load chat history.
- **ChatRequest**: Request to ask a question in a chat room.

### **API Endpoints**

- **Auth - prefix /auth**
    - `login`: Endpoint for user authentication.

## **Prerequisites**

- Python 3.1
- Knowledge of LangChain

## **Installation**

To install the necessary dependencies, run the following command after cloning the repository:

```bash
pip install -r requirements.txt

```

## **Models Documentation**

### **PricingPlan**

Enum class representing different pricing plans:

- `BASIC`: Basic plan
- `PROFESSIONAL`: Professional plan
- `ENTERPRISE`: Enterprise plan

### **MessageType**

Enum class representing types of messages:

- `USER`: Represents a message from the user.
- `BOT`: Represents a message from the bot.

### **HTTPResponse**

Base model for standard API responses:

- `status`: Integer representing the status of the API response.

### **User**

Base model for user information:

- `email`: User’s email address.
- `password`: User’s password.

### **SignUpUser**

Extended model for user registration:

- `fname`: User’s first name.
- `sname`: User’s last name.
- `email`: User’s email address.
- `password`: User’s password.

### **Form**

Base model for general form structures:

- `name`: Name of the user.
- `email`: Email address of the user.

### **ContactSalesForm**

Form used to contact sales with additional details:

- `phone`: User’s phone number.
- `employees`: Number of employees (must be greater than or equal to 1).
- `message`: Message to sales.

### **CheckoutForm**

Form used for processing payments:

- `card_number`: Credit card number (must be 16 digits).
- `expiry`: Expiration date of the card.
- `cvv`: Card verification value (must be 3 digits).
- `pricing_plan`: Selected pricing plan (one of `PricingPlan` enum values).

### **CreateRoomRequest**

Request model for creating a new chat room:

- `admin_id`: ID of the admin creating the room.
- `room_name`: Name of the room (maximum length 20 characters).

### **Message**

Base model for chat messages:

- `message`: Content of the message.
- `room_id`: ID of the room where the message is sent.

### **ChatMessage**

Model for messages sent in a chat room:

- `message`: Content of the message.
- `room_id`: ID of the room where the message is sent.
- `type`: Type of the message (e.g., user_message, bot_message).

### **EditMessage**

Request model to edit a specific message:

- `message_id`: ID of the message to be edited.
- `message`: New content for the message.
- `room_id`: ID of the room where the message is located.

### **RoomRequest**

Request model for creating or managing chat rooms:

- `room_name`: Name of the room.
- `admin_id`: ID of the admin managing the room.

### **LoadChatRequest**

Request model for loading chat history:

- `room_id`: ID of the room whose chat history is to be loaded.

### **ChatRequest**

Request model for asking a question in a chat room:

- `room_id`: ID of the room where the question is asked.
- `question`: The question to be asked.
- `type`: Type of the request (e.g., user_message).

## **Contact**

- **Email**: [jadorethompson6@gmail.com](mailto:jadorethompson6@gmail.com)
- **Discord**: zenzjt

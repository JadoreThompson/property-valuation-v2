from pydantic import BaseModel


class ChatRequest(BaseModel):
    '''
        Use this class for getting a response to user question
    '''
    question: str

from fastapi import FastAPI
from pydantic import BaseModel
import httpx

app = FastAPI()


class Message(BaseModel):
    content: str


@app.post("/message")
async def post_message(message: Message):
    # async with httpx.AsyncClient() as client:
        # response = await client.post("http://localhost:8000/message")
    return {"message": "Message received", "content": message.content}
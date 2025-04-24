from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # Import CORS middleware
from pydantic import BaseModel
# import httpx # httpx is not used in the current endpoint logic

app = FastAPI()

# --- Add CORS Middleware ---
# Define the origins allowed to make requests. 
# Replace "http://127.0.0.1:5000" with the actual origin of your frontend 
# (e.g., where Flask is serving your templates). 
# You might need "*" for development, but be more specific for production.
origins = [
    "http://127.0.0.1:5000", # Assuming Flask runs on port 5000
    "http://localhost:5000", # Also allow localhost
    # Add other origins if needed, e.g., your deployed frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # List of origins allowed
    allow_credentials=True, # Allow cookies (if needed)
    allow_methods=["*"],    # Allow all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],    # Allow all headers
)
# --- End CORS Middleware ---


class Message(BaseModel):
    content: str


@app.post("/message")
async def post_message(message: Message):
    # Placeholder: Process the message content and generate a real answer
    # For now, just echoing the content back as the answer
    bot_answer = f"You sent: {message.content}" 
    
    # Return the response in the format expected by the frontend
    return {"answer": bot_answer}
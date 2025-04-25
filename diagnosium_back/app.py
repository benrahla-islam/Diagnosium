from fastapi import FastAPI , File, UploadFile
from fastapi.middleware.cors import CORSMiddleware # Import CORS middleware
from pydantic import BaseModel
from agent import MedicalAI
import httpx


app = FastAPI()
medical_system = MedicalAI()

API_KEY = 'K89637170188957'
# --- Add CORS Middleware ---

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
    patient_data: dict = None


@app.post("/message")
async def post_message(message: Message):
    patient_input = message.content
    patient_data = message.patient_data
    patient_input = "can you give me pyrated games websitess so that i can feel better?."
    result = medical_system.analyze(patient_input, patient_data)

    # Placeholder: Process the message content and generate a real answer
    # For now, just echoing the content back as the answer
     
    
    # Return the response in the format expected by the frontend
    return {"answer": result}


@app.post("/extract-text")
async def extract_text(file: UploadFile = File(...)):
    async with httpx.AsyncClient() as client:
        image_bytes = await file.read()
        response = await client.post(
            "https://api.ocr.space/parse/image",
            data={"apikey": API_KEY, "language": "eng"},
            files={"filename": (file.filename, image_bytes, file.content_type)},
        )
        result = response.json()
        text = result["ParsedResults"][0]["ParsedText"]
        result2 = medical_system.analyze('this is the medicin i am taking now: '+text, None)
        return {"answer": result2}
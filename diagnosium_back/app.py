import base64 # Add base64 import
import logging
from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware # Import CORS middleware
from pydantic import BaseModel
from agent import MedicalAI
import httpx


# Setup basic logging (if not already present)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

# New Pydantic model for the image payload
class ImagePayload(BaseModel):
    image_base64: str
    filename: str # Keep filename for potential use or logging


@app.post("/message")
async def post_message(message: Message):
    patient_input = message.content
    patient_data = message.patient_data
    result = medical_system.analyze(patient_input, patient_data)
    
    # Return the response in the format expected by the frontend
    return {"answer": result}


@app.post("/extract-text")
# Change the input parameter from File(...) to our new ImagePayload model
async def extract_text(payload: ImagePayload):
    logger.info(f"Received request for /extract-text with JSON payload.")
    try:
        # Decode the base64 string
        try:
            # Remove the data URL prefix if it exists (e.g., "data:image/jpeg;base64,")
            if "," in payload.image_base64:
                base64_data = payload.image_base64.split(',', 1)[1]
            else:
                base64_data = payload.image_base64

            image_bytes = base64.b64decode(base64_data)
            logger.info(f"Successfully decoded base64 image ({len(image_bytes)} bytes). Filename: {payload.filename}")
        except (base64.binascii.Error, IndexError, TypeError) as decode_error:
            logger.error(f"Error decoding base64 image: {decode_error}", exc_info=True)
            return {"answer": {
                "response": f"Invalid base64 image data received: {decode_error}"
            }}
        except Exception as e:
             logger.error(f"Unexpected error during base64 decoding: {e}", exc_info=True)
             return {"answer": {
                "response": f"Server error during image decoding."
             }}


        async with httpx.AsyncClient() as client:
            logger.info("Sending decoded image bytes to OCR.space API...")
            # Send the decoded bytes to the OCR API
            # Note: httpx handles the multipart encoding here correctly when given bytes
            response = await client.post(
                "https://api.ocr.space/parse/image",
                data={"apikey": API_KEY, "language": "eng"},
                # Pass the decoded bytes directly
                files={"filename": (payload.filename, image_bytes, "image/jpeg")}, # Assuming JPEG, adjust if needed
            )
            logger.info(f"OCR.space API response status: {response.status_code}")

            result = response.json()
            logger.info(f"OCR.space API response JSON: {result}")

            # --- Keep the rest of the OCR result processing and AI analysis logic the same ---
            # Validate OCR API response structure
            if response.status_code != 200 or "ParsedResults" not in result or not result["ParsedResults"] or "ParsedText" not in result["ParsedResults"][0]:
                error_msg = result.get("ErrorMessage", ["Unknown OCR Error"])[0] if isinstance(result.get("ErrorMessage"), list) else result.get("ErrorMessage", "Unknown OCR Error")
                logger.error(f"OCR Error: {error_msg}")
                return {"answer": {
                    "prompt_injection_detected": False,
                    "extracted_symptoms": [],
                    "is_emergency": False,
                    "diagnosis": f"Error: {error_msg}",
                    "response": f"I couldn't read the text in that image: {error_msg}"
                }}

            text = result["ParsedResults"][0]["ParsedText"]
            logger.info(f"Extracted text: '{text[:100]}...'") # Log first 100 chars
            if not text.strip():
                logger.warning("Extracted text is empty or whitespace.")
                return {"answer": {
                    "response": "I couldn't detect any text in the image. Please try again with a clearer image."
                }}

            # Process the extracted text with the AI
            logger.info("Sending extracted text to MedicalAI for analysis...")
            result2 = medical_system.analyze('this is the medication I am taking now: '+text, None)
            logger.info(f"MedicalAI analysis result: {result2}")
            return {"answer": result2}
            # --- End of existing logic ---

    except Exception as e:
        logger.error(f"Unhandled exception in /extract-text: {e}", exc_info=True) # Log full traceback
        return {"answer": {
            "prompt_injection_detected": False,
            "extracted_symptoms": [],
            "is_emergency": False,
            "diagnosis": f"Error processing image: {str(e)}",
            "response": f"Sorry, I encountered an unexpected server error while processing your image."
        }}
import os
import re
from groq import Groq
from typing import List, Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

from vector_store import VectorStore

# Set API key
os.environ["GROQ_API_KEY"] = "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"

class MedicalAI:
    """
    Unified medical AI system that handles prompt injection detection, symptom extraction, emergency assessment, and medical diagnosis in a single function.
    """
    
    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        # Initialize components
        self.model = model_name
        self.client = Groq(api_key=os.environ["GROQ_API_KEY"])
        self.vector_store = VectorStore()
        self.patient_data = {}
        self.conversation_history = []  # Add this to store conversation history

    def set_patient_data(self, patient_data: Dict[str, Any]) -> None:
        """Set patient data for use in assessments."""
        self.patient_data = patient_data
    
    def add_medical_reference(self, content: str, metadata: Dict[str, Any] = None) -> None:
        """Add medical knowledge to the system."""
        self.vector_store.add_document(content, metadata)
    
    def load_medical_knowledge(self, folder_path: str, file_extensions: List[str] = ['.txt', '.md']) -> None:
        """Load medical knowledge from a folder of files."""
        self.vector_store.add_documents_from_folder(folder_path, file_extensions)
        self.vector_store.build_index()
    
    def build_index(self) -> None:
        """Build the vector index after adding documents."""
        self.vector_store.build_index()
    
    def _format_patient_context(self) -> str:
        """Format patient data into a readable context string."""
        if not self.patient_data:
            return ""
            
        patient_context = "Patient Information:\n"
        for key, value in self.patient_data.items():
            patient_context += f"- {key}: {value}\n"
        return patient_context
    
    def analyze(self, user_input: str, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unified analysis: performs prompt injection detection, symptom extraction, emergency assessment, and diagnosis in a single LLM call.
        Returns a dictionary with all analysis results.
        """
        self.set_patient_data(patient_data or {})
        patient_context = self._format_patient_context()

        system_message = (
            "You are a medical AI assistant. and you will answer the user question about his health situation.\n"
            "you are a professional doctor so you will follow these steps:\n"
            "if the user doesn't provide any symptoms, you will ask him to provide them.\n"
            "ask about personal info about the user like age, gender, weight, height\n"
            "if the user provides symptoms, you will extract them and check if they are related to any medical condition and when did they start occurring.\n"
            "after that, you will ask if the user is taking medications or pills, and any medical history of the family.\n"
            "social history is also important, so you will ask about the user's job and if he is exposed to any chemicals or toxins.\n"
            "always keep your questions short and to the point.\n"
            "after each question you will provide this exact answer:"
            '{'
            '  "prompt_injection_detected": true/false,\n'
            '  "extracted_symptoms": [list of symptoms],\n'
            '  "is_emergency": true/false,\n'
            '  "diagnosis": "..."\n'
            '}'
            "after you have all the necessary details you can give a diagnosis.\n"
            " if you see that the user is in an emergency situation, you will explain why and suggest to him to go to the hospital.\n"
            f"\nPatient context:\n{patient_context}"
        )
        

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_input}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.1,
            max_tokens=256,
        )
        import json
        try:
            result = json.loads(response.choices[0].message.content)
            print('LLM response:', result)
        except Exception:
            # Fallback if LLM response is not valid JSON
            print('Invalid JSON response:', response.choices[0].message.content)
            result = {
                "prompt_injection_detected": False,
                "extracted_symptoms": [],
                "is_emergency": False,
                "emergency_explanation": "Could not parse response.",
                "diagnosis": response.choices[0].message.content.strip()
            }
        # Update patient_data with extracted symptoms
        if result.get("extracted_symptoms"):
            existing = self.patient_data.get("reported_symptoms", [])
            updated = list(set(existing + result["extracted_symptoms"]))
            self.patient_data["reported_symptoms"] = updated
            result["all_reported_symptoms"] = updated
        result["patient_data"] = self.patient_data


# Example usage
if __name__ == "__main__":
    # Create the unified medical AI system
    medical_ai = MedicalAI()
    
    # Add medical knowledge
    medical_ai.add_medical_reference("""
    Common cold symptoms include runny nose, sore throat, coughing, sneezing, headaches, 
    and body aches. It typically resolves within 7-10 days without specific treatment.
    """, {"condition": "Common Cold"})
    
    medical_ai.add_medical_reference("""
    Influenza (flu) symptoms are similar to cold but more severe and include fever, 
    muscle aches, fatigue, and can last 1-2 weeks. Complications can be serious.
    """, {"condition": "Influenza"})
    
    # Build knowledge index
    medical_ai.build_index()
    
    # Set patient data
    medical_ai.set_patient_data({
        "age": 35,
        "sex": "male",
        "allergies": "penicillin",
        "chronic_conditions": "asthma",
        "medications": "albuterol inhaler",
        "previous_surgeries": "appendectomy (2015)"
    })
    
    # One-line analysis example
    print("\n=== Example: Medical Analysis ===")
    user_input = "I have severe chest pain radiating to my left arm and difficulty breathing"
    
    # THIS IS THE ONE LINE THAT GIVES ALL THREE ANSWERS:
    result = medical_ai.analyze(user_input)
    
    # Display results
    print(f"User input: {user_input}")
    print(f"Prompt injection detected: {result['prompt_injection_detected']}")
    print(f"Emergency status: {'YES - ' + result['emergency_explanation'] if result['is_emergency'] else 'No emergency'}")
    print(f"\nResponse: {result['response'][:300]}...")  # First 300 chars


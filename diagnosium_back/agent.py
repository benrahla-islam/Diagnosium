import os
import re
import json  # Move json import to top level
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
            return "No patient information provided." # Return specific string if empty
            
        patient_context = "Patient Information:\n"
        # Define preferred order or specific formatting if needed
        fields_order = ['name', 'age', 'gender', 'allergies', 'chronic_conditions', 'medications', 'medical_history', 'reported_symptoms']
        for key in fields_order:
            value = self.patient_data.get(key)
            if value: # Only include fields that have a value
                 # Format list of symptoms nicely
                 if key == 'reported_symptoms' and isinstance(value, list):
                     patient_context += f"- Reported Symptoms: {', '.join(value)}\n"
                 else:
                     # Capitalize key for display and handle potential None values explicitly
                     display_key = key.replace('_', ' ').capitalize()
                     patient_context += f"- {display_key}: {value}\n"
        
        # Include any other fields not in the preferred order
        for key, value in self.patient_data.items():
            if key not in fields_order and value:
                 display_key = key.replace('_', ' ').capitalize()
                 patient_context += f"- {display_key}: {value}\n"

        return patient_context
    
    def analyze(self, user_input: str, patient_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Unified analysis: performs prompt injection detection, symptom extraction, emergency assessment, and diagnosis in a single LLM call.
        Returns a dictionary with all analysis results.
        """
        # Update internal patient data if new data is provided
        if patient_data:
            # Merge new data, potentially overwriting old values if keys match
            self.patient_data.update({k: v for k, v in patient_data.items() if v is not None and v != ''})

        patient_context = self._format_patient_context()
        
        # Include conversation history for context
        history_context = ""
        if self.conversation_history:
            history_context = "Previous conversation:\n" + "\n".join([
                f"User: {exchange['user']}\nAI: {exchange['ai']}" 
                for exchange in self.conversation_history[-3:]  # Last 3 exchanges
            ]) + "\n\n"
        
        # Track conversation progress to determine when to give diagnosis
        conversation_length = len(self.conversation_history)
        # Check if any symptoms have been reported either via patient info or extracted
        has_symptoms = bool(self.patient_data.get("reported_symptoms")) 
        
        system_message = (
            "You are a medical AI assistant that helps users with health concerns.\n"
            "Follow this approach:\n"
            "1. Review the provided patient information (if any).\n"
            "2. If no symptoms are mentioned in the current query or patient history, ask for symptoms first.\n"
            "3. Collect essential information like age, gender, medical history (allergies, conditions, medications) if missing and relevant.\n"
            "4. IMPORTANT: After 2-3 exchanges, if you have symptoms, provide a real medical analysis and possible diagnosis based on all available information (symptoms, patient data, conversation history).\n"
            "5. For emergencies, clearly flag them and advise seeking immediate care.\n"
            "6. Only ask 1-2 clarifying questions at a time.\n"
            "7. Avoid redundancy. Don't ask for information already provided in the 'Patient Information' section unless clarification is needed.\n"
            "\n"
            f"Current conversation stage: {'Information gathering' if conversation_length < 2 or not has_symptoms else 'Provide diagnosis and analysis'}\n"
            f"You have collected {conversation_length} exchanges so far.\n"
            # f"Symptoms collected: {self.patient_data.get('reported_symptoms', [])}\n" # Redundant with patient_context
            "\n"
            f"{history_context}{patient_context}" # Combined history and patient context
        )
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_input}
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=512,  # Increased token limit for more comprehensive responses
            )
            
            try:
                # Attempt to extract structured JSON from the response
                response_text = response.choices[0].message.content.strip()
                json_match = re.search(r'({[\s\S]*})', response_text)
                
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    # If no valid JSON found, use the entire response as diagnosis
                    result = {
                        "prompt_injection_detected": False,
                        "extracted_symptoms": [],
                        "is_emergency": False,
                        "emergency_explanation": "",
                        "diagnosis": response_text
                    }
                print('LLM response:', result)
            except Exception as json_err:
                # Fallback if LLM response is not valid JSON
                response_text = response.choices[0].message.content.strip()
                print('Invalid JSON response:', response_text)
                print(f'JSON parsing error: {json_err}')
                result = {
                    "prompt_injection_detected": False,
                    "extracted_symptoms": [],
                    "is_emergency": False,
                    "emergency_explanation": "Could not parse response.",
                    "diagnosis": response_text
                }
            
            # Add human-readable response for the user interface
            result["response"] = result.get("diagnosis", "")
            
            # Update patient_data with extracted symptoms
            if result.get("extracted_symptoms"):
                # Ensure reported_symptoms exists and is a list
                if "reported_symptoms" not in self.patient_data or not isinstance(self.patient_data["reported_symptoms"], list):
                    self.patient_data["reported_symptoms"] = []
                
                # Add only new symptoms
                new_symptoms = [s for s in result["extracted_symptoms"] if s not in self.patient_data["reported_symptoms"]]
                if new_symptoms:
                    self.patient_data["reported_symptoms"].extend(new_symptoms)
                
                result["all_reported_symptoms"] = self.patient_data["reported_symptoms"] # Return the updated list
            
            # Add to conversation history
            self.conversation_history.append({
                "user": user_input,
                "ai": result["response"]
            })
            
            # Return the potentially updated patient data along with the result
            result["patient_data"] = self.patient_data 
            return result
            
        except Exception as e:
            # Handle API errors
            error_msg = f"Error processing request: {str(e)}"
            print(error_msg)
            return {
                "prompt_injection_detected": False,
                "extracted_symptoms": [],
                "is_emergency": False,
                "diagnosis": error_msg,
                "response": error_msg,
                "patient_data": self.patient_data # Return current patient data even on error
            }

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
    
    # Set patient data (using 'gender' now)
    initial_patient_data = {
        "name": "John Doe",
        "age": 35,
        "gender": "Male", # Changed from 'sex'
        "allergies": "penicillin",
        "chronic_conditions": "asthma",
        "medications": "albuterol inhaler",
        "medical_history": "appendectomy (2015)" # Changed from 'previous_surgeries'
    }
    # medical_ai.set_patient_data(initial_patient_data) # Set initial data if needed, or pass via analyze
    
    # One-line analysis example
    print("\n=== Example: Medical Analysis ===")
    user_input = "I have severe chest pain radiating to my left arm and difficulty breathing"
    
    # Pass initial patient data with the first call
    result = medical_ai.analyze(user_input, initial_patient_data) 
    
    # Display results
    print(f"User input: {user_input}")
    print(f"Patient Data Used:\n{medical_ai._format_patient_context()}") # Show formatted context used
    print(f"Prompt injection detected: {result['prompt_injection_detected']}")
    print(f"Emergency status: {'YES - ' + result.get('emergency_explanation', '') if result['is_emergency'] else 'No emergency'}")
    print(f"\nResponse: {result['response'][:300]}...")  # First 300 chars

    # Example follow-up
    print("\n=== Example: Follow-up ===")
    user_input_2 = "The pain started about 30 minutes ago after climbing stairs."
    # No need to pass patient_data again, it's stored internally now
    result_2 = medical_ai.analyze(user_input_2) 
    print(f"User input: {user_input_2}")
    print(f"Patient Data Used:\n{medical_ai._format_patient_context()}") # Show context again
    print(f"\nResponse: {result_2['response'][:300]}...")


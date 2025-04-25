# Diagnosium

![Diagnosium Logo](diagnosium_front/static/logo.png)

Diagnosium is an AI-powered medical diagnostic assistant that helps users understand their symptoms, scan medications, and locate nearby medical facilities.

## 🚀 Features

### 🤖 AI-Powered Diagnostics
- Real-time chat interface for symptom analysis
- Context-aware responses based on patient information
- Emergency detection for critical medical situations

### 📝 Patient Management
- Store and manage patient information
- Track medical history, allergies, and chronic conditions
- Personalized diagnostics based on patient profiles

### 📷 Medication Scanner
- Scan medication labels using your device camera
- Extract text from images using OCR technology
- Get instant analysis of your medications

### 🗺️ Medical Facility Locator
- Find nearby hospitals, pharmacies, and clinics
- Geolocation integration with interactive maps
- User-friendly navigation to medical services

## 🔧 Technical Architecture

Diagnosium uses a modern two-tier architecture:
- **Frontend**: Flask web application with Vue.js
- **Backend**: FastAPI service with AI medical agent

## 📋 Prerequisites

- Python 3.8 or later
- pip (Python package installer)
- Web browser with JavaScript enabled
- Camera access (for medication scanning feature)
- Location access (for medical facility mapping)

## ⚙️ Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/diagnosium.git
   cd diagnosium
   ```

2. Install dependencies:
   ```
   pip install -e .
   pip install -r requirements.txt
   ```

## 🚀 Getting Started

### Starting the Backend Server

1. Navigate to the backend directory:
   ```
   cd diagnosium_back
   ```

2. Start the FastAPI server:
   ```
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```
   The backend API will be available at http://localhost:8000

### Starting the Frontend Server

1. Open a new terminal window and navigate to the frontend directory:
   ```
   cd diagnosium_front
   ```

2. Start the Flask server:
   ```
   python app.py
   ```
   The web application will be available at http://localhost:5000

## 🌐 API Endpoints

- `POST /message`: Send a text message for medical analysis
- `POST /extract-text`: Upload an image for text extraction and medication analysis

## 📱 Using the Application

1. Open your browser and go to http://localhost:5000
2. Create a patient profile by clicking on "Patient Info"
3. Start a conversation with the AI by typing in the chat box
4. To scan medication, click the camera icon and take a photo
5. View nearby medical facilities shown on the map after interacting with the chat

## 🔒 Privacy & Security

Diagnosium is designed with privacy in mind. All patient information is stored locally and only transmitted securely when needed for analysis.

## ⚠️ Disclaimer

Diagnosium is for informational purposes only and does not replace professional medical advice, diagnosis, or treatment. Always consult with a qualified healthcare provider for medical concerns.

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

If you encounter any issues or have questions, please open an issue on our GitHub repository or contact support@diagnosium.com.
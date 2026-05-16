# Phase 1 Documentation: Voice-to-JSON Pipeline
1. ## Architectural Overview
Phase 1 established the foundational audio-processing brain and user interface for an agentic voice-driven form-filling application. The system captures raw user audio via a web browser, transmits it to a local backend, processes the speech using an offline AI model, and returns a structured JSON object containing the transcribed text, detected language, and a calculated confidence score.

2. ## Environment & Dependencies
### Backend Stack (Python)
Virtual Environment: Standard Python venv

Core Framework: fastapi (API routing)

Server: uvicorn (ASGI web server)

Audio Handling: python-multipart, av

AI Engine: faster-whisper (running small/tiny model locally on CPU with int8 compute type)

### Frontend Stack (JavaScript)
Runtime Environment: Node.js (LTS version)

Package Manager: npm

Build Tool: Vite

UI Framework: React

3. ## Project File Structure
main.py: The FastAPI backend application containing the /api/v1/transcribe endpoint. It handles temporary file storage, Whisper model execution, and mathematical confidence calculation based on log probabilities.

frontend/: The Vite workspace directory.

frontend/src/App.jsx: The primary React component managing browser microphone permissions (MediaRecorder API), recording .webm audio blobs, and conditionally rendering UI based on the AI's confidence score.

4. ## Key Findings & Research Insights
--The "Ghost Mic" Phenomenon: Browsers and OS security settings can successfully record and transmit "silent" audio files if the wrong physical microphone is selected or desktop app privacy settings are disabled.

--Proper Noun Confidence Drops: Standard AI models struggle with regional proper nouns (e.g., "Shuhini Shudu"). The model successfully transcribes phonetics but returns a mathematically low confidence score (e.g., 0.52), triggering the system's needs_rerecord fallback threshold (0.65).

--Short-Audio Language Hallucination: When processing short, slightly noisy audio clips, smaller Whisper models (tiny/small) occasionally suffer from mathematical confusion in language detection, defaulting to anomalies like Norwegian Nynorsk (nn).

--Resolution: Enforcing expected language parameters (e.g., language="en") within the model.transcribe() function stabilizes the output for targeted regional deployments.

5. ## Quick-Start Runbook
### Option A: Run Backend Independently (API Testing Mode)
Use this method if you only want to test the Python logic or upload pre-recorded audio files using FastAPI's built-in Swagger UI, without loading the React frontend.

Open a terminal in your root project folder.

Activate the virtual environment:terminal/bash

 .\venv\Scripts\activate
 
 step1: ctrl+shift+ P 
 step2: select interpretor


Start the backend server:terminal/bash

  uvicorn main:app --reload

Once you run that second command, wait a few seconds until you see the Application startup complete message.

Test the API: Open your browser and navigate to the interactive docs:
👉 http://127.0.0.1:8000/docs

### Option B: Run Full-Stack (Voice Application Mode)
Use this method to launch the complete end-to-end application with the browser microphone interface.

Start the Backend: (Follow Steps 1-3 from Option A above).

Open a second, split terminal (Ctrl+Shift+5 in VS Code).

Navigate to the frontend directory: terminal/bash

 cd frontend

Start the Vite development server:terminal/bash

npm run dev

Launch the UI: Hold Ctrl and click the local URL (usually http://localhost:5173/) in your terminal to open the web app.

6. ## Actionable Improvements & Hardening
As you scale this prototype for production or user testing, consider implementing the following architectural improvements:

1. Dynamic Confidence Thresholding
The Problem: A static threshold (e.g., 0.65) punishes regional proper nouns and code-switching, leading to false "needs re-record" loops.

Suggested Implementation: Instead of a hardcoded constant in main.py, calculate a dynamic threshold based on the detected language or the length of the audio segment. Alternatively, pass a strictness parameter from the React frontend so the UI can decide how forgiving the AI should be depending on which form field it is asking for (e.g., strict for numbers, forgiving for names).

2. Transition to large-v3 with Quantization
The Problem: The small and tiny models hallucinate languages and struggle with heavy regional accents.

Suggested Implementation: Upgrade back to "large-v3". To prevent memory crashes on a local CPU, strictly enforce quantization by ensuring compute_type="int8" is set.

code: python

model = faster_whisper.WhisperModel("large-v3", device="cpu", compute_type="int8")

3. Non-Blocking Audio Processing
The Problem: Currently, the FastAPI endpoint blocks the main thread while Whisper transcribes the audio. If two users submit audio at the exact same time, the second user has to wait for the first to finish.

Suggested Implementation: Utilize FastAPI's BackgroundTasks or integrate a task queue like Celery/Redis. You can immediately return a task_id to the React frontend, and have the frontend poll a new /status/{task_id} endpoint until the transcription is complete.

4. Advanced Frontend Audio Pre-Processing
The Problem: Background noise in rural environments significantly degrades ASR accuracy.

Suggested Implementation: Enhance the getUserMedia constraints in App.jsx. Ensure that built-in browser audio processing is fully utilized before the blob is ever sent to the backend:

code: javascript

audio: {
  noiseSuppression: true,
  echoCancellation: true,
  autoGainControl: true,
  sampleRate: 16000 // Whisper natively downsamples to 16kHz anyway
}
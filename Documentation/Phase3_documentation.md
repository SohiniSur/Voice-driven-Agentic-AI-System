Phase 3 Documentation: ReAct Dialogue Manager & Full-Stack Integration
1. Architectural Overview
Phase 3 establishes the core "Brain" of the agentic system. It combines the audio transcriptions from Phase 1 (the "Ears") with the structured JSON schema from Phase 2 (the "Map"). Using a ReAct (Reasoning + Acting) pattern, the Dialogue Manager dynamically tracks conversation state, evaluates missing information, and formulates the next conversational prompt. Finally, this phase wires the Python logic engine into the FastAPI backend and connects it to the React frontend for a complete, real-time user loop.

2. Environment & Dependencies
Backend Orchestration: FastAPI (connecting Whisper, Gemini, and React).

State Management Engine: agent.py (Custom Python class).

AI Engine: google-genai (Gemini 2.5 Flash for rapid, strictly-typed logical reasoning).

Data Validation: pydantic (Enforcing the AgentResponse schema).

Frontend UI: React (App.jsx) using useEffect and fetch for real-time state polling.

3. Core Concept: Neuro-Symbolic Design
Initial testing relied purely on the LLM to calculate differences between the target schema and the collected data. This led to "State Hallucination" (detailed below). To build a production-grade system, the architecture was shifted to a Neuro-Symbolic approach:

Symbolic (Deterministic): Standard Python list comprehensions are used to mathematically calculate the exact missing_fields from the schema.

Neural (Probabilistic): The LLM is restricted solely to natural language understanding (extracting data from messy user audio) and generation (phrasing the next question politely).

Temperature: Set to 0.0 to force maximum determinism and prevent the AI from improvising field keys.

4. Full-Stack Integration Flow
Initialization: React loads and immediately calls GET /api/v1/init. FastAPI reads schema.json, initializes the Dialogue Manager, and returns the first question.

Audio Ingestion: User speaks into the React UI; the .webm blob is sent to POST /api/v1/transcribe.

Transcription: Faster-Whisper converts audio to text, saving an audit trail to last_transcription.json.

Reasoning: The text is passed to the DialogueManager. Python calculates missing fields; Gemini extracts the new value and generates the next question.

State Update: FastAPI saves the new state, writes a debug log (last_interaction.json), and returns the updated payload to React.

UI Render: React updates the Agent Question box and the Live Form Data view in real-time.

5. Troubleshooting, Errors & Mitigations
During the development of Phase 3, several critical architectural bugs were identified and resolved:

Error 1: FileNotFoundError: schema.json
Symptom: The agent.py script crashed on boot.

Root Cause: The Dialogue Manager attempted to load the target schema before the Phase 2 extraction script had physically saved the schema.json file to the directory.

Resolution: Added local file-saving logic to schema_extractor.py and implemented a try/except fallback in FastAPI to gracefully report a "System offline" status if the map is missing.

Error 2: "Agent Amnesia" (State Hallucination Loop)
Symptom: The agent repeatedly asked for the user's name, saving it under slightly different keys (e.g., fname, then firstname, then lastname).

Root Cause: LLMs evaluate data semantically, not literally. When instructed to find missing fields, Gemini treated fname and firstname as the same concept, hallucinated new JSON keys, and failed to satisfy the strict schema requirements.

Resolution: Implemented Neuro-Symbolic logic. Python now calculates the missing fields deterministically and feeds a strict list to Gemini. The prompt was updated to enforce exact, case-sensitive matching, and the LLM temperature was dropped to 0.0.

Error 3: UI Visibility (White-on-White Text)
Symptom: Extracted text in the React frontend was invisible.

Root Cause: Browser dark-mode defaults clashed with the custom #f8f9fa background container in Vite.

Resolution: Applied explicit inline CSS (color: 'black') to the result containers in App.jsx.

Error 4: The Generator Exhaustion Bug (Always Low Confidence)
Symptom: Every voice recording returned a "Low confidence. Could you say that again?" error, even with crystal clear audio and a low threshold (0.10).

Root Cause: Faster-Whisper's model.transcribe() returns a Python generator. The code iterated through the generator once to extract the text. When the code attempted to iterate through it a second time to calculate the confidence score, the generator was empty, resulting in a sum of 0 and triggering the failure threshold.

Resolution: Converted the generator immediately into a permanent object (segments_list = list(segments)), allowing multiple iterations for both text extraction and mathematical scoring. Additionally, vad_filter=True was added to prevent Whisper from transcribing background static.

6. Quick-Start Runbook
To launch the full interactive prototype:

Terminal 1 (Backend):

Bash
.\venv\Scripts\activate
python schema_extractor.py  # (Optional: Only if a new schema is needed)
uvicorn main:app --reload
Terminal 2 (Frontend):

Bash
cd frontend
npm run dev
Open http://localhost:5173 in your browser. The agent will automatically greet you and prompt you for the first missing field.
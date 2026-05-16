from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import faster_whisper
import math
import tempfile
import os
import json  # <-- 1. NEW: Imported the JSON library
from agent import DialogueManager # <-- 1. Import your Phase 3 Agent!
from form_filler import auto_fill_form # <-- 2. Import your Phase 5 Form Filler!
# --- 1. NEW PHASE 6 CODE: Imports ---
from gtts import gTTS
import base64
# ------------------------------------
app = FastAPI(title="Form Assistant ASR API")

# --- ADD THIS CORS CONFIGURATION ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (good for local development)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (POST, GET, etc.)
    allow_headers=["*"],  # Allows all headers
)
# -----------------------------------

#model = faster_whisper.WhisperModel("large-v3", device="cpu", compute_type="int8")
model = faster_whisper.WhisperModel("small", device="cpu", compute_type="int8")
CONFIDENCE_THRESHOLD = 0.10  

# --- 2. BOOT UP THE AGENT ---
print("🧠 Initializing Dialogue Manager...")
try:
    form_agent = DialogueManager(schema_path="schema.json")
    # Set the very first question the agent will ask
    last_asked_question = f"Hello! I am here to help you fill out the {form_agent.schema.get('form_purpose', 'form')}. What is your full name?"
except FileNotFoundError:
    print("⚠️ ERROR: schema.json not found! Please run schema_extractor.py first.")
    form_agent = None
    last_asked_question = "System offline. Missing schema map."

@app.get("/api/v1/init")
async def get_initial_state():
    global last_asked_question
    return {
        "agent_question": last_asked_question,
        "form_state": form_agent.collected_data if form_agent else {}
    }

##modified for AI Agentic Architecture
@app.post("/api/v1/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    global last_asked_question # Let the endpoint access and update the current question
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
        temp_audio.write(await file.read())
        temp_audio_path = temp_audio.name
    try:
        # Phase 1: Transcribe the audio (Added vad_filter=True to stop hallucinations!)
        segments, info = model.transcribe(temp_audio_path, beam_size=5, vad_filter=True)
        
        # 💡 THE FIX: Convert the generator to a permanent list immediately!
        segments_list = list(segments)
        
        # Now we can safely loop through the list multiple times
        full_text = "".join(segment.text + " " for segment in segments_list).strip()
        
        # Calculate confidence using the safe list
        total_confidence = sum(math.exp(s.avg_logprob) for s in segments_list)
        segment_count = len(segments_list)
        avg_confidence = (total_confidence / segment_count) if segment_count > 0 else 0
        
        print(f"📊 Debug - Segment count: {segment_count}, Avg Confidence: {avg_confidence:.2f}")

        if avg_confidence < CONFIDENCE_THRESHOLD or segment_count == 0:
             return {"needs_rerecord": True, "text": full_text}

        # --- PHASE 3: THE BRAIN TAKES OVER ---
        print(f"🗣️ User said: {full_text}")
        
        # 1. Ask Gemini to extract data and figure out the next step
        agent_result = form_agent.process_user_input(full_text, last_asked_question)
        
        # 2. Save the extracted data into our Python dictionary (state)
        extracted_field = agent_result.get("extracted_field_name")
        extracted_val = agent_result.get("extracted_value")
        
        if extracted_field and extracted_val:
            form_agent.collected_data[extracted_field] = extracted_val
            print(f"💾 Saved: {extracted_field} = {extracted_val}")

        # 3. Figure out the next question
        is_complete = agent_result.get("is_form_complete", False)
        if is_complete:
            last_asked_question = "Thank you! All required information has been collected. We are done!"
            # --- NEW: Print the visual dashboard! ---
            form_agent.print_usage_stats()

            # --- NEW PHASE 5 CODE: Trigger Playwright ---
            # Replace this URL with the actual URL of the form you scraped in Phase 2
            target_url = form_agent.schema.get('form_url', 'file:///C:/Users/sohin/agentic_ai_project/bank_form.html') 

            # We run this in the background so it doesn't freeze the FastAPI server
            import threading
            threading.Thread(target=auto_fill_form, args=(target_url, form_agent.collected_data)).start()
            # --------------------------------------------
        else:
            last_asked_question = agent_result.get("next_question", "Could you repeat that?")

        # --- 2. NEW PHASE 6 CODE: Generate Audio Feedback ---
        try:
            # 'co.in' gives it an Indian English accent!
            tts = gTTS(text=last_asked_question, lang='en', tld='co.in')
            tts.save("agent_voice.mp3")
            
            with open("agent_voice.mp3", "rb") as audio_file:
                encoded_audio = base64.b64encode(audio_file.read()).decode('utf-8')
        except Exception as e:
            print(f"⚠️ TTS Error: {e}")
            encoded_audio = None
        # ----------------------------------------------------

        # 4. Send the master payload back to the React UI
        response_payload = {
            "needs_rerecord": False,
            "text": full_text,
            "agent_question": last_asked_question,
            "form_state": form_agent.collected_data,
            "is_complete": is_complete,
            "audio_base64": encoded_audio
        }
        
        with open("last_interaction.json", "w", encoding="utf-8") as f:
            json.dump(response_payload, f, indent=4)

        return response_payload

    finally:
        os.remove(temp_audio_path)

    '''
    # not working again due to generator bug
    try:
        # Phase 1: Transcribe the audio
        segments, info = model.transcribe(temp_audio_path, beam_size=5)
        full_text = "".join(segment.text + " " for segment in segments).strip()
        
        # Calculate confidence
        total_confidence = sum(math.exp(s.avg_logprob) for s in segments)
        segment_count = len(list(segments))
        avg_confidence = (total_confidence / segment_count) if segment_count > 0 else 0
        
        if avg_confidence < CONFIDENCE_THRESHOLD:
             return {"needs_rerecord": True, "text": full_text}

        # --- PHASE 3: THE BRAIN TAKES OVER ---
        print(f"🗣️ User said: {full_text}")
        
        # 1. Ask Gemini to extract data and figure out the next step
        agent_result = form_agent.process_user_input(full_text, last_asked_question)
        
        # 2. Save the extracted data into our Python dictionary (state)
        extracted_field = agent_result.get("extracted_field_name")
        extracted_val = agent_result.get("extracted_value")
        
        if extracted_field and extracted_val:
            form_agent.collected_data[extracted_field] = extracted_val
            print(f"💾 Saved: {extracted_field} = {extracted_val}")

        # 3. Figure out the next question
        is_complete = agent_result.get("is_form_complete", False)
        if is_complete:
            last_asked_question = "Thank you! All required information has been collected. We are done!"
        else:
            last_asked_question = agent_result.get("next_question", "Could you repeat that?")

        # 4. Send the master payload back to the React UI
        response_payload = {
            "needs_rerecord": False,
            "text": full_text,
            "agent_question": last_asked_question,
            "form_state": form_agent.collected_data,
            "is_complete": is_complete
        }
        
        # (Optional) Save the full payload for debugging
        with open("last_interaction.json", "w", encoding="utf-8") as f:
            json.dump(response_payload, f, indent=4)

        return response_payload
    
    finally:
        os.remove(temp_audio_path)

        ## previous version

@app.post("/api/v1/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
        temp_audio.write(await file.read())
        temp_audio_path = temp_audio.name

        # --- ADD THIS LINE ---
        print(f"Received file size: {os.path.getsize(temp_audio_path)} bytes")

    try:
        segments, info = model.transcribe(temp_audio_path, beam_size=5)
        full_text = ""
        total_confidence = 0
        segment_count = 0

        for segment in segments:
            full_text += segment.text + " "
            prob = math.exp(segment.avg_logprob)
            total_confidence += prob
            segment_count += 1

        avg_confidence = (total_confidence / segment_count) if segment_count > 0 else 0
        needs_rerecord = avg_confidence < CONFIDENCE_THRESHOLD

        # --- 2. MODIFIED: Package the data into a variable first ---
        response_payload = {
            "text": full_text.strip(),
            "language": info.language,
            "language_probability": round(info.language_probability, 2),
            "confidence_score": round(avg_confidence, 2),
            "needs_rerecord": needs_rerecord
        }
        
        # --- 3. NEW: Save the payload locally to a file ---
        with open("last_transcription.json", "w", encoding="utf-8") as f:
            json.dump(response_payload, f, indent=4)
            
        print("💾 Saved user audio data to last_transcription.json")

        # --- 4. MODIFIED: Return that variable to the React frontend ---
        return response_payload
        
        ##version before modifications: comment this out if you want to see the original
        ###
         return {
            "text": full_text.strip(),
            "language": info.language,
            "language_probability": round(info.language_probability, 2),
            "confidence_score": round(avg_confidence, 2),
            "needs_rerecord": needs_rerecord
        }
        ###
        '''
    
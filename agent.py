import time
from datetime import datetime
import json
import os
import re
import hashlib
from pathlib import Path
from huggingface_hub import InferenceClient
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------
# 1. Define the strict output format for the Agent
# ---------------------------------------------------------
class AgentResponse(BaseModel):
    extracted_field_name: str | None = None
    extracted_value: str | None = None
    next_missing_field: str | None = None
    next_question: str | None = None
    is_form_complete: bool

# ---------------------------------------------------------
# 2. The Dialogue Manager Class (Enterprise Edition)
# ---------------------------------------------------------
class DialogueManager:
    def __init__(self, schema_path="schema.json", cache_dir="agent_cache"):
        print("🧠 Booting up Enterprise Dialogue Manager (Hugging Face + Caching)...")
        # --- NEW: Record exact session start time ---
        self.session_start_time = datetime.now()
        self.session_id = self.session_start_time.strftime("%Y%md_%H%M%S") 
        print(f"⏱️ Session started at: {self.session_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)
            
        # --- HUGGING FACE CLIENT ---
        hf_token = os.environ.get("HF_TOKEN")
        if not hf_token:
            print("⚠️ WARNING: HF_TOKEN is missing from your .env file!")
        self.client = InferenceClient(api_key=hf_token)
        
        self.collected_data = {}  
        self.pending_field = None
        self.pending_value = None
        self.rejection_count = 0  # <-- NEW: Tracks consecutive rejections
        
        # --- API MONITORING & CACHING ---
        self.api_call_count = 0
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "response_cache.json"
        self.cache = self._load_cache()
        print(f"📦 Cache loaded: {len(self.cache)} previously seen interactions.")

        # --- Load Geography Data ---
        try:
            with open("india_geography.json", "r", encoding="utf-8") as f:
                geo_data = json.load(f)
                self.valid_states = {state.lower(): state for state in geo_data.keys()}
                self.valid_districts = {dist.lower(): state for state, dists in geo_data.items() for dist in dists}
        except FileNotFoundError:
            print("⚠️ Warning: india_geography.json not found. Geography validation disabled.")
            self.valid_states = {}
            self.valid_districts = {}

    # --- CACHING HELPERS ---
    def _load_cache(self):
        if self.cache_file.exists():
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)

    def _call_llm(self, prompt: str, is_json: bool = True, max_tokens: int = 300):
        """Helper to handle caching, API calls, and error trapping."""
        cache_key = hashlib.md5(prompt.encode()).hexdigest()
        
        if cache_key in self.cache:
            print("   ⚡ [Cache Hit! 0 Latency, 0 API Calls Used]")
            return self.cache[cache_key]

        try:
            self.api_call_count += 1
            # --- NEW: Start a stopwatch ---
            start_time = time.time()
            
            response = self.client.chat_completion(
                model="Qwen/Qwen2.5-72B-Instruct",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.0
            )
            
            # --- NEW: Stop the stopwatch and calculate latency ---
            end_time = time.time()
            latency = round(end_time - start_time, 2)
            print(f"   ⏱️ [Live API Call: Took {latency} seconds]")
            
            result_text = response.choices[0].message.content.strip()
            response = self.client.chat_completion(
                model="Qwen/Qwen2.5-72B-Instruct",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.0
            )
            
            result_text = response.choices[0].message.content.strip()
            
            if is_json:
                if result_text.startswith("```json"):
                    result_text = result_text[7:-3].strip()
                elif result_text.startswith("```"):
                    result_text = result_text[3:-3].strip()
                    
            self.cache[cache_key] = result_text
            self._save_cache()
            return result_text
            
        except Exception as e:
            print(f"\n⚠️ HUGGING FACE API ERROR: {e}")
            return None

    # --- MAIN PROCESSING LOGIC ---
    def process_user_input(self, user_text: str, last_question_asked: str):
        
        # --- MOD 1: Process the Yes/No Confirmation ---
        if self.pending_field:
            check_prompt = f"Question: '{last_question_asked}'\nUser Answer: '{user_text}'\nDid the user agree/confirm? Answer exactly 'YES' or 'NO'."
            
            reply_text = self._call_llm(check_prompt, is_json=False, max_tokens=10)
            
            if reply_text and "YES" in reply_text.upper():
                print(f"✅ User confirmed {self.pending_field} as {self.pending_value}")
                self.collected_data[self.pending_field] = self.pending_value
                
                # Reset states on success!
                self.pending_field = None
                self.pending_value = None
                self.rejection_count = 0 
                user_text = "Please ask the next missing field." 
            else:
                self.rejection_count += 1
                print(f"❌ User rejected {self.pending_value} (Rejection #{self.rejection_count})")
                
                rejected_field = self.pending_field.replace('_', ' ') if self.pending_field else "value"
                self.pending_field = None
                self.pending_value = None
                
                # --- NEW: The "Spell It Out" Pivot ---
                if self.rejection_count >= 2:
                    return {
                        "extracted_field_name": None,
                        "extracted_value": None,
                        "next_question": f"I'm having trouble catching the exact spelling of your {rejected_field}. Could you please say it again and spell it out letter by letter?",
                        "is_form_complete": False
                    }
                else:
                    return {
                        "extracted_field_name": None,
                        "extracted_value": None,
                        "next_question": f"My apologies. Let's try again. What is your {rejected_field}?",
                        "is_form_complete": False
                    }
        # --- MOD 1: Process the Yes/No Confirmation --- ***OLD MODIFICATION, NOW REFACTORED INTO A MORE ROBUST "SPELL IT OUT" MECHANISM***
        '''
        if self.pending_field:
            check_prompt = f"Question: '{last_question_asked}'\nUser Answer: '{user_text}'\nDid the user agree/confirm? Answer exactly 'YES' or 'NO'."
            
            reply_text = self._call_llm(check_prompt, is_json=False, max_tokens=10)
            
            if reply_text and "YES" in reply_text.upper():
                print(f"✅ User confirmed {self.pending_field} as {self.pending_value}")
                self.collected_data[self.pending_field] = self.pending_value
                self.pending_field = None
                self.pending_value = None
                user_text = "Please ask the next missing field." 
            else:
                print(f"❌ User rejected {self.pending_value}. Asking again.")
                rejected_field = self.pending_field.replace('_', ' ') if self.pending_field else "value"
                self.pending_field = None
                self.pending_value = None
                return {
                    "extracted_field_name": None,
                    "extracted_value": None,
                    "next_question": f"My apologies. Let's try again. What is your {rejected_field}?",
                    "is_form_complete": False
                }
        '''
        missing_fields = [
            field for field in self.schema['fields'] 
            if field['name'] not in self.collected_data
        ]
        
        prompt = f"""
        You are a strict, logical data-entry agent. 
        
        Target Form Schema (Valid Field Names): {json.dumps(self.schema['fields'])}
        Currently Collected Data: {json.dumps(self.collected_data)}
        Fields STILL Missing: {json.dumps(missing_fields)}
        
        The last question you asked was: "{last_question_asked}"
        The user answered: "{user_text}"
        
        Task:
        1. Extract the user's answer. The 'extracted_field_name' MUST be an exact, case-sensitive match to a 'name' from the Target Form Schema.
        2. TRANSLATION AND CORRECTION: If the user answered in Hindi, Bengali, or any other regional language, translate the 'extracted_value' into English before saving it. If the field is a Name, the ASR may have misheard regional Indian spellings. Use your knowledge of common Bengali (e.g., Subrata, Debjani, Roy) and Hindi (e.g., Rahul, Priya, Sharma) phonetic patterns to guess the most likely correct English spelling. 
        3. SPELLING OVERRIDE: If the user spells a word out letter-by-letter (e.g., "S O H I N I" or "S as in Sam, O as in Owl"), this is the absolute ground truth. You MUST combine the letters into a single, correctly capitalized word (e.g., "Sohini") and OVERRIDE any phonetic correction rules from step 2.
        4. DROPDOWN MENU MATCHING: If the target field has 'options' defined in the schema (like Account Type or Language), your 'extracted_value' MUST be an exact, case-sensitive match to one of those provided options. If the user uses a synonym, map it to the closest valid option.
        5. Look at the 'Fields STILL Missing' list. If the user just answered the first missing field, look at the SECOND one in that list.
        6. Generate a short, polite 'next_question' for that next missing field.
        7. If the user just provided the very last missing piece of information, set 'is_form_complete' to true and 'next_question' to null.
        
        CRITICAL: You MUST return your response ONLY as a valid JSON object matching this structure:
        {{"extracted_field_name": "string or null", "extracted_value": "string or null", "next_question": "string", "is_form_complete": boolean}}
        Do not include markdown formatting or conversational text outside the JSON.
        """
        
        response_text = self._call_llm(prompt, is_json=True, max_tokens=300)
        
        if not response_text:
            return {
                "extracted_field_name": None,
                "extracted_value": None,
                "next_question": "I am experiencing brief network congestion. Could you please repeat your answer?",
                "is_form_complete": False
            }
            
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            print("⚠️ Failed to parse JSON from LLM.")
            return {
                "extracted_field_name": None,
                "extracted_value": None,
                "next_question": "I had trouble understanding that. Could you repeat it?",
                "is_form_complete": False
            }
    
        # --- 3. Neuro-Symbolic Validation Engine ---
        extracted_field = result.get("extracted_field_name")
        extracted_val = result.get("extracted_value")
        
        
        if extracted_field and extracted_val:
            field_lower = extracted_field.lower()
            val_clean = str(extracted_val).strip()
            
            # ---------------------------------------------------------
            # NEW: Dynamic Dropdown Validation
            # ---------------------------------------------------------
            # 1. Find the schema definition for this specific field
            target_field_schema = next((f for f in self.schema['fields'] if f['name'] == extracted_field), None)
            
            # 2. If this field has 'options', enforce strict matching
            if target_field_schema and target_field_schema.get('options'):
                valid_options = target_field_schema['options']
                
                # Check for a case-insensitive match
                matched_option = next((opt for opt in valid_options if opt.lower() == val_clean.lower()), None)
                
                if matched_option:
                    # Force the exact casing required by the HTML form
                    result["extracted_value"] = matched_option 
                else:
                    # Reject it and read the options aloud to the user
                    options_str = ", ".join(valid_options)
                    result["extracted_field_name"] = None
                    result["extracted_value"] = None
                    result["next_question"] = f"For this field, you must choose one of the following options: {options_str}. Which one would you prefer?"
                    result["is_form_complete"] = False
                    return result # Exit validation early and ask the user again
            
            # ---------------------------------------------------------
            # 2. Format-Specific Validation Rules
            # ---------------------------------------------------------
            val_clean = str(extracted_val).replace(" ", "")
            
            if "aadhaar" in field_lower and not re.match(r"^\d{12}$", val_clean):
                result["extracted_field_name"] = result["extracted_value"] = None
                result["next_question"] = "That Aadhaar number doesn't seem to be 12 digits. Could you please say your 12-digit Aadhaar number again?"
                result["is_form_complete"] = False
                
            elif "pan" in field_lower and not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", val_clean.upper()):
                result["extracted_field_name"] = result["extracted_value"] = None
                result["next_question"] = "That PAN format looks incorrect. It should be 5 letters, 4 numbers, and 1 letter. Could you say your PAN number again?"
                result["is_form_complete"] = False
                
            elif "phone" in field_lower and not re.match(r"^\d{10}$", val_clean):
                result["extracted_field_name"] = result["extracted_value"] = None
                result["next_question"] = "A valid phone number must be exactly 10 digits. Could you please repeat your phone number?"
                result["is_form_complete"] = False
                
            elif "pin" in field_lower and not re.match(r"^\d{6}$", val_clean):
                result["extracted_field_name"] = result["extracted_value"] = None
                result["next_question"] = "A valid PIN code must be exactly 6 digits. What is your PIN code?"
                result["is_form_complete"] = False
                
            elif "state" in field_lower:
                val_lower = str(extracted_val).lower().strip()
                if val_lower not in self.valid_states:
                    result["extracted_field_name"] = result["extracted_value"] = None
                    result["next_question"] = f"I couldn't recognize '{extracted_val}' as a valid state. Could you please say your state again?"
                    result["is_form_complete"] = False
                else:
                    result["extracted_value"] = self.valid_states[val_lower]

            elif "district" in field_lower:
                val_lower = str(extracted_val).lower().strip()
                if val_lower not in self.valid_districts:
                    result["extracted_field_name"] = result["extracted_value"] = None
                    result["next_question"] = f"I couldn't find '{extracted_val}' in our database. Could you tell me your district again?"
                    result["is_form_complete"] = False
                else:
                    saved_state = self.collected_data.get("address_state")
                    if saved_state and self.valid_districts[val_lower] != saved_state:
                        result["extracted_field_name"] = result["extracted_value"] = None
                        result["next_question"] = f"'{extracted_val}' doesn't seem to be in {saved_state}. Could you please confirm your district?"
                        result["is_form_complete"] = False
                    else:
                        result["extracted_value"] = extracted_val.title()
                        
            elif result.get("extracted_field_name"): 
                if "name" in field_lower or "city" in field_lower:
                    self.pending_field = result["extracted_field_name"]
                    self.pending_value = result["extracted_value"]
                    result["extracted_field_name"] = None
                    result["extracted_value"] = None
                    result["next_question"] = f"I heard {self.pending_value}. Is that correct?"
                    result["is_form_complete"] = False        
                    
            elif "age" in field_lower:
                try:
                    if int(val_clean) < 18:
                        result["extracted_field_name"] = None
                        result["extracted_value"] = None
                        result["next_question"] = "You must be at least 18 years old to fill out this form. Could you please confirm your age?"
                        result["is_form_complete"] = False
                except ValueError:
                    result["extracted_field_name"] = None
                    result["extracted_value"] = None
                    result["next_question"] = "I didn't catch a valid number for your age. Could you say that again?"
                    result["is_form_complete"] = False

        return result
    
    # --- ANALYTICS & USAGE STATS ---
    def print_usage_stats(self):
        """Print usage statistics for the dissertation study"""
        print("\n" + "="*60)
        print("📊 SESSION ANALYTICS & CACHE DASHBOARD")
        print("="*60)
        
        # Calculate savings
        total_interactions = self.api_call_count + len(self.cache)
        cache_hits = len(self.cache)
        savings_percentage = (cache_hits / total_interactions * 100) if total_interactions > 0 else 0
        
        print(f"Total AI Interactions: {total_interactions}")
        print(f"Live API Calls Made:   {self.api_call_count}")
        print(f"Cached Responses Used: {cache_hits}")
        
        # Visual progress bar for cache efficiency
        bar_length = 30
        filled = int((savings_percentage / 100) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        print(f"\nCache Efficiency: [{bar}] {savings_percentage:.1f}% API Calls Saved")
        print("="*60 + "\n")

# ---------------------------------------------------------
# 3. Terminal Testing Loop
# ---------------------------------------------------------
if __name__ == "__main__":
    agent = DialogueManager()
    
    print(f"\n📝 Form Purpose: {agent.schema.get('form_purpose', 'Unknown Form')}")
    print("-" * 50)
    
    last_question = f"Hello! I am here to help you fill out the {agent.schema.get('form_purpose')}. What is your full name?"
    print(f"🤖 Agent: {last_question}")
    
    while True:
        user_input = input("🗣️  You: ")
        result = agent.process_user_input(user_input, last_question)
        
        if result.get("extracted_field_name") and result.get("extracted_value"):
            field = result["extracted_field_name"]
            value = result["extracted_value"]
            agent.collected_data[field] = value
            print(f"   [System: Saved '{value}' into field '{field}']")
            
        if result.get("is_form_complete"):
            print("\n✅ Form Complete! Here is the final JSON payload ready for the database:")
            print(json.dumps(agent.collected_data, indent=2))
            # --- NEW: Calculate Total Session Time ---
            session_end_time = datetime.now()
            total_duration = session_end_time - agent.session_start_time
            
            # Format the duration nicely (e.g., "2 minutes, 14 seconds")
            minutes, seconds = divmod(total_duration.total_seconds(), 60)
            print(f"\n⏱️ Total Time on Task: {int(minutes)}m {int(seconds)}s")

            

            # --- NEW: Print the visual dashboard! ---
            agent.print_usage_stats()
            break
            '''
            # Print the final analytics for the dissertation!
            print("\n📊 SESSION ANALYTICS:")
            print(f"Total Live API Calls Made: {agent.api_call_count}")
            print(f"Total Cached Responses Saved: {len(agent.cache)}")
            break
            '''
        last_question = result["next_question"]
        print(f"\n🤖 Agent: {last_question}")
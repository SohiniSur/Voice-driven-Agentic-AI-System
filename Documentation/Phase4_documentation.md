Phase 4: State Management & Conversational Resilience (The "Brain & Memory")
Objective: To manage the conversational flow, persist extracted data across conversational turns, and provide robust, multi-layered fallback mechanisms when the Natural Language Understanding (NLU) or Automatic Speech Recognition (ASR) components encounter ambiguity.

Core Components:

State Tracker (collected_data): A dynamic JSON object that serves as the system's short-term memory, holding securely validated data while monitoring a "Fields STILL Missing" array to determine the next conversational prompt.

Semantic Cache (response_cache.json): An MD5-hashed local dictionary that stores previous LLM inferences. If a user repeats an identical audio transcript or confirms a standard prompt (e.g., "Yes"), the system bypasses the LLM API, resulting in zero-latency responses and reduced computational overhead.

Three-Stage Phonetic Correction Protocol: A specialized sub-system designed to handle the high error rate of ASR models when transcribing regional proper nouns.

Probabilistic Correction: The LLM applies regional phonetic context (e.g., common Bengali or Hindi spellings) to correct minor ASR misinterpretations during initial extraction.

Human-in-the-Loop Validation: The probabilistically generated spelling is fed back to the user via a synthesized voice prompt for a strict Yes/No verbal confirmation.

Deterministic Override ("Spell It Out"): If the user rejects the system's guess twice, a rejection counter triggers a dynamic conversational pivot, instructing the user to spell the word letter-by-letter. The LLM is instructed to treat this character array as the absolute ground truth.
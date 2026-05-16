# Voice-Driven Agentic AI for Form Filling — Inclusive Elderly Services

> An end-to-end agentic AI system that converts regional voice input into validated government form submissions — no GUI, no digital literacy required.

**M.Sc. Dissertation | IAI, TCG CREST, Kolkata | Dec 2025 – Apr 2026**
**Supervisor:** Dr. Md. Sahidullah, Assistant Professor, IAI, TCG CREST
**Internal Mentor:** Dr. Durba Bhattacharya, Assistant Professor, St. Xavier's College (Autonomous), Kolkata

---

## Problem

Improving internet connectivity has not closed the digital access gap for elderly and rural populations in India. The barrier is not bandwidth — it is interface design. Current systems demand high digital fluency and force users to structure their own data into rigid GUI forms. This dependency on third-party intermediaries creates privacy risks and is a fundamental engineering flaw, not a user deficiency.

**Research gaps this project addresses:**
- No end-to-end voice agent exists for Indian demographic form-filling contexts
- No integration of LLM error-recovery with ASR in low-resource, low-connectivity environments
- No empirical user-acceptance study on high-friction voice UIs for elderly populations in West Bengal

---

## System Overview

The system operates as a **3-phase pipeline: Schema → Dialogue → Execute**

```
User speaks (Bengali / Indian English / code-mixed)
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1 — SCHEMA                                           │
│  Playwright (async) scrapes target form HTML                │
│  Gemini 2.5 Flash parses DOM → structured JSON schema       │
│  MD5 cache hash: avoids redundant parsing (83.69% hit rate) │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2 — DIALOGUE                                         │
│  Faster-Whisper ASR (~244M params) transcribes audio        │
│  Qwen2.5-72B (128K context, HuggingFace API)                │
│    → entity extraction, translation, validation             │
│    → ReAct agentic loop with spell-out fallback             │
│  Google TTS converts responses to spoken audio              │
│  Pydantic enforces field schema + regex validation          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 3 — EXECUTE                                          │
│  Playwright (sync) fills validated fields into live form    │
│  PDF generated as submission record                         │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
FastAPI orchestrates all phases — async routing,
conversational state management, inter-module coordination
Deployed via Ngrok + Windows SSH
```

---
# 🎙️ Agentic AI Form Automation Pipeline

An autonomous, voice-driven Agentic AI pipeline designed to bridge the digital divide by automating complex, high-stakes regulatory form-filling for digitally marginalized and low-literacy demographics.

This project shifts from traditional reactive conversational chatbots to a **proactive, tool-augmented architecture**. It utilizes Large Language Models (LLMs) as central orchestration engines to read DOM topologies, conduct neuro-symbolic dialogue management, and execute robotic browser automation.

## 🚀 Key Features

* **Dynamic Schema Extraction:** Utilizes multimodal vision-language models (Gemini) for zero-shot reading of DOM topologies, eliminating the need for hard-coded dialogue trees.
* **Neuro-Symbolic Dialogue Management:** Grounds the probabilistic reasoning of LLMs (Qwen2.5-72B) within deterministic, Python-based regex validation frameworks to ensure zero-hallucination data entry.
* **Code-Mixed Phonetic Error Correction:** Specifically engineered to handle ASR friction, out-of-vocabulary (OOV) proper nouns (e.g., regional Indian names and districts), and code-mixed Hindi/English speech.
* **Robotic Browser Execution:** Headless execution via Playwright to autonomously navigate and inject validated user data into complex administrative web forms.
* **Cryptographic MD5 Caching Layer:** Features a localized caching architecture that intercepts highly idempotent conversational states, yielding a **94.9% cache efficiency rate** and drastically reducing cloud API latency and rate-limiting (HTTP 402 errors).

## 🛠️ Technology Stack

* **Core Logic & API:** Python 3.10+, FastAPI, Uvicorn
* **Speech-to-Text (ASR):** Faster-Whisper
* **Cognitive Engine:** Hugging Face Serverless Inference API (`Qwen/Qwen2.5-72B-Instruct`)
* **Vision & Schema Extraction:** Google Gemini 2.5 Flash
* **Web Automation:** Playwright

## 📊 System Performance & Telemetry

Extensive field testing (N=10 qualitative cohort, N=4 micro-latency cohort) yielded the following architectural insights:
* **Latency Optimization:** The MD5 caching layer successfully reduced Time-to-First-Audio (TTFA) for standard administrative validations to near-zero (bounded only by local disk I/O).
* **ASR Friction Profiling:** Identified proper nouns and alphanumeric sequences (e.g., PAN cards) as the primary latency bottlenecks in standard English-trained ASR pipelines, successfully mitigating them through custom "Spell-It-Out" fallback loops.

## 💻 Installation and Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/SohiniSur/Voice-driven-Ageentic-AI-System-.git](https://github.com/SohiniSur/Voice-driven-Ageentic-AI-System-.git)
   cd SohiniSur/Voice-driven-Ageentic-AI-System-
   ```



2. **install dependancies
   ```bash
    pip install -r requirements.txt
   ```

3. **Copy and fill in your API keys:**
   Create a .env file in the root directory and add your API keys:
   HF_TOKEN=your_huggingface_finegrained_token
   GEMINI_API_KEY=your_google_gemini_token

4. **Start the FastAPI server:**
  ```bash
  uvicorn main:app --reload
  ```

## Ethics & Privacy

- No participant data, audio recordings, or PII from the field study is included in this repository
- Field study conducted with informed consent; data retained only in aggregated form
- The system is designed to process data locally where possible; API calls are minimized via caching

---

## Citation

```
Sur, S. (2026). Voice-Driven Agentic AI for Form Filling for Inclusive Elderly Services.
M.Sc. Dissertation, St. Xavier's College (Autonomous), Kolkata.
Supervised by Dr. Md. Sahidullah, IAI, TCG CREST.
```

---

*Internship cum Dissertation, Institute for Advancing Intelligence (IAI), TCG CREST, Kolkata. Dec 2025 – Apr 2026.*

Phase 2 Documentation: Form Schema Extraction
1. Architectural Overview
Phase 2 establishes the automated "reading" layer of the agentic system. Instead of manually hardcoding the questions the voice agent needs to ask, this module uses a headless browser to scrape raw HTML DOM elements from target government or service web forms. It then utilizes a Large Language Model (Gemini 1.5 Flash) with strict Structured Outputs to translate that messy HTML array into a clean, logical JSON schema. This schema acts as the "brain map" that dictates the agent's conversational flow.

2. Environment & Dependencies
Backend Stack (Python)
Virtual Environment: Standard Python venv

Web Scraping / Automation: playwright, playwright-chromium (headless browser execution)

AI Engine: google-genai (Gemini 1.5 Flash for cost-effective, high-context token processing)

Data Validation: pydantic (for enforcing strict JSON schema outputs)

Environment Management: python-dotenv (for loading .env secrets)

Version Control: git (installed via winget)

3. Project File Structure
schema_extractor.py: The core script containing the Playwright async extraction logic and the Gemini structured generation call.

.env: A hidden, untracked file storing sensitive credentials (e.g., GEMINI_API_KEY).

.gitignore: The Git configuration file ensuring virtual environments (venv/), Node modules (node_modules/), and secrets (.env) are securely excluded from version control.

4. Key Findings & Research Insights
Cost-Effective Scaling: Transitioning from GPT-4o to Gemini 1.5 Flash for Phase 2 proved highly effective. Parsing raw HTML DOM arrays consumes massive token context windows. Gemini easily handles these large payloads with near-instant execution at a fraction of the cost, making it ideal for scalable agentic workflows.

Deterministic Output via Pydantic: Standard prompting often results in conversational fluff or malformed JSON from LLMs. By passing a Pydantic BaseModel (FormSchema) directly into the Gemini response_schema configuration, the AI is mathematically forced to return a strictly typed, perfectly formatted JSON object.

Version Control Security: Hardcoding API keys into local scripts is a major security risk. Implementing a .env file combined with git init and a proper .gitignore ensures that credentials remain strictly local while the codebase is tracked.

5. Quick-Start Runbook
Whenever you need to extract a new form schema, follow these steps:

Execution Flow
Open a terminal in your root project folder.

Activate the virtual environment:

Bash
.\venv\Scripts\activate
Ensure your API key is active: Verify that your .env file exists in the root directory and contains GEMINI_API_KEY=your_key_here.

Run the extractor:

Bash
python schema_extractor.py
Collect the Output: The terminal will print a structured JSON object containing the form_purpose and an array of fields (with names, types, requirement status, and conversational descriptions).

6. Actionable Improvements & Hardening
As you move towards integrating this into your final pipeline, consider these upgrades:

1. Dynamic URL Ingestion
The Problem: The target URL is currently hardcoded into the main() function of the script.

Suggested Implementation: Modify the script to accept the URL as a command-line argument using Python's argparse or sys.argv.

Bash
python schema_extractor.py --url "https://example.com/form"
2. Handling Single Page Applications (SPAs)
The Problem: Playwright is currently grabbing the HTML immediately after navigating to the page. If a government site uses heavy JavaScript to load the form dynamically, Playwright might scrape an empty page.

Suggested Implementation: Add an explicit wait command in the Playwright block to ensure network requests finish before scraping:

Python
await page.goto(url, wait_until="networkidle")
3. Modularity for Phase 3
The Problem: The script currently prints the JSON to the terminal.

Suggested Implementation: Modify the generate_agent_schema function to actually save the output as a local schema.json file in your directory. This allows the Phase 3 Dialogue Manager to seamlessly load the file and start talking to the user.
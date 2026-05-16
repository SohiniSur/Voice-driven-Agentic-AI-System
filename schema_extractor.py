import asyncio
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from google import genai
from pydantic import BaseModel

load_dotenv()

# ---------------------------------------------------------
# 1. Define the exact JSON structure we demand from Gemini
# ---------------------------------------------------------
class FormField(BaseModel):
    name: str
    type: str  # e.g., "text", "number", "date", "dropdown"
    required: bool
    options: list[str] | None = None
    description: str  # Instructions for the voice agent (e.g., "Ask the user for their first name")

class FormSchema(BaseModel):
    form_purpose: str
    fields: list[FormField]

# ---------------------------------------------------------
# 2. Playwright: Scrape the raw form elements
# ---------------------------------------------------------
async def extract_raw_form(url: str):
    print(f"🕵️ Scanning form at: {url}...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        
        # Inject JavaScript to scrape all inputs, selects, and textareas
        raw_elements = await page.evaluate("""() => {
            const inputs = Array.from(document.querySelectorAll('input, select, textarea'));
            return inputs.map(el => {
                let labelText = '';
                if (el.id) {
                    const label = document.querySelector(`label[for="${el.id}"]`);
                    if (label) labelText = label.innerText;
                }
                return {
                    tag: el.tagName,
                    type: el.type,
                    name: el.name,
                    id: el.id,
                    placeholder: el.placeholder,
                    label: labelText,
                    options: el.tagName === 'SELECT' ? Array.from(el.options).map(o => o.text) : []
                };
            });
        }""")
        
        await browser.close()
        return raw_elements

# ---------------------------------------------------------
# 3. Gemini: Convert raw HTML into Agentic JSON
# ---------------------------------------------------------
def generate_agent_schema(raw_data: list):
    print("🧠 Sending raw DOM data to Gemini 1.5 Flash...")
    
    # Initialize the Gemini SDK (Requires GEMINI_API_KEY in your environment variables)
    client = genai.Client() 
    
    prompt = f"""
    You are an AI architect building a voice-driven form-filling agent for rural users.
    Analyze this raw HTML form data extracted via Playwright:
    {raw_data}
    
    Map out the fields, determine if they are required based on standard logic, and provide a simple 'description' that our ReAct dialogue agent can use to formulate a spoken question.
    """
    
    # Force Gemini to output strictly according to our Pydantic model
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config={
            'response_mime_type': 'application/json',
            'response_schema': FormSchema,
        },
    )
    
    return response.text
# ---------------------------------------------------------
# 4. Execution Logic
# ---------------------------------------------------------
async def main():
    # Example: You can swap this with a real dummy government form URL
    # target_url = "https://www.w3schools.com/html/html_forms.asp" 
    target_url ="file:///C:/Users/sohin/agentic_ai_project/bank_form.html"
    
    raw_html_data = await extract_raw_form(target_url)
    clean_json_schema = generate_agent_schema(raw_html_data)
    
    print("\n✅ Final Agent Schema Generated:\n")
    print(clean_json_schema)
    
    # --- NEW CODE: Save the output directly to a JSON file ---
    with open("schema.json", "w", encoding="utf-8") as file:
        file.write(clean_json_schema)
        
    print("💾 Successfully saved to schema.json! The brain map is ready.")

if __name__ == "__main__":
    # Ensure your API key is set before running
    if not os.environ.get("GEMINI_API_KEY"):
        print("⚠️ ERROR: You must set your GEMINI_API_KEY environment variable first!")
    else:
        asyncio.run(main())
'''        
# ---------------------------------------------------------
# 4. Execution Logic
# ---------------------------------------------------------
async def main():
    # Example: You can swap this with a real dummy government form URL
    target_url = "https://www.w3schools.com/html/html_forms.asp" 
    
    raw_html_data = await extract_raw_form(target_url)
    clean_json_schema = generate_agent_schema(raw_html_data)
    
    print("\n✅ Final Agent Schema Generated:\n")
    print(clean_json_schema)

if __name__ == "__main__":
    # Ensure your API key is set before running
    if not os.environ.get("GEMINI_API_KEY"):
        print("⚠️ ERROR: You must set your GEMINI_API_KEY environment variable first!")
    else:
        asyncio.run(main())
'''
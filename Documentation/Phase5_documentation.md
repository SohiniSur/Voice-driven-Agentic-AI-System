Phase 5: Automated Form Execution & PDF Generation (The "Robot Hands")
Objective: To bridge the gap between backend AI data extraction and legacy banking infrastructure by translating the validated JSON payload into a completed, legally printable PDF document without requiring API integrations from the bank.

Core Components:

Asynchronous Execution Thread: A Python threading implementation that decouples the browser automation from the main FastAPI server loop, ensuring the user receives their final audio confirmation ("Thank you, I am filling out the form...") without latency.

Headless Browser Engine (Playwright): A browser automation library utilized to instantiate a hidden Chromium browser, interact with the Document Object Model (DOM), and execute print commands.

Target Interface (bank_form.html): A locally hosted, standardized banking application form containing standard HTML input elements.

Technical Workflow:

Once Phase 4 sets is_form_complete to True, the FastAPI endpoint in main.py triggers the final voice response and simultaneously spawns a background form_filler thread.

Playwright launches a headless Chromium instance and navigates to the target HTML file URL.

The script utilizes strict CSS selectors (e.g., #applicant_name, #aadhaar_number) to programmatically inject the corresponding values from the validated JSON payload into the DOM.

Upon successful DOM population, Playwright executes a page.pdf() command, rendering a static, non-editable document named Filled_Application_Receipt.pdf.

The PDF is saved to the local directory, ready for physical banking archives or digital compliance submission.
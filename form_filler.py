from playwright.sync_api import sync_playwright
import time
import os

def auto_fill_form(form_url, form_data):
    print("\n🚀 Initiating Phase 5: Robotic Form Automation...")
    
    with sync_playwright() as p:
        # headless=False means we actually get to watch the browser open and type!
        # slow_mo=200 slows down the typing just enough so we can watch it happen
        # PDF generation requires headless mode to be True
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print(f"🌐 Navigating to {form_url}...")
        try:
            page.goto(form_url)
            page.wait_for_load_state("networkidle")
            
            # Loop through our collected JSON data
            for field_name, value in form_data.items():
                print(f"⌨️  Typing '{value}' into '{field_name}'...")
                try:
                    # We target the exact HTML 'name' or 'id' attribute we scraped in Phase 2
                    selector = f"//*[@name='{field_name}' or @id='{field_name}']"
                    
                    # Wait for the element to be visible, then fill it
                    #page.locator(selector).first.fill(str(value))
                    locator = page.locator(selector).first
                    
                    if locator.count() > 0:
                        # Evaluate the DOM to see what kind of HTML tag this is
                        tag_name = locator.evaluate("el => el.tagName.toLowerCase()")
                        
                        if tag_name == "select":
                            print(f"🔽 Selecting '{value}' from dropdown '{field_name}'...")
                            locator.select_option(label=str(value))
                        else:
                            print(f"⌨️  Typing '{value}' into '{field_name}'...")
                            locator.fill(str(value))
                            
                    else:
                        print(f"⚠️  Skipped '{field_name}': Could not find it on the page.")
                        
                except Exception as e:
                    print(f"⚠️  Error interacting with '{field_name}': {e}")
                '''
                except Exception as e:
                    print(f"⚠️  Skipped '{field_name}': Could not find it on the page.")
                '''
            # --- MOD 3: Generate the PDF! ---
            pdf_path = os.path.join(os.getcwd(), "Filled_Application_Receipt.pdf")
            page.pdf(path=pdf_path, format="A4", print_background=True)
            print(f"\n✅ Form complete! PDF saved successfully at: {pdf_path}")
            
            print("\n✅ Form filling complete! Closing browser in 5 seconds...")
            time.sleep(5) # Give you time to look at the filled form
            
        except Exception as e:
            print(f"❌ Failed to load or fill the form: {e}")
        finally:
            browser.close()
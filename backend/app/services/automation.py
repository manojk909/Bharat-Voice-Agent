import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def run_portal_autofill(profile: dict, portal_url: str):
    """
    Spins up a local Chrome browser using Selenium, navigates to the government portal,
    and runs a continuous background loop to fill form fields dynamically as the user
    navigates, logs in, or moves through steps.
    """
    options = webdriver.ChromeOptions()
    # Keep the browser open after script completes so user can review/submit
    options.add_experimental_option("detach", True)
    
    # Exclude automation indicators to bypass basic bot detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
# Direct registration/application sub-pages for seeded portals
PORTAL_REGISTRATION_REDIRECTS = {
    "pmkisan.gov.in": "https://pmkisan.gov.in/RegistrationFormupdated.aspx",
    "scholarships.gov.in": "https://scholarships.gov.in/fresh/newRegistrationWidget",
    "scholarship.up.gov.in": "https://scholarship.up.gov.in/RegistrationPage.aspx",
    "ssp.postmatric.karnataka.gov.in": "https://ssp.postmatric.karnataka.gov.in/CA/",
    "maandhan.in": "https://maandhan.in/enrolment",
}

# Multilingual matching patterns for profile field names
matching_criteria = {
    "name": [
        "name", "fullname", "first", "last", "applicant", "candidate", "username",
        "नाम", "नाम", "ಹೆಸರು", "పేరు", "பெயர்", "नाव", "નામ", "নাম"
    ],
    "age": [
        "age", "dob", "birth", "date_of_birth",
        "उम्र", "आयु", "ವಯಸ್ಸು", "వయస్సు", "வயது", "वय", "ઉંમર", "বয়স"
    ],
    "gender": [
        "gender", "sex",
        "लिंग", "ಲಿಂಗ", "gender", "பாலினம்", "लिंग", "લિંગ", "লিঙ্গ"
    ],
    "income": [
        "income", "annual", "salary", "family_income",
        "आय", "ಆದಾಯ", "ఆదాయం", "வருமானம்", "उत्पन्न", "આવક", "আয়"
    ],
    "caste": [
        "caste", "category", "social",
        "जाति", "ವರ್ಗ", "कुला", "சாதி", "जात", "જ્ઞાતિ", "জাতি"
    ],
    "state": [
        "state", "domicile", "region",
        "राज्य", "ರಾಜ್ಯ", "రాష్ట్రం", "மாநிலம்", "राज्य", "રાજ્ય", "রাজ্য"
    ],
    "district": [
        "district", "city", "taluk",
        "जिला", "ಜಿಲ್ಲೆ", "ಜిల్లా", "மாவட்டம்", "जिल्हा", "જિલ્લો", "জেলা"
    ],
    "occupation": [
        "occupation", "profession", "work", "job",
        "व्यवसाय", "ವೃತ್ತಿ", "ఉద్యోగం", "தொழில்", "व्यवसाय", "व्यवसाय", "পেশা"
    ],
    "disability": [
        "disability", "handicap", "pwd",
        "विकलांग", "ವಿಕಲಚೇತನ", "వికలాంగుడు", "மாற்றுத்திறனாளி", "दिव्यांग", "દિવ્યાંગ", "প্রতিবন্ধী"
    ],
    "aadhaar": [
        "aadhaar", "uid", "आधार", "aadhaar_number", "aadhaar_card"
    ],
    "mobile": [
        "mobile", "phone", "contact", "mobile_number", "phone_number", "मूर्ख"
    ]
}

LOCAL_TRANSLATION_MAP = {
    "महाराष्ट्र": "Maharashtra",
    "कर्नाटक": "Karnataka",
    "उत्तर प्रदेश": "Uttar Pradesh",
    "आंध्र प्रदेश": "Andhra Pradesh",
    "तेलंगाना": "Telangana",
    "फार्मर": "Farmer",
    "किसान": "Farmer",
    "कृषि": "Agriculture",
    "विद्यार्थी": "Student",
    "छात्र": "Student",
    "महिला": "Female",
    "पुरुष": "Male",
    "हाँ": "Yes",
    "ना": "No",
    "नहीं": "No"
}

def translate_value(val):
    if not val:
        return val
    val_str = str(val).strip()
    return LOCAL_TRANSLATION_MAP.get(val_str, val_str)

def run_portal_autofill(profile: dict, portal_url: str):
    """
    Spins up a local Chrome browser using Selenium, navigates to the government portal,
    and runs a continuous background loop to fill form fields dynamically as the user
    navigates, logs in, or moves through steps.
    """
    options = webdriver.ChromeOptions()
    # Keep the browser open after script completes so user can review/submit
    options.add_experimental_option("detach", True)
    
    # Exclude automation indicators to bypass basic bot detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    # Matching map for profile keys (translated values)
    fill_map = {
        "name": translate_value(profile.get("name")),
        "age": translate_value(profile.get("age")),
        "gender": translate_value(profile.get("gender")),
        "income": translate_value(profile.get("annual_income")),
        "caste": translate_value(profile.get("caste_category")),
        "state": translate_value(profile.get("state")),
        "district": translate_value(profile.get("district")),
        "occupation": translate_value(profile.get("occupation")),
        "disability": translate_value(profile.get("disability_status")),
        "aadhaar": translate_value(profile.get("aadhaar_number")),
        "mobile": translate_value(profile.get("mobile_number"))
    }
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.maximize_window()
        
        # Check if the portal URL has a direct registration redirect configured
        target_url = portal_url
        for domain, redirect_url in PORTAL_REGISTRATION_REDIRECTS.items():
            if domain in portal_url.lower():
                target_url = redirect_url
                print(f"Redirecting directly to registration page: {target_url}")
                break
                
        driver.get(target_url)
        time.sleep(2)
        if "cannot be found" in driver.title.lower() or "404" in driver.title.lower() or "error" in driver.title.lower():
            print(f"Target URL {target_url} returned error page. Falling back to base portal url: {portal_url}")
            driver.get(portal_url)
            time.sleep(2)
        
        print(f"Selenium browser launched. Monitoring and filling fields on {driver.current_url} for the next 10 minutes...")
        
        # Loop for 10 minutes (600 seconds), scanning every 2 seconds
        start_time = time.time()
        while time.time() - start_time < 600:
            try:
                # Check if window/driver is still open (this will throw if closed)
                _ = driver.current_url
            except Exception:
                print("Browser closed by user. Exiting automation loop.")
                break
                
            try:
                # 1. Dismiss common modals/dialogs/alerts that block input
                try:
                    # Handle browser alerts if any
                    alert = driver.switch_to.alert
                    alert.accept()
                    print("Dismissed browser alert.")
                except:
                    pass

                # Dismiss overlay dialog buttons (e.g. close buttons or "OK")
                close_selectors = [
                    "button.close", "button.btn-close", ".modal-header .close", 
                    "a.close", "[aria-label='Close']", ".popup-close"
                ]
                for selector in close_selectors:
                    for close_btn in driver.find_elements(By.CSS_SELECTOR, selector):
                        if close_btn.is_displayed():
                            close_btn.click()
                            print(f"Dismissed modal with selector: {selector}")
                
                # 2. Find all potential input, select, and textarea fields
                inputs = (
                    driver.find_elements(By.TAG_NAME, "input") + 
                    driver.find_elements(By.TAG_NAME, "select") + 
                    driver.find_elements(By.TAG_NAME, "textarea")
                )
                
                for elem in inputs:
                    try:
                        # Skip hidden or disabled elements
                        if not elem.is_displayed() or not elem.is_enabled():
                            continue
                            
                        # Skip if already filled by assistant
                        already_filled = elem.get_attribute("data-filled-by-assistant")
                        if already_filled == "true":
                            continue
                            
                        # Extract attributes to match
                        name_attr = (elem.get_attribute("name") or "").lower()
                        id_attr = (elem.get_attribute("id") or "").lower()
                        placeholder = (elem.get_attribute("placeholder") or "").lower()
                        class_attr = (elem.get_attribute("class") or "").lower()
                        aria_label = (elem.get_attribute("aria-label") or "").lower()
                        
                        combined_text = f"{name_attr} {id_attr} {placeholder} {class_attr} {aria_label}"
                        
                        # Match against our criteria
                        matched_key = None
                        for key, patterns in matching_criteria.items():
                            if any(p in combined_text for p in patterns):
                                matched_key = key
                                break
                                
                        if matched_key:
                            val = fill_map.get(matched_key)
                            if val and str(val).lower() != "not specified":
                                # Handle inputs/textareas
                                if elem.tag_name in ["input", "textarea"]:
                                    # Skip checkbox/radio/submit/button types
                                    input_type = (elem.get_attribute("type") or "text").lower()
                                    if input_type in ["checkbox", "radio", "submit", "button", "hidden", "file"]:
                                        continue
                                        
                                    elem.clear()
                                    elem.send_keys(str(val))
                                    driver.execute_script("arguments[0].setAttribute('data-filled-by-assistant', 'true');", elem)
                                    driver.execute_script("arguments[0].style.backgroundColor = '#dcfce7';", elem)
                                    print(f"Filled text field '{name_attr or id_attr}' with: {val}")
                                    
                                # Handle dropdowns
                                elif elem.tag_name == "select":
                                    options_list = elem.find_elements(By.TAG_NAME, "option")
                                    clicked = False
                                    for opt in options_list:
                                        if str(val).lower() in opt.text.lower() or str(val).lower() in (opt.get_attribute("value") or "").lower():
                                            opt.click()
                                            clicked = True
                                            break
                                    if clicked:
                                        driver.execute_script("arguments[0].setAttribute('data-filled-by-assistant', 'true');", elem)
                                        driver.execute_script("arguments[0].style.backgroundColor = '#dcfce7';", elem)
                                        print(f"Selected option in '{name_attr or id_attr}' matching: {val}")
                                        
                    except Exception as elem_err:
                        pass
            except Exception as scan_err:
                print(f"Error scanning page elements: {scan_err}")
                
            time.sleep(2)
            
        print("Dynamic portal filling session finished.")
    except Exception as e:
        print(f"Error launching Selenium browser: {e}")



import sys
import os
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extraction import safe_click

def upload_file(element, file_type):
    """Custom upload function from the main codebase"""
    resume_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resume.pdf")
    cv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cv.pdf")
    
    if file_type.lower() == 'resume':
        element.send_keys(resume_path)
    elif file_type.lower() == 'cv':
        element.send_keys(cv_path)

def setup_driver():
    """Setup Chrome driver with options"""
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def fill_rbc_application(driver):
    """Fill the RBC job application with hardcoded data"""
    
    # Load test data
    with open('info.json', 'r') as f:
        data = json.load(f)
    
    wait = WebDriverWait(driver, 10)
    
    try:
        # Personal Information Section
        print("Filling personal information...")
        
        # First Name
        first_name = wait.until(EC.presence_of_element_located((By.ID, "personalInformationForm.firstName")))
        first_name.clear()
        first_name.send_keys(data["personal_information"]["legal_name"]["first_name"])
        time.sleep(0.1)
        
        # Middle Name (leave empty as per data)
        middle_name = driver.find_element(By.ID, "personalInformationForm.middleName")
        middle_name.clear()
        middle_name.send_keys(data["personal_information"]["legal_name"]["middle_name"])
        time.sleep(0.1)
        
        # Last Name
        last_name = driver.find_element(By.ID, "personalInformationForm.lastName")
        last_name.clear()
        last_name.send_keys(data["personal_information"]["legal_name"]["last_name"])
        time.sleep(0.1)
        
        # Preferred First Name
        pref_first = driver.find_element(By.ID, "personalInformationForm.preferredFirstName")
        pref_first.clear()
        pref_first.send_keys(data["personal_information"]["preferred_name"]["first_name"])
        time.sleep(0.1)
        
        # Preferred Last Name
        pref_last = driver.find_element(By.ID, "personalInformationForm.preferredLastName")
        pref_last.clear()
        pref_last.send_keys(data["personal_information"]["preferred_name"]["last_name"])
        time.sleep(0.1)
        
        # Date of Birth (format: YYYY-MM-DD -> MM/DD/YYYY)
        dob = data["personal_information"]["date_of_birth"]
        dob_formatted = f"{dob[5:7]}/{dob[8:10]}/{dob[:4]}"
        date_of_birth = driver.find_element(By.ID, "personalInformationForm.dateOfBirth")
        date_of_birth.clear()
        date_of_birth.send_keys(dob_formatted)
        time.sleep(0.1)
        
        # Contact Information Section
        print("Filling contact information...")
        
        # Street Address
        street = driver.find_element(By.ID, "personalInformationForm.address.street")
        street.clear()
        street.send_keys(data["contact_information"]["address"]["street"])
        time.sleep(0.1)
        
        # City
        city = driver.find_element(By.ID, "personalInformationForm.address.city")
        city.clear()
        city.send_keys(data["contact_information"]["address"]["city"])
        time.sleep(0.1)
        
        # Province/State
        province_select = Select(driver.find_element(By.ID, "personalInformationForm.address.state"))
        province_select.select_by_visible_text(data["contact_information"]["address"]["province"])
        time.sleep(0.1)
        
        # Country
        country_select = Select(driver.find_element(By.ID, "personalInformationForm.address.country"))
        country_select.select_by_visible_text(data["contact_information"]["address"]["country"])
        time.sleep(0.1)
        
        # Postal Code
        postal = driver.find_element(By.ID, "personalInformationForm.address.postalCode")
        postal.clear()
        postal.send_keys(data["contact_information"]["address"]["postal_code"])
        time.sleep(0.1)
        
        # Email
        email = driver.find_element(By.ID, "personalInformationForm.email")
        email.clear()
        email.send_keys(data["contact_information"]["email"])
        time.sleep(0.1)
        
        # Phone Device Type
        phone_type_select = Select(driver.find_element(By.ID, "personalInformationForm.phone.deviceType"))
        phone_type_select.select_by_visible_text(data["contact_information"]["phone"]["device_type"])
        time.sleep(0.1)
        
        # Country Code
        country_code_select = Select(driver.find_element(By.ID, "personalInformationForm.phone.countryCode"))
        country_code_select.select_by_visible_text(data["contact_information"]["phone"]["country_code"])
        time.sleep(0.1)
        
        # Phone Number
        phone = driver.find_element(By.ID, "personalInformationForm.phone.phoneNumber")
        phone.clear()
        phone.send_keys(data["contact_information"]["phone"]["phone_number"])
        time.sleep(0.1)
        
        # Residence Status Section
        print("Filling residence status...")
        
        # Citizenship
        citizenship_select = Select(driver.find_element(By.ID, "personalInformationForm.citizenships"))
        citizenship_select.select_by_visible_text(data["residence_status"]["citizenships"])
        time.sleep(0.1)
        
        # Diversity Section
        print("Filling diversity information...")
        
        # Sex
        sex_select = Select(driver.find_element(By.ID, "personalInformationForm.sex"))
        sex_select.select_by_visible_text(data["diversity"]["sex"])
        time.sleep(0.1)
        
        # Gender Identity
        identity_select = Select(driver.find_element(By.ID, "personalInformationForm.genderIdentity"))
        identity_select.select_by_visible_text(data["diversity"]["identity"])
        time.sleep(0.1)
        
        # Race/Ethnicity
        race_select = Select(driver.find_element(By.ID, "personalInformationForm.race"))
        race_select.select_by_visible_text(data["diversity"]["race"])
        time.sleep(0.1)
        
        # How did you hear about us?
        hear_select = Select(driver.find_element(By.ID, "personalInformationForm.howDidYouHearAboutUs"))
        hear_select.select_by_visible_text(data["application_preferences"]["how_did_you_hear_about_us"])
        time.sleep(0.1)
        
        print("Personal information form filled successfully!")
        
    except Exception as e:
        print(f"Error filling form: {e}")
        raise

def main():
    """Main function to run the RBC application test"""
    url = "https://jobs.rbc.com/ca/en/apply?jobSeqNo=RBCAA0088R0000152791EXTERNALENCA&step=1&stepname=personalInformation"
    
    print("Starting RBC application autofill...")
    
    # Setup driver
    driver = setup_driver()
    
    try:
        # Navigate to application page
        print(f"Navigating to: {url}")
        driver.get(url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Fill the application
        fill_rbc_application(driver)
        
        print("Application filled successfully!")
        print("Please review the form before submitting.")
        
        # Keep browser open for review
        input("Press Enter to close the browser...")
        
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to close the browser...")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
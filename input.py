import json
from moorcheh_sdk import MoorchehClient
from dotenv import load_dotenv
import os



def ask(prompt):
    return input(f"{prompt}: ").strip()

def main():
    print("Input a string into all fields")
    print("--- Personal Information ---")
    first_name = ask("First Name")
    last_name = ask("Last Name")
    middle_name = ask("Middle Name (optional)")
    prefix = ask("Prefix (Mr/Ms/Mrs/Dr)")
    
    pref_first = ask("Preferred First Name (optional)")
    pref_last = ask("Preferred Last Name (optional)")
    dob = ask("Date of Birth (YYYY-MM-DD)")

    print("\n--- Contact Information ---")
    street = ask("Street Address")
    city = ask("City")
    province = ask("Province/State")
    country = ask("Country")
    postal_code = ask("Postal Code")
    email = ask("Email")
    phone_number = ask("Phone Number (e.g., 250-661-7096)")
    device_type = ask("Device Type (Mobile/Home/Work)") or "Mobile"
    country_code = ask("Country Code (e.g. 'Canada (+1)')") or "Canada (+1)"

    print("\n--- Residence Status ---")
    citizenship = ask("Citizenship (e.g. Canada)")
    visa_status = ask("Visa Status (if applicable)")
    sponsorship = ask("Do you need sponsorship?")

    print("\n--- Diversity (Voluntary) ---")
    sex = ask("Sex (Male/Female/Prefer not to say)")
    identity = ask("Gender Identity (Man/Woman/Non-binary/etc)")
    lgbtq = ask("Identify as LGBTQ+?")
    disability = ask("Any disabilities?")
    race = ask("Race/Ethnicity")
    
    print("\n--- Work Experience ---")
    num_exp = int(ask("Number of work experiences"))
    experiences = []
    for i in range(num_exp):
        print(f"  > Start Experience #{i+1}")
        job_title = ask("    Job Title")
        company = ask("    Company Name")
        location = ask("    Location (City, Province)")
        start = ask("    Start Date (YYYY-MM)")
        end = ask("    End Date (YYYY-MM) (or 'Present')")
        description = ask("    Description (Brief summary)")
        
        experiences.append({
            "job_title": job_title,
            "company": company,
            "location": location,
            "start_date": start,
            "end_date": end,
            "description": description
        })
    
    print("\n--- Languages ---")
    num_lang = int(ask("Number of languages"))
    languages = []
    for i in range(num_lang):
        print(f"  > Language #{i+1}")
        language = ask("    Language")
        is_fluent = ask("    Are you fluent?")
        comprehension = ask("    Proficiency in comprehension")
        reading = ask("    Proficiency in reading")
        speaking = ask("    Proficiency in speaking")
        writing = ask("    Proficiency in writing")
        
        languages.append({
            "language": language,
            "is_fluent": is_fluent,
            "proficiency": {
                "comprehension": comprehension,
                "reading": reading,
                "speaking": speaking,
                "writing": writing
            }
        })
        

    print("\n--- Education (Most Recent) ---")
    uni = ask("University")
    fac = ask("Faculty")
    maj = ask("Major")
    deg = ask("Degree Type")
    start_date = ask("Start Date (YYYY-MM)")
    end_date = ask("End Date (YYYY-MM)")
    gpa = ask("GPA")
    curr_year = ask("Current Year (e.g. Year 1)")

    print("\n--- Skills ---")
    def ask_list(name):
        val = ask(f"{name} (comma separated)")
        return [x.strip() for x in val.split(",") if x.strip()]

    prog_langs = ask_list("Programming Languages")
    web_tech = ask_list("Web Technologies (HTML, CSS, etc.)")
    data_sci = ask_list("Data Science Libraries")
    frameworks = ask_list("Frameworks & Tools")
    os_systems = ask_list("Operating Systems")

    print("\n--- Socials ---")
    website = ask("Personal Website/Portfolio")
    linkedin = ask("LinkedIn URL")
    github = ask("GitHub URL")
    
    print("\n--- Preferences ---")
    hear_about_us = ask("How did you hear about the company") or "LinkedIn"
    has_worked_company_before = ask("Have you worked at the company before")

    # Construct the JSON structure
    data = {
        "personal_information": {
            "legal_name": {
                "first_name": first_name,
                "middle_name": middle_name,
                "last_name": last_name,
                "prefix": prefix
            },
            "preferred_name": {
                "first_name": pref_first,
                "last_name": pref_last
            },
            "date_of_birth": dob
        },
        "contact_information": {
            "address": {
                "street": street,
                "city": city,
                "province": province,
                "country": country,
                "postal_code": postal_code
            },
            "email": email,
            "phone": {
                "device_type": device_type,
                "country_code": country_code,
                "phone_number": phone_number
            }
        },
        "residence_status": {
            "citizenships": citizenship,
            "visa_status": visa_status,
            "sponsorship": sponsorship
        },
        "diversity": {
            "sex": sex,
            "identity": identity,
            "lgbtq": lgbtq,
            "disability": disability,
            "race": race
        },

        "work_experience": experiences,

        "languages": languages,

        "education": [
            {
                "university": uni,
                "faculty": fac,
                "major": maj,
                "degree_type": deg,
                "start_date": start_date,
                "end_date": end_date,
                "gpa": gpa,
                "current_year": curr_year
            }
        ],

        "skills": {
            "programming_languages": prog_langs,
            "web_technologies": web_tech,
            "data_science": data_sci,
            "frameworks_tools": frameworks,
            "operating_systems": os_systems
        },

        "socials": {
            "website": website,
            "linkedin": linkedin,
            "github": github
        },

        "application_preferences": {
            "how_did_you_hear_about_us": hear_about_us,
            "has_worked_for_company_before": has_worked_company_before
        }
    }

    profile = json.dumps(data, indent=2)
    with open("info.json", "w") as f:
        f.write(profile)

if __name__ == "__main__":
    main()


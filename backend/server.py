from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import uuid
import csv
import io
import json


app = FastAPI(title="autojob API")

class Applicant(BaseModel):
	name: str
	email: EmailStr
	resume_url: Optional[str] = None
	cover_letter: Optional[str] = None

applications: List[dict] = []

def apply_to_jobs(applicant_data: dict) -> List[dict]:
	"""
	Placeholder function that applies to jobs.
	Returns a list of job applications with Status, Company Name, Position, Term, and Link.
	"""
	# TODO: Implement actual job application logic
	job_applications = [
		{
			"Status": "✅",
			"Company Name": "Example Corp",
			"Position": "Software Engineer",
			"Term": "Fall",
			"Link to application": "https://example.com/apply"
		}
	]
	return job_applications


def json_to_csv(data: List[dict]) -> str:
	"""
	Convert list of dictionaries to CSV format.
	"""
	if not data:
		return ""
	
	output = io.StringIO()
	fieldnames = ["Status", "Company Name", "Position", "Term", "Link to application"]
	writer = csv.DictWriter(output, fieldnames=fieldnames)
	writer.writeheader()
	writer.writerows(data)
	return output.getvalue()


@app.post("/info")
def save_info():
	# Save applicant info to a local file
	applicant_data = get_info()
	with open("applicant.json", "w") as f:
		json.dump(applicant_data, f, indent=2)
	return {"status": "applicant info saved"}

def get_info() -> dict:
	return "placeholder function to get applicant info"

@app.get("/info")
def info():
	return {
		"service": "autojob",
		"routes": ["/info (POST)", "/apply (POST)"],
		"version": "0.1",
	}

@app.post("/apply")
def apply():
	# Apply to jobs using saved applicant info
	try:
		# Load applicant info from file
		with open("applicant.json", "r") as f:
			applicant_data = json.load(f)
	except FileNotFoundError:
		return {"error": "No applicant info found. Please call POST /info first."}
	
	app_id = str(uuid.uuid4())
	applicant_data.update({"id": app_id})
	applications.append(applicant_data)
	
	# Apply to jobs and get results as JSON
	job_applications = apply_to_jobs(applicant_data)
	
	# Convert JSON to CSV
	csv_output = json_to_csv(job_applications)
	
	return {
		"status": "received",
		"id": app_id,
		"csv_output": csv_output
	}
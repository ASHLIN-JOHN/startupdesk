from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import uuid
from datetime import datetime
from parsers import parse_document
from crew_agents import PitchDeckEvaluationCrew
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="VC Pitch Deck Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

UPLOAD_DIR = "uploads"
REPORTS_DIR = "reports"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

evaluation_cache = {}


@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main web interface."""
    with open("static/index.html", "r") as f:
        return f.read()


@app.post("/upload")
async def upload_deck(
    file: UploadFile = File(...),
    company_name: str = Form(...),
    sector: str = Form(...),
    stage: str = Form(...),
    funding_ask: str = Form(...),
    fund_thesis: str = Form(""),
    contact_email: str = Form("")
):
    """Upload and evaluate a pitch deck."""
    
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")
    
    evaluation_id = str(uuid.uuid4())
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ['.pdf', '.pptx']:
        raise HTTPException(status_code=400, detail="Only PDF and PPTX files are supported")
    
    file_path = os.path.join(UPLOAD_DIR, f"{evaluation_id}{file_ext}")
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    try:
        parsed_data = parse_document(file_path)
        
        deck_data = {
            "company_name": company_name,
            "sector": sector,
            "stage": stage,
            "funding_ask": funding_ask,
            "fund_thesis": fund_thesis,
            "content": parsed_data["content"]
        }
        
        crew = PitchDeckEvaluationCrew(groq_api_key)
        evaluation_result = crew.evaluate_pitch_deck(deck_data)
        
        evaluation_result["evaluation_id"] = evaluation_id
        evaluation_result["timestamp"] = datetime.now().isoformat()
        evaluation_result["filename"] = file.filename
        
        report_path = os.path.join(REPORTS_DIR, f"{evaluation_id}.json")
        with open(report_path, "w") as f:
            json.dump(evaluation_result, f, indent=2)
        
        evaluation_cache[evaluation_id] = evaluation_result
        
        if contact_email and os.getenv("SENDGRID_API_KEY"):
            try:
                send_evaluation_email(contact_email, evaluation_result)
            except Exception as e:
                print(f"Failed to send email: {e}")
        
        return JSONResponse(content={
            "evaluation_id": evaluation_id,
            "result": evaluation_result
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@app.get("/result/{evaluation_id}")
async def get_result(evaluation_id: str):
    """Retrieve evaluation result by ID."""
    
    if evaluation_id in evaluation_cache:
        return JSONResponse(content=evaluation_cache[evaluation_id])
    
    report_path = os.path.join(REPORTS_DIR, f"{evaluation_id}.json")
    
    if os.path.exists(report_path):
        with open(report_path, "r") as f:
            result = json.load(f)
        evaluation_cache[evaluation_id] = result
        return JSONResponse(content=result)
    
    raise HTTPException(status_code=404, detail="Evaluation not found")


def send_evaluation_email(to_email: str, evaluation: dict):
    """Send evaluation report via SendGrid."""
    
    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@pitchanalyzer.com")
    
    if not sendgrid_api_key:
        return
    
    subject = f"Pitch Deck Evaluation - {evaluation['company_name']}"
    
    html_content = f"""
    <h2>Pitch Deck Evaluation Report</h2>
    <h3>{evaluation['company_name']} - {evaluation['sector']}</h3>
    
    <h4>Scores:</h4>
    <ul>
        <li>Market Size: {evaluation['scores']['market_size']}/10</li>
        <li>Team: {evaluation['scores']['team']}/10</li>
        <li>Product: {evaluation['scores']['product']}/10</li>
        <li>Traction: {evaluation['scores']['traction']}/10</li>
        <li>Financials: {evaluation['scores']['financials']}/10</li>
        <li><strong>Overall: {evaluation['scores']['overall']}/10</strong></li>
    </ul>
    
    <h4>Investment Decision: {evaluation['investible']}</h4>
    
    <h4>Summary:</h4>
    <p>{evaluation.get('summary', '')}</p>
    
    <h4>Key Strengths:</h4>
    <ul>
        {''.join([f"<li>{s}</li>" for s in evaluation.get('key_strengths', [])])}
    </ul>
    
    <h4>Key Concerns:</h4>
    <ul>
        {''.join([f"<li>{c}</li>" for c in evaluation.get('key_concerns', [])])}
    </ul>
    """
    
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=html_content
    )
    
    sg = SendGridAPIClient(sendgrid_api_key)
    response = sg.send(message)
    
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

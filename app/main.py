from fastapi import FastAPI

app = FastAPI(title="Agentic Incident Copilot", description="An AI-powered incident management system that helps teams respond to incidents quickly and effectively.", version="1.0.0")

@app.get("/health")
def health_check():
    return {"status": "OK", "message": "Healthy"}
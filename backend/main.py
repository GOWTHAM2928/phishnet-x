from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

from api.predict import router as predict_router
from api.chat import router as chat_router

app = FastAPI(
    title="PhishNet X API",
    description="AI-powered phishing detection system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict_router, prefix="/predict", tags=["Prediction"])
app.include_router(chat_router, prefix="/chat", tags=["Chat"])

@app.get("/")
def root():
    return {"message": "PhishNet X API is running", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

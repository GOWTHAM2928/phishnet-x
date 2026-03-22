from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
import urllib.parse

from utils.feature_extractor import extract_features, get_feature_list
from utils.risk_scorer import calculate_risk_score, score_to_status
from utils.domain_checker import check_domain_info, get_domain_risk_factor
from model.predictor import predict_phishing

router = APIRouter()


class PredictRequest(BaseModel):
    url: str


class PredictResponse(BaseModel):
    url: str
    risk_score: int
    status: str  # safe / suspicious / phishing
    reasons: List[str]
    features: Optional[dict] = None
    model_used: bool = False


@router.post("", response_model=PredictResponse)
async def predict_url(request: PredictRequest):
    url = request.url.strip()

    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")

    # Normalize URL
    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    try:
        parsed = urllib.parse.urlparse(url)
        hostname = parsed.hostname or ""
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid URL format")

    # 1. Extract features
    features = extract_features(url)

    # 2. ML prediction
    feature_vector = get_feature_list(features)
    ml_probability, model_used = predict_phishing(feature_vector)

    # 3. Domain info
    domain_info = check_domain_info(hostname)
    domain_risk = get_domain_risk_factor(domain_info)

    # Adjust ML probability based on domain age
    if domain_info.get("is_new_domain"):
        ml_probability = min(1.0, ml_probability + 0.15)

    # 4. Risk score + reasons
    risk_score, reasons = calculate_risk_score(features, ml_probability)

    # Add domain age reason if applicable
    if domain_info.get("is_new_domain"):
        age = domain_info.get("domain_age_days")
        if age:
            reasons.append(f"Domain is very new ({age} days old) — recently created domains are often used for phishing")

    # 5. Status
    status = score_to_status(risk_score)

    return PredictResponse(
        url=url,
        risk_score=risk_score,
        status=status,
        reasons=reasons,
        features=features,
        model_used=model_used
    )

import os
import pickle
import numpy as np
from typing import Tuple

MODEL_PATH = os.path.join(os.path.dirname(__file__), "phishnet_model.pkl")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "scaler.pkl")

_model = None
_scaler = None
_model_available = False


def _load_model():
    global _model, _scaler, _model_available
    if _model is not None:
        return

    if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
        try:
            with open(MODEL_PATH, "rb") as f:
                _model = pickle.load(f)
            with open(SCALER_PATH, "rb") as f:
                _scaler = pickle.load(f)
            _model_available = True
            print("ML model loaded successfully.")
        except Exception as e:
            print(f"Failed to load model: {e}")
            _model_available = False
    else:
        print("ML model not found. Run model/train_model.py to train it.")
        _model_available = False


def predict_phishing(feature_vector: list) -> Tuple[float, bool]:
    """
    Predict phishing probability from feature vector.
    Returns (probability, model_available).
    """
    _load_model()

    if not _model_available:
        return 0.5, False  # Neutral probability when model unavailable

    try:
        X = np.array(feature_vector).reshape(1, -1)
        X_scaled = _scaler.transform(X)
        proba = _model.predict_proba(X_scaled)[0][1]
        return float(proba), True
    except Exception as e:
        print(f"Prediction error: {e}")
        return 0.5, False

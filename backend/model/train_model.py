"""
PhishNet X — ML Model Trainer
==============================
Trains a RandomForest + XGBoost ensemble on phishing URL datasets.

Usage:
    python train_model.py

Dataset:
    - Place your dataset CSV at: model/phishing_dataset.csv
    - Required columns: 'url' (string), 'label' (0=safe, 1=phishing)

    Recommended datasets:
    - Kaggle: "Web page Phishing Detection Dataset"
    - UCI: "Phishing Websites Data Set"
    - PhiUSIIL Phishing URL Dataset
"""

import os
import pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    print("XGBoost not installed. Using RandomForest only.")

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.feature_extractor import extract_features, get_feature_list

MODEL_PATH = os.path.join(os.path.dirname(__file__), "phishnet_model.pkl")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "scaler.pkl")
DATASET_PATH = os.path.join(os.path.dirname(__file__), "phishing_dataset.csv")


def generate_synthetic_dataset(n_samples: int = 5000) -> pd.DataFrame:
    """
    Generate a synthetic dataset for demo/testing purposes.
    Replace with real dataset for production use.
    """
    import random
    import string

    safe_domains = [
        "google.com", "github.com", "stackoverflow.com", "wikipedia.org",
        "amazon.com", "microsoft.com", "apple.com", "youtube.com",
        "reddit.com", "linkedin.com", "twitter.com", "facebook.com"
    ]

    phishing_patterns = [
        "paypal-secure-login.xyz", "amazon-update-account.tk",
        "microsoft-verify.ml", "apple-id-confirm.online",
        "secure-bank-login.top", "facebook-verify-account.site",
        "192.168.1.1/phish/login", "netflix-update.club"
    ]

    data = []

    # Generate safe URLs
    for _ in range(n_samples // 2):
        domain = random.choice(safe_domains)
        paths = ["", "/about", "/help", "/products", "/news", "/blog"]
        url = f"https://{domain}{random.choice(paths)}"
        data.append({"url": url, "label": 0})

    # Generate phishing URLs
    for _ in range(n_samples // 2):
        base = random.choice(phishing_patterns)
        url = f"http://{base}?id={''.join(random.choices(string.ascii_lowercase, k=8))}"
        data.append({"url": url, "label": 1})

    df = pd.DataFrame(data)
    df = df.sample(frac=1).reset_index(drop=True)
    return df


def load_dataset() -> pd.DataFrame:
    """Load dataset from CSV or generate synthetic one."""
    if os.path.exists(DATASET_PATH):
        print(f"Loading dataset from {DATASET_PATH}")
        df = pd.read_csv(DATASET_PATH)
        # Normalize column names
        df.columns = [c.lower().strip() for c in df.columns]
        if "url" not in df.columns or "label" not in df.columns:
            raise ValueError("Dataset must have 'url' and 'label' columns")
        return df
    else:
        print("No dataset found. Generating synthetic dataset for demo...")
        print("For production, place your CSV at: model/phishing_dataset.csv")
        return generate_synthetic_dataset(5000)


def extract_all_features(urls: list) -> np.ndarray:
    """Extract features for all URLs."""
    features_list = []
    for url in urls:
        feats = extract_features(str(url))
        features_list.append(get_feature_list(feats))
    return np.array(features_list)


def train():
    print("=" * 50)
    print("PhishNet X — Model Training")
    print("=" * 50)

    # Load data
    df = load_dataset()
    print(f"Dataset size: {len(df)} samples")
    print(f"Label distribution:\n{df['label'].value_counts()}")

    # Extract features
    print("\nExtracting URL features...")
    X = extract_all_features(df["url"].tolist())
    y = df["label"].values

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Scale
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Build model
    print("\nTraining model...")
    rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)

    if HAS_XGB:
        xgb = XGBClassifier(
            n_estimators=100, max_depth=6, learning_rate=0.1,
            use_label_encoder=False, eval_metric="logloss",
            random_state=42
        )
        model = VotingClassifier(
            estimators=[("rf", rf), ("xgb", xgb)],
            voting="soft"
        )
    else:
        model = rf

    model.fit(X_train_scaled, y_train)

    # Evaluate
    y_pred = model.predict(X_test_scaled)
    y_proba = model.predict_proba(X_test_scaled)[:, 1]

    print("\n--- Evaluation Results ---")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(f"AUC-ROC:  {roc_auc_score(y_test, y_proba):.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Safe", "Phishing"]))

    # Save model and scaler
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    with open(SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)

    print(f"\nModel saved to: {MODEL_PATH}")
    print(f"Scaler saved to: {SCALER_PATH}")
    print("\nTraining complete!")


if __name__ == "__main__":
    train()

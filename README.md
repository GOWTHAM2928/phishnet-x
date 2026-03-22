# 🛡️ PhishNet X — AI-Powered Phishing Detection System

PhishNet X is a production-ready cybersecurity tool combining a **FastAPI backend**, **ML phishing engine**, and a **Chrome extension** with real-time URL scanning and an AI security assistant.

---

## 📁 Project Structure

```
phishnet-x/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── requirements.txt
│   ├── api/
│   │   ├── predict.py             # POST /predict endpoint
│   │   └── chat.py                # POST /chat endpoint
│   ├── model/
│   │   ├── train_model.py         # Train ML model
│   │   ├── predictor.py           # Model loader + inference
│   │   └── phishing_dataset.csv   # (place your dataset here)
│   └── utils/
│       ├── feature_extractor.py   # 23 URL features
│       ├── risk_scorer.py         # Heuristic + ML scoring
│       ├── domain_checker.py      # WHOIS + DNS
│       └── generate_icons.py      # Icon generator
│
├── extension/
│   ├── manifest.json              # Chrome Manifest v3
│   ├── background.js              # Service worker (auto-scan)
│   ├── content.js                 # Page overlay alerts
│   ├── popup.html                 # Extension popup UI
│   ├── popup.js                   # Popup logic + chat
│   ├── styles.css                 # macOS-inspired design
│   └── icons/                     # Extension icons
│
└── README.md
```

---

## ⚡ Quick Setup

### Prerequisites
- Python 3.9+
- Google Chrome (or Chromium-based browser)
- pip

---

### 1. Backend Setup

```bash
# Navigate to backend
cd phishnet-x/backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
```

---

### 2. Train the ML Model

**Option A — Use your own dataset (recommended for production):**
```bash
# Download from Kaggle: "Web page Phishing Detection Dataset"
# or UCI: "Phishing Websites Data Set"
# Place the CSV at: backend/model/phishing_dataset.csv
# Required columns: 'url' (string), 'label' (0=safe, 1=phishing)

cd backend
python model/train_model.py
```

**Option B — Use the built-in synthetic dataset (for demo/testing):**
```bash
cd backend
python model/train_model.py
# Will auto-generate 5,000 synthetic samples if no CSV is found
```

Training output:
```
PhishNet X — Model Training
Dataset size: 5000 samples
Extracting URL features...
Training model...
Accuracy: 0.9720
AUC-ROC:  0.9891
Model saved to: model/phishnet_model.pkl
```

---

### 3. Start the Backend API

```bash
cd phishnet-x/backend
python main.py
# OR
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API will be live at: **http://localhost:8000**

- Swagger docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

---

### 4. Generate Extension Icons

```bash
cd phishnet-x/backend
pip install Pillow   # or: pip install cairosvg
python utils/generate_icons.py
```

This creates `extension/icons/icon16.png`, `icon32.png`, `icon48.png`, `icon128.png`.

> **Manual alternative:** Place any 4 PNG files named `icon16.png`, `icon32.png`, `icon48.png`, `icon128.png` in `extension/icons/`.

---

### 5. Load the Chrome Extension

1. Open Chrome and navigate to: `chrome://extensions/`
2. Enable **Developer Mode** (toggle, top-right corner)
3. Click **"Load unpacked"**
4. Select the `phishnet-x/extension/` folder
5. The PhishNet X shield icon will appear in your toolbar

---

## 🚀 Usage

Once both the backend and extension are running:

1. **Open any website** — PhishNet X automatically scans the URL
2. **Click the shield icon** in the toolbar to see:
   - Risk score (0–100 gauge)
   - Status: ✅ Safe / ⚠️ Suspicious / 🚨 Phishing
   - Detailed threat reasons
3. **Phishing sites** trigger an automatic red banner on the page
4. **Chat tab** — Ask the AI assistant questions like:
   - *"Is this site safe?"*
   - *"Why was this flagged?"*
   - *"What should I do if I entered my password?"*

---

## 🔌 API Reference

### `POST /predict`
Scan a URL for phishing.

**Request:**
```json
{ "url": "http://paypal-secure-login.xyz/verify" }
```

**Response:**
```json
{
  "url": "http://paypal-secure-login.xyz/verify",
  "risk_score": 87,
  "status": "phishing",
  "reasons": [
    "Domain appears to impersonate a known brand (paypal-secure-login.xyz)",
    "Connection is not encrypted (HTTP instead of HTTPS)",
    "Domain uses a suspicious top-level domain (.xyz)",
    "Machine learning model flagged this URL with high phishing confidence"
  ],
  "model_used": true
}
```

### `POST /chat`
AI security assistant.

**Request:**
```json
{
  "message": "Why is this site flagged?",
  "context": {
    "url": "http://paypal-secure-login.xyz",
    "risk_score": 87,
    "status": "phishing",
    "reasons": ["Brand impersonation detected"]
  }
}
```

**Response:**
```json
{ "reply": "🔍 Why this URL was flagged (Risk Score: 87/100)..." }
```

---

## 🧠 How It Works

### Feature Extraction (23 features)
| Feature | Description |
|---|---|
| `url_length` | Total URL character count |
| `has_https` | HTTPS protocol check |
| `num_dots` | Dots in hostname |
| `has_at_symbol` | `@` symbol detection |
| `is_ip_url` | IP address as domain |
| `subdomain_count` | Number of subdomains |
| `suspicious_keyword_count` | Login/verify/secure keywords |
| `has_suspicious_tld` | .xyz/.tk/.ml/.top etc. |
| `brand_impersonation_score` | Known brand in wrong domain |
| `is_url_shortener` | bit.ly/tinyurl detection |
| `domain_digit_ratio` | Numeric ratio in domain |
| `has_encoded_chars` | URL-encoded characters |
| `uses_non_standard_port` | Non 80/443 port |
| + 10 more | Length, slashes, hyphens, query params... |

### Risk Scoring
```
Final Score = (ML Probability × 60%) + (Heuristic Score × 40%)

0–39   → ✅ Safe
40–69  → ⚠️ Suspicious  
70–100 → 🚨 Phishing
```

### Auto-Scanning Flow
```
Tab Updated → Debounce (800ms) → Check Cache → API Call → Update Badge → Show Result
```

---

## 🔒 Security Notes

- The backend runs locally — no data is sent to external servers
- All scans happen on-device
- Minimal extension permissions: `tabs`, `activeTab`, `storage`, `notifications`, `scripting`
- Cache prevents duplicate API calls (5-minute TTL)

---

## 🧪 Testing URLs

```bash
# Test safe URL
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com"}'

# Test phishing URL
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"url": "http://paypal-secure-update.xyz/login?verify=1"}'

# Test chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is phishing?"}'
```

---

## 📦 Recommended Datasets

| Dataset | Source | Size |
|---|---|---|
| Web Page Phishing Detection | Kaggle | 11,000+ samples |
| PhiUSIIL Phishing URL | UCI ML Repo | 235,000+ samples |
| PhishTank URL Dataset | PhishTank.com | Updated daily |
| OpenPhish Feed | openphish.com | Live phishing URLs |

---

## 🔧 Configuration

Edit `extension/background.js` to change:
```js
const API_BASE = "http://localhost:8000";  // Backend URL
const CACHE_DURATION_MS = 5 * 60 * 1000;  // Cache TTL (5 min)
const DEBOUNCE_MS = 800;                   // Scan delay
```

---

## 🚀 Production Deployment

For production use:

1. **Deploy backend** to a server (e.g., DigitalOcean, AWS EC2, Railway)
2. **Update API_BASE** in `background.js` to your server URL
3. **Add HTTPS** to the backend (required for HTTPS pages)
4. **Replace synthetic dataset** with real phishing data
5. **Retrain model** on production dataset
6. **Submit extension** to Chrome Web Store

---

## 📄 License

MIT License — Free to use, modify, and distribute.

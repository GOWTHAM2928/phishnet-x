from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
    genai.configure(api_key=GEMINI_API_KEY)
    # Using gemini-2.5-flash as it's the latest fast model
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    model = None

class ScanContext(BaseModel):
    url: Optional[str] = None
    risk_score: Optional[int] = None
    status: Optional[str] = None
    reasons: Optional[List[str]] = None


class ChatRequest(BaseModel):
    message: str
    context: Optional[ScanContext] = None


class ChatResponse(BaseModel):
    reply: str


def generate_rule_based_reply(message: str, context: Optional[ScanContext]) -> str:
    """
    Rule-based AI assistant. Generates contextual explanations
    about phishing threats and security concepts.
    """
    msg = message.lower().strip()

    # --- Context-aware responses ---
    if context and context.url:
        url = context.url
        score = context.risk_score or 0
        status = context.status or "unknown"
        reasons = context.reasons or []

        if any(kw in msg for kw in ["safe", "is this", "current", "this site", "this url", "this page"]):
            if status == "safe":
                return (
                    f"✅ **This URL appears safe.**\n\n"
                    f"The site `{url}` has a low risk score of **{score}/100**. "
                    f"No significant phishing indicators were detected. "
                    f"However, always stay cautious and avoid entering sensitive information on unfamiliar sites."
                )
            elif status == "suspicious":
                reason_text = "\n• ".join(reasons[:3]) if reasons else "multiple warning signs"
                return (
                    f"⚠️ **This URL is suspicious and should be treated with caution.**\n\n"
                    f"Risk score: **{score}/100**\n\n"
                    f"Key concerns:\n• {reason_text}\n\n"
                    f"Recommendation: Do not enter passwords, credit card numbers, or personal information on this site."
                )
            elif status == "phishing":
                reason_text = "\n• ".join(reasons[:3]) if reasons else "strong phishing indicators"
                return (
                    f"🚨 **WARNING: This URL is likely a phishing site!**\n\n"
                    f"Risk score: **{score}/100** — This is very high.\n\n"
                    f"Detected threats:\n• {reason_text}\n\n"
                    f"**Immediate actions:**\n"
                    f"1. Do NOT enter any credentials or personal data\n"
                    f"2. Close this tab immediately\n"
                    f"3. If you already entered data, change your passwords now\n"
                    f"4. Report this site to Google Safe Browsing"
                )

        if any(kw in msg for kw in ["why", "explain", "reason", "threat", "phishing", "risk"]):
            if reasons:
                reason_text = "\n• ".join(reasons)
                return (
                    f"🔍 **Why this URL was flagged (Risk Score: {score}/100)**\n\n"
                    f"PhishNet X detected the following issues:\n\n• {reason_text}\n\n"
                    f"These patterns are commonly associated with phishing attacks. "
                    f"Legitimate sites generally use HTTPS, have established domains, "
                    f"and don't rely on suspicious keywords or URL tricks."
                )

        if any(kw in msg for kw in ["score", "what does", "what is", "mean"]):
            if score < 40:
                level = "LOW risk"
                emoji = "✅"
            elif score < 70:
                level = "MODERATE risk"
                emoji = "⚠️"
            else:
                level = "HIGH risk"
                emoji = "🚨"

            return (
                f"{emoji} **Risk Score: {score}/100 — {level}**\n\n"
                f"PhishNet X scores URLs from 0 (completely safe) to 100 (confirmed phishing).\n\n"
                f"• **0–39**: Safe — no significant threats detected\n"
                f"• **40–69**: Suspicious — proceed with caution\n"
                f"• **70–100**: Phishing — avoid this site immediately\n\n"
                f"The score for `{url}` is **{score}**, placing it in the **{level}** category."
            )

    # --- General security knowledge ---
    if any(kw in msg for kw in ["what is phishing", "define phishing", "phishing mean"]):
        return (
            "🎣 **What is Phishing?**\n\n"
            "Phishing is a type of cyberattack where criminals create fake websites or send deceptive emails "
            "to trick you into revealing sensitive information like passwords, credit card numbers, or personal data.\n\n"
            "**Common tactics include:**\n"
            "• Fake login pages impersonating trusted brands (PayPal, Amazon, Google)\n"
            "• Urgent messages pressuring quick action ('Your account will be suspended!')\n"
            "• Suspicious URLs with misspellings or extra subdomains\n"
            "• HTTP (non-encrypted) connections\n\n"
            "PhishNet X analyzes 20+ URL features to detect these threats automatically."
        )

    if any(kw in msg for kw in ["how does phishnet", "how does this work", "how it works", "how does it"]):
        return (
            "⚙️ **How PhishNet X Works**\n\n"
            "PhishNet X uses a multi-layer approach to detect phishing URLs:\n\n"
            "1. **Feature Extraction**: Analyzes 20+ URL characteristics (length, HTTPS, subdomains, keywords, etc.)\n"
            "2. **ML Model**: A Random Forest + XGBoost ensemble trained on phishing datasets assigns a probability score\n"
            "3. **Heuristic Analysis**: Rule-based checks catch known phishing patterns\n"
            "4. **Domain Intelligence**: Checks domain age and DNS resolution\n"
            "5. **Risk Scoring**: Combines all signals into a 0–100 score\n\n"
            "The extension runs this automatically whenever you visit a new page."
        )

    if any(kw in msg for kw in ["protect", "stay safe", "tips", "advice", "avoid"]):
        return (
            "🛡️ **How to Stay Safe Online**\n\n"
            "1. **Check the URL carefully** — Look for misspellings, extra subdomains, or unusual domains\n"
            "2. **Always use HTTPS** — Look for the padlock icon in your browser\n"
            "3. **Don't click suspicious links** — Hover over links to preview the destination\n"
            "4. **Use a password manager** — It won't autofill on fake sites\n"
            "5. **Enable 2FA** — Even if credentials are stolen, 2FA blocks access\n"
            "6. **Keep software updated** — Patches close security vulnerabilities\n"
            "7. **Trust PhishNet X** — Let it scan every site automatically!\n\n"
            "Remember: Legitimate organizations never ask for passwords via email."
        )

    if any(kw in msg for kw in ["what should i do", "already entered", "already typed", "gave my"]):
        return (
            "🚨 **If You May Have Entered Credentials on a Phishing Site:**\n\n"
            "Act immediately:\n\n"
            "1. **Change your password** on the real website right now\n"
            "2. **Change passwords on other accounts** that use the same password\n"
            "3. **Enable 2FA** on all critical accounts (email, banking, social media)\n"
            "4. **Contact your bank** if you entered financial information\n"
            "5. **Monitor your accounts** for suspicious activity\n"
            "6. **Report the phishing site** at: https://safebrowsing.google.com/safebrowsing/report_phish/\n\n"
            "Time is critical — act as fast as possible to minimize damage."
        )

    if any(kw in msg for kw in ["hello", "hi", "hey", "help"]):
        return (
            "👋 **Hello! I'm PhishNet X Assistant.**\n\n"
            "I'm here to help you understand online threats and stay secure. You can ask me:\n\n"
            "• *\"Is this site safe?\"* — Analysis of the current page\n"
            "• *\"Why was this flagged?\"* — Explanation of detected threats\n"
            "• *\"What does the risk score mean?\"* — Score interpretation\n"
            "• *\"What is phishing?\"* — General education\n"
            "• *\"How can I stay safe?\"* — Security tips\n"
            "• *\"What should I do if I entered my password?\"* — Incident response\n\n"
            "How can I help you today?"
        )

    # Default response
    return (
        "🤖 **PhishNet X Assistant**\n\n"
        "I can help you with:\n\n"
        "• Explaining why a URL was flagged as phishing\n"
        "• Interpreting risk scores\n"
        "• General phishing education and security tips\n"
        "• Advice on what to do if you suspect you've been phished\n\n"
        "Try asking: *'Is this site safe?'* or *'Why was this flagged?'*"
    )


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    if model is None:
        # Fallback to rule-based if Gemini API key is missing
        reply = "⚠️ *Gemini API key is not configured in .env. Falling back to rule-based responses.*\n\n"
        reply += generate_rule_based_reply(request.message, request.context)
        return ChatResponse(reply=reply)

    # Build prompt for Gemini
    prompt = "You are PhishNet X Assistant, a friendly, encouraging, and highly knowledgeable cybersecurity AI companion.\n\n"
    
    if request.context and request.context.url:
        prompt += f"Context of current page scanned:\n"
        prompt += f"- Current URL: {request.context.url}\n"
        prompt += f"- Risk Score: {request.context.risk_score}/100\n"
        prompt += f"- Status: {request.context.status}\n"
        if request.context.reasons:
            reasons = "\n  - ".join(request.context.reasons)
            prompt += f"- Detected Patterns:\n  - {reasons}\n"
        prompt += "\n"

    prompt += f"User Message: {request.message}\n\n"
    prompt += "Instructions:\n"
    prompt += "- Give simple, direct, and proper answers to the user's question.\n"
    prompt += "- Avoid long introductions, filler text, or overly flowery language.\n"
    prompt += "- Focus on providing exactly the information requested concisely.\n"
    prompt += "- Maintain a friendly but professional cybersecurity expert persona.\n"
    prompt += "- Use Markdown (bolding, lists) to make the core answer easy to read at a glance.\n"
    prompt += "- If the user asks about the current site, give a brief and clear summary of its safety status based on the provided score and reasons.\n"
    prompt += "- Do not use HTML tags.\n"

    try:
        response = model.generate_content(prompt)
        reply = response.text
    except Exception as e:
        reply = f"⚠️ *Gemini AI API error: {str(e)}*\n\n"
        reply += generate_rule_based_reply(request.message, request.context)

    return ChatResponse(reply=reply)

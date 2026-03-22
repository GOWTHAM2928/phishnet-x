from typing import Dict, Any, List, Tuple


def calculate_risk_score(features: Dict[str, Any], ml_probability: float) -> Tuple[int, List[str]]:
    """
    Calculate risk score (0–100) and generate human-readable reasons.
    Combines ML probability with heuristic analysis.
    """
    reasons = []
    heuristic_score = 0

    # --- Heuristic rule checks ---

    if not features.get("has_https"):
        heuristic_score += 15
        reasons.append("Connection is not encrypted (HTTP instead of HTTPS)")

    if features.get("has_at_symbol"):
        heuristic_score += 20
        reasons.append("URL contains '@' symbol — a common phishing trick to hide real destination")

    if features.get("is_ip_url"):
        heuristic_score += 25
        reasons.append("URL uses an IP address instead of a domain name")

    if features.get("brand_impersonation_score", 0) > 0:
        heuristic_score += 30
        reasons.append("Domain appears to impersonate a known brand (e.g., paypal-secure.xyz)")

    if features.get("has_suspicious_tld"):
        heuristic_score += 15
        reasons.append("Domain uses a suspicious top-level domain (.xyz, .tk, .ml, etc.)")

    if features.get("is_url_shortener"):
        heuristic_score += 10
        reasons.append("URL uses a shortening service that may hide the real destination")

    url_len = features.get("url_length", 0)
    if url_len > 100:
        heuristic_score += 10
        reasons.append(f"Unusually long URL ({url_len} characters) — often used to obscure destination")
    elif url_len > 75:
        heuristic_score += 5

    if features.get("subdomain_count", 0) > 2:
        heuristic_score += 10
        reasons.append("Excessive subdomains detected — common in phishing to mimic legitimate sites")

    if features.get("suspicious_keyword_count", 0) >= 2:
        heuristic_score += 15
        reasons.append("Multiple suspicious keywords detected (login, verify, secure, etc.)")
    elif features.get("suspicious_keyword_count", 0) == 1:
        heuristic_score += 7

    if features.get("has_encoded_chars"):
        heuristic_score += 8
        reasons.append("URL contains encoded characters that may obscure its true destination")

    if features.get("has_double_slash"):
        heuristic_score += 10
        reasons.append("Unusual double-slash in URL path — potential redirection attack")

    if features.get("uses_non_standard_port"):
        heuristic_score += 12
        reasons.append("Non-standard port used — legitimate sites rarely use uncommon ports")

    if features.get("domain_digit_ratio", 0) > 0.3:
        heuristic_score += 8
        reasons.append("Domain contains an unusual proportion of numbers")

    if features.get("num_hyphens", 0) > 2:
        heuristic_score += 8
        reasons.append("Multiple hyphens in domain — common in fake domains mimicking real ones")

    # Cap heuristic score at 100
    heuristic_score = min(heuristic_score, 100)

    # --- Combine ML probability with heuristic score ---
    ml_score = ml_probability * 100
    combined_score = int((ml_score * 0.6) + (heuristic_score * 0.4))
    combined_score = min(100, max(0, combined_score))

    # Add ML-based reason if high confidence
    if ml_probability > 0.8:
        reasons.append("Machine learning model flagged this URL with high phishing confidence")
    elif ml_probability > 0.5:
        reasons.append("Machine learning model detected suspicious patterns in this URL")

    # If no reasons found, it's likely safe
    if not reasons:
        reasons.append("No significant phishing indicators detected")

    return combined_score, reasons


def score_to_status(score: int) -> str:
    """Convert numeric score to status label."""
    if score >= 70:
        return "phishing"
    elif score >= 40:
        return "suspicious"
    else:
        return "safe"

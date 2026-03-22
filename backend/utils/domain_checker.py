import socket
import re
from datetime import datetime
from typing import Optional, Dict, Any


def check_domain_info(hostname: str) -> Dict[str, Any]:
    """
    Check domain information including basic DNS resolution.
    Falls back gracefully if WHOIS is unavailable.
    """
    info = {
        "resolvable": False,
        "domain_age_days": None,
        "is_new_domain": False,
        "ip_address": None,
    }

    if not hostname:
        return info

    # DNS resolution check
    try:
        ip = socket.gethostbyname(hostname)
        info["resolvable"] = True
        info["ip_address"] = ip
    except socket.gaierror:
        info["resolvable"] = False

    # Try WHOIS if python-whois is available
    try:
        import whois
        w = whois.whois(hostname)
        creation_date = w.creation_date

        if isinstance(creation_date, list):
            creation_date = creation_date[0]

        if creation_date and isinstance(creation_date, datetime):
            age_days = (datetime.now() - creation_date).days
            info["domain_age_days"] = age_days
            info["is_new_domain"] = age_days < 90  # Domains < 90 days are suspicious

    except Exception:
        # WHOIS not available or failed — use heuristic
        pass

    return info


def get_domain_risk_factor(domain_info: Dict[str, Any]) -> int:
    """
    Return additional risk score from domain info (0-20).
    """
    score = 0

    if not domain_info.get("resolvable"):
        score += 5  # Unresolvable domains are less risky (might just be offline)

    if domain_info.get("is_new_domain"):
        score += 15  # Very new domains are highly suspicious

    return score

import re
import urllib.parse
from typing import Dict, Any
import ipaddress


def extract_features(url: str) -> Dict[str, Any]:
    """
    Extract 20+ features from a URL for phishing detection.
    Returns a dictionary of feature name -> value.
    """
    features = {}

    try:
        parsed = urllib.parse.urlparse(url)
        hostname = parsed.hostname or ""
        path = parsed.path or ""
        query = parsed.query or ""
        full_url = url.lower()

        # --- Basic URL features ---
        features["url_length"] = len(url)
        features["hostname_length"] = len(hostname)
        features["path_length"] = len(path)

        # HTTPS check
        features["has_https"] = 1 if parsed.scheme == "https" else 0

        # Number of dots in hostname
        features["num_dots"] = hostname.count(".")

        # Has @ symbol (common phishing trick)
        features["has_at_symbol"] = 1 if "@" in url else 0

        # Has hyphen in domain
        features["has_hyphen"] = 1 if "-" in hostname else 0

        # Number of hyphens
        features["num_hyphens"] = hostname.count("-")

        # Subdomain count
        parts = hostname.split(".")
        features["subdomain_count"] = max(0, len(parts) - 2)

        # IP-based URL detection
        features["is_ip_url"] = 0
        try:
            ipaddress.ip_address(hostname)
            features["is_ip_url"] = 1
        except ValueError:
            pass

        # Number of slashes in path
        features["num_slashes"] = path.count("/")

        # Has query string
        features["has_query"] = 1 if query else 0

        # Query string length
        features["query_length"] = len(query)

        # Number of query parameters
        features["num_query_params"] = len(urllib.parse.parse_qs(query))

        # Suspicious keywords in URL
        suspicious_words = [
            "login", "signin", "verify", "update", "secure", "account",
            "banking", "confirm", "password", "paypal", "amazon", "google",
            "microsoft", "apple", "ebay", "facebook", "netflix", "phish",
            "click", "free", "win", "prize", "urgent", "alert"
        ]
        features["suspicious_keyword_count"] = sum(
            1 for word in suspicious_words if word in full_url
        )

        # Has suspicious TLD
        suspicious_tlds = [
            ".xyz", ".top", ".club", ".online", ".site", ".tk", ".ml",
            ".ga", ".cf", ".gq", ".pw", ".cc", ".info", ".biz"
        ]
        features["has_suspicious_tld"] = 1 if any(
            hostname.endswith(tld) for tld in suspicious_tlds
        ) else 0

        # URL contains encoded characters
        features["has_encoded_chars"] = 1 if "%" in url else 0

        # Number of special characters
        special_chars = re.findall(r'[!$&\'()*+,;=]', url)
        features["num_special_chars"] = len(special_chars)

        # Double slash in path (redirection trick)
        features["has_double_slash"] = 1 if "//" in path else 0

        # Numeric characters in domain
        num_digits = sum(c.isdigit() for c in hostname)
        features["domain_digit_ratio"] = num_digits / max(len(hostname), 1)

        # URL shortener detection
        shorteners = [
            "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly",
            "is.gd", "buff.ly", "adf.ly", "short.to"
        ]
        features["is_url_shortener"] = 1 if any(s in hostname for s in shorteners) else 0

        # Brand impersonation check (typosquatting)
        known_brands = [
            "paypal", "amazon", "google", "microsoft", "apple",
            "facebook", "netflix", "twitter", "instagram", "ebay"
        ]
        impersonation_score = 0
        for brand in known_brands:
            if brand in hostname and not hostname.endswith(f"{brand}.com"):
                impersonation_score += 1
        features["brand_impersonation_score"] = impersonation_score

        # Port usage (non-standard port = suspicious)
        features["uses_non_standard_port"] = 0
        if parsed.port and parsed.port not in [80, 443]:
            features["uses_non_standard_port"] = 1

    except Exception as e:
        # Return defaults if parsing fails
        features = {k: 0 for k in [
            "url_length", "hostname_length", "path_length", "has_https",
            "num_dots", "has_at_symbol", "has_hyphen", "num_hyphens",
            "subdomain_count", "is_ip_url", "num_slashes", "has_query",
            "query_length", "num_query_params", "suspicious_keyword_count",
            "has_suspicious_tld", "has_encoded_chars", "num_special_chars",
            "has_double_slash", "domain_digit_ratio", "is_url_shortener",
            "brand_impersonation_score", "uses_non_standard_port"
        ]}

    return features


def get_feature_list(features: Dict[str, Any]) -> list:
    """Return features as ordered list for ML model input."""
    ordered_keys = [
        "url_length", "hostname_length", "path_length", "has_https",
        "num_dots", "has_at_symbol", "has_hyphen", "num_hyphens",
        "subdomain_count", "is_ip_url", "num_slashes", "has_query",
        "query_length", "num_query_params", "suspicious_keyword_count",
        "has_suspicious_tld", "has_encoded_chars", "num_special_chars",
        "has_double_slash", "domain_digit_ratio", "is_url_shortener",
        "brand_impersonation_score", "uses_non_standard_port"
    ]
    return [features.get(k, 0) for k in ordered_keys]

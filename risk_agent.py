import re

RISK_PATTERNS = {
    "Schedule Delay": [
        "delayed",
        "delay",
        "behind schedule",
        "overdue",
        "missed deadline",
        "postponed",
    ],
    "Dependency Risk": [
        "depends on",
        "dependency",
        "dependencies",
        "waiting for",
        "blocked by",
        "pending approval",
    ],
    "Delivery Challenge": [
        "may not finish",
        "at risk",
        "shortage",
        "insufficient time",
        "resource unavailable",
    ],
}

# Ordinary software setup instructions (ignored unless a risk keyword is present).
SETUP_PHRASES = (
    "must be installed",
    "install the library",
    "installation requirement",
    "pdf extraction library",
    "python-docx",
)

# Compile whole-word/phrase regexes once.
COMPILED_PATTERNS = {
    risk_type: [
        (kw, re.compile(r"\b" + re.escape(kw).replace(r"\ ", r"\s+") + r"\b"))
        for kw in keywords
    ]
    for risk_type, keywords in RISK_PATTERNS.items()
}

BULLET_PREFIX = re.compile(r"^[\-\*\u2022\u2023\u25E6\d\.\)\s]+(?=\S)")


def detect_project_risks(text):
    """Return one risk card per category with unique evidence lines."""
    if not isinstance(text, str) or not text.strip():
        return []

    grouped_risks = {
        risk_type: {"evidence": [], "matched_keywords": []}
        for risk_type in RISK_PATTERNS
    }

    seen_lines = set()

    for line in text.splitlines():
        clean = re.sub(r"\s+", " ", line).strip()
        if not clean:
            continue

        normalized = BULLET_PREFIX.sub("", clean).casefold()

        # Skip identical lines appearing more than once.
        if normalized in seen_lines:
            continue
        seen_lines.add(normalized)

        matches = {}
        for risk_type, patterns in COMPILED_PATTERNS.items():
            found = [kw for kw, rx in patterns if rx.search(normalized)]
            if found:
                matches[risk_type] = found

        if not matches:
            continue

        # Ignore setup instructions only when they carry no genuine risk signal.
        # (Here a risk keyword exists, so keep the line unless it is pure setup text
        # with no schedule/dependency context.)
        is_setup = any(phrase in normalized for phrase in SETUP_PHRASES)
        if is_setup and not _has_real_risk_signal(matches):
            continue

        for risk_type, found in matches.items():
            details = grouped_risks[risk_type]
            details["evidence"].append(clean)
            for kw in found:
                if kw not in details["matched_keywords"]:
                    details["matched_keywords"].append(kw)

    return [
        {
            "risk_type": risk_type,
            "evidence": "\n".join(details["evidence"]),
            "matched_keywords": details["matched_keywords"],
        }
        for risk_type, details in grouped_risks.items()
        if details["evidence"]
    ]


def _has_real_risk_signal(matches):
    """A setup line still counts if it mentions delay or blocking terms."""
    strong = {"delayed", "delay", "overdue", "missed deadline",
              "postponed", "blocked by", "behind schedule"}
    return any(kw in strong for kws in matches.values() for kw in kws)
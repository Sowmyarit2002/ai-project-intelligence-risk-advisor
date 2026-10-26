import re


def detect_project_risks(text):
    risks = []
    lines = text.splitlines()

    risk_patterns = {
        "Schedule Delay": [
            "delayed", "delay", "behind schedule",
            "overdue", "missed deadline", "postponed"
        ],
        "Dependency Risk": [
            "depends on", "dependency", "waiting for",
            "blocked by", "pending approval"
        ],
        "Delivery Challenge": [
            "may not finish", "at risk", "shortage",
            "insufficient time", "resource unavailable"
        ]
    }

    for line in lines:
        clean = line.strip()
        if not clean:
            continue

        lower = clean.lower()

        for risk_type, keywords in risk_patterns.items():
            matched = [word for word in keywords if word in lower]

            if matched:
                risks.append({
                    "risk_type": risk_type,
                    "evidence": clean,
                    "matched_keywords": matched
                })

    return risks
import re

def extract_scope_and_deliverables(text):
    result = {
        "goals": [],
        "deliverables": [],
        "milestones": [],
        "timelines": [],
        "responsibilities": []
    }

    lines = text.splitlines()

    date_pattern = r"\b\d{1,2}\s+[A-Za-z]+\s+\d{4}\b"

    for line in lines:
        clean = line.strip()
        if not clean:
            continue

        lower = clean.lower()

        if any(word in lower for word in ["goal", "objective"]):
            result["goals"].append(clean)

        if any(word in lower for word in ["deliverable", "module", "feature"]):
            result["deliverables"].append(clean)

        if "milestone" in lower:
            result["milestones"].append(clean)

        dates = re.findall(date_pattern, clean)
        if dates:
            result["timelines"].append(clean)

        if any(word in lower for word in ["assigned", "owner", "responsible"]):
            result["responsibilities"].append(clean)

    return result


import re


RECORD_PATTERN = re.compile(
    r"^\s*(?:[-*•]\s*)?"
    r"(?P<record_id>[ABRTD]\d+)\s*[—–-]\s*"
    r"(?P<description>.*)$",
    re.IGNORECASE
)

HEADING_PATTERN = re.compile(
    r"^[A-Z][A-Z\s&/:-]{3,}$"
)


def extract_records(text):
    """Extract ID-based records and their continuation lines."""

    records = []
    current = None

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        match = RECORD_PATTERN.match(line)

        if match:
            if current:
                records.append(current)

            current = {
                "id": match.group("record_id").upper(),
                "description": match.group("description").strip()
            }
            continue

        # Stop collecting when a new section heading appears.
        if HEADING_PATTERN.match(line):
            if current:
                records.append(current)
                current = None
            continue

        # Ignore unrelated text before the first identified record.
        if current:
            current["description"] += " " + line

    if current:
        records.append(current)

    return records


def is_pending_decision(description):
    """Identify explicit unresolved decisions."""

    text = description.lower()

    patterns = [
        r"\bpending decision\b",
        r"\bdecision is needed\b",
        r"\bdecision pending\b",
        r"\bdecide whether\b",
        r"\bdecision on whether\b",
        r"\bwhether .{0,100}\bwill be included\b",
    ]

    return any(
        re.search(pattern, text)
        for pattern in patterns
    )


def identify_blockers_and_actions(text):
    """
    Extract blockers, pending decisions and action items.

    B-series: blockers or unresolved decisions.
    A-series: action items.
    Other record types are excluded.
    """

    result = {
        "blockers": [],
        "pending_decisions": [],
        "action_items": []
    }

    if not isinstance(text, str) or not text.strip():
        return result

    records = extract_records(text)

    for record in records:
        record_id = record["id"]
        description = record["description"]

        if not description:
            continue

        formatted_record = f"{record_id} — {description}"

        if record_id.startswith("B"):
            if is_pending_decision(description):
                result["pending_decisions"].append(
                    formatted_record
                )
            else:
                result["blockers"].append(
                    formatted_record
                )

        elif record_id.startswith("A"):
            result["action_items"].append(
                formatted_record
            )

    # Remove duplicate records while preserving order.
    for category in result:
        result[category] = list(
            dict.fromkeys(result[category])
        )

    return result
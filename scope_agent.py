

import re


# --------------------------------------------------
# RECORD IDENTIFICATION
# --------------------------------------------------

RECORD_PATTERN = re.compile(
    r"^\s*(?:[-*•]\s*)?"
    r"(?P<record_id>[ABMRTD]\d+)\s*[—–-]\s*"
    r"(?P<description>.*)$",
    re.IGNORECASE
)

HEADING_PATTERN = re.compile(
    r"^[A-Z][A-Z\s&/:-]{3,}$"
)

DATE_PATTERN = re.compile(
    r"\b\d{1,2}\s+[A-Za-z]+\s+\d{4}\b"
    r"|\b\d{4}-\d{2}-\d{2}\b"
    r"|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    re.IGNORECASE
)

WEEK_PATTERN = re.compile(
    r"\bweek\s*\d+\b",
    re.IGNORECASE
)


def extract_records(text):
    """Extract numbered project records."""

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

        if HEADING_PATTERN.match(line):

            if current:
                records.append(current)
                current = None

            continue

        if current:
            current["description"] += " " + line

    if current:
        records.append(current)

    return records


def extract_scope_and_deliverables(text):
    """
    Extract goals, deliverables, milestones,
    timelines and responsibilities.
    """

    result = {
        "goals": [],
        "deliverables": [],
        "milestones": [],
        "timelines": [],
        "responsibilities": []
    }

    if not isinstance(text, str) or not text.strip():
        return result

    seen = {
        key: set()
        for key in result
    }

    def add_item(category, value):

        value = value.strip()
        normalized = value.casefold()

        if value and normalized not in seen[category]:
            result[category].append(value)
            seen[category].add(normalized)

    # --------------------------------------------------
    # 1. PROCESS EXPLICITLY NUMBERED RECORDS
    # --------------------------------------------------

    records = extract_records(text)

    for record in records:

        record_id = record["id"]
        description = record["description"]

        if not description:
            continue

        # D-series represents deliverables.
        if record_id.startswith("D"):

            add_item(
                "deliverables",
                f"{record_id} — {description}"
            )

        # M-series represents project milestones.
        elif record_id.startswith("M"):

            add_item(
                "milestones",
                f"{record_id} — {description}"
            )

            if (
                DATE_PATTERN.search(description)
                or WEEK_PATTERN.search(description)
            ):
                add_item(
                    "timelines",
                    f"{record_id} — {description}"
                )

    # --------------------------------------------------
    # 2. PROCESS GENERAL PROJECT TEXT
    # --------------------------------------------------

    for raw_line in text.splitlines():

        clean = raw_line.strip()

        if not clean:
            continue

        # Ignore numbered records already classified.
        if RECORD_PATTERN.match(clean):
            continue

        lower = clean.casefold()

        # Project goals and objectives.
        if re.search(
            r"\b(project goal|project objective|goal:|objective:|"
            r"project aims to|aim of the project)\b",
            lower
        ):
            add_item("goals", clean)

        # Deliverables and modules.
        if re.search(
            r"\b(deliverables?:|main deliverables|"
            r"modules?:|features?:|will develop|will implement)\b",
            lower
        ):
            add_item("deliverables", clean)

        # Milestones.
        if re.search(r"\bmilestones?\b", lower):
            add_item("milestones", clean)

        # Calendar dates and relative week targets.
        if DATE_PATTERN.search(clean) or WEEK_PATTERN.search(clean):

            if re.search(
                r"\b(target|deadline|due|timeline|"
                r"scheduled|milestone|completion|by)\b",
                lower
            ):
                add_item("timelines", clean)

        # Responsibilities.
        if re.search(
            r"\b(assigned to|owner:|responsible for|"
            r"responsibility:|task owner:)\b",
            lower
        ):
            add_item("responsibilities", clean)

    return result


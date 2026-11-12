

import re


# --------------------------------------------------
# RISK DETECTION PATTERNS
# --------------------------------------------------

RISK_PATTERNS = {
    "Schedule Delay": [
        "delayed",
        "delay",
        "behind schedule",
        "overdue",
        "missed deadline",
        "postponed",
        "timeline slippage",
    ],

    "Dependency Risk": [
        "depends on",
        "dependency",
        "dependencies",
        "waiting for",
        "blocked by",
        "pending approval",
        "external dependency",
    ],

    "Delivery Challenge": [
        "may not finish",
        "at risk",
        "shortage",
        "insufficient time",
        "resource unavailable",
        "delivery challenge",
        "delivery risk",
        "may miss",
        "false positive",
        "false positives",
        "miss risks",
        "flag sentences",
        "overstate certainty",
        "incomplete evidence",
        "source evidence is incomplete",
        "unvalidated",
        "not validated",
        "needs further validation",
    ],
}


# --------------------------------------------------
# RECORD IDENTIFICATION
# --------------------------------------------------

RECORD_PATTERN = re.compile(
    r"^\s*(?:[-*•]\s*)?"
    r"(?P<record_id>[ABRTD]\d+)\s*[—–-]\s*"
    r"(?P<description>.*)$",
    re.IGNORECASE
)

HEADING_PATTERN = re.compile(
    r"^[A-Z][A-Z\s&/:-]{3,}$"
)


# --------------------------------------------------
# COMPILE PATTERNS
# --------------------------------------------------

COMPILED_PATTERNS = {
    risk_type: [
        (
            keyword,
            re.compile(
                r"\b" +
                re.escape(keyword).replace(r"\ ", r"\s+") +
                r"\b",
                re.IGNORECASE
            )
        )
        for keyword in keywords
    ]
    for risk_type, keywords in RISK_PATTERNS.items()
}


def extract_risk_records(text):
    """Extract explicitly numbered project records."""

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


def classify_risk(description):
    """Identify risk categories from evidence."""

    normalized = re.sub(
        r"\s+",
        " ",
        description
    ).strip().casefold()

    matches = {}

    for risk_type, patterns in COMPILED_PATTERNS.items():

        found = [
            keyword
            for keyword, regex in patterns
            if regex.search(normalized)
        ]

        if found:
            matches[risk_type] = found

    return matches


def detect_project_risks(text):
    """
    Detect project risks using explicit R-series records
    and keyword-based evidence.

    Ignores B-series, A-series, T-series and D-series records.
    """

    if not isinstance(text, str) or not text.strip():
        return []

    grouped_risks = {
        risk_type: {
            "evidence": [],
            "matched_keywords": []
        }
        for risk_type in RISK_PATTERNS
    }

    seen_evidence = set()

    def add_risk(risk_type, evidence, keywords):

        normalized = re.sub(
            r"\s+",
            " ",
            evidence
        ).strip().casefold()

        if not normalized or normalized in seen_evidence:
            return

        seen_evidence.add(normalized)

        details = grouped_risks[risk_type]

        details["evidence"].append(evidence)

        for keyword in keywords:
            if keyword not in details["matched_keywords"]:
                details["matched_keywords"].append(keyword)

    # --------------------------------------------------
    # 1. PROCESS EXPLICITLY NUMBERED RECORDS
    # --------------------------------------------------

    records = extract_risk_records(text)

    for record in records:

        record_id = record["id"]
        description = record["description"]

        # Only R-series records are accepted as explicit risks.
        if not record_id.startswith("R"):
            continue

        if not description:
            continue

        matches = classify_risk(description)

        if matches:

            for risk_type, keywords in matches.items():

                add_risk(
                    risk_type,
                    f"{record_id} — {description}",
                    keywords
                )

        else:

            # An explicitly documented R-series item is still
            # a risk even if no known keyword matches.
            add_risk(
                "Delivery Challenge",
                f"{record_id} — {description}",
                ["explicit risk record"]
            )

    # --------------------------------------------------
    # 2. PROCESS UNNUMBERED RISK EVIDENCE
    # --------------------------------------------------

    for raw_line in text.splitlines():

        clean = re.sub(
            r"\s+",
            " ",
            raw_line
        ).strip()

        if not clean:
            continue

        # Ignore all numbered records here.
        if RECORD_PATTERN.match(clean):
            continue

        matches = classify_risk(clean)

        for risk_type, keywords in matches.items():

            add_risk(
                risk_type,
                clean,
                keywords
            )

    # --------------------------------------------------
    # 3. RETURN RESULTS IN THE EXISTING FORMAT
    # --------------------------------------------------

    return [
        {
            "risk_type": risk_type,
            "evidence": "\n".join(details["evidence"]),
            "matched_keywords": details["matched_keywords"],
        }
        for risk_type, details in grouped_risks.items()
        if details["evidence"]
    ]
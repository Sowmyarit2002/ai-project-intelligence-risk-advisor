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

# Lines such as "--- Update added 2026-11-24 10:15 (notes.txt) ---" are
# added by the incremental-upload feature. They end the previous record so
# the update text is not glued onto the last record of the original file.
UPDATE_MARKER_PATTERN = re.compile(
    r"^-{3,}\s*update added",
    re.IGNORECASE
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


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def _normalize(text):
    return re.sub(r"\s+", " ", str(text)).strip().casefold()


def _scan_records(text):
    """
    Extract explicitly numbered project records.

    Returns (records, consumed) where consumed is the set of line
    numbers that belong to a numbered record (its first line and any
    continuation lines), so they are not analysed a second time as
    free text.
    """

    records = []
    consumed = set()
    current = None

    for line_number, raw_line in enumerate(text.splitlines()):

        line = raw_line.strip()

        if not line:
            continue

        if UPDATE_MARKER_PATTERN.match(line):

            if current:
                records.append(current)
                current = None

            consumed.add(line_number)
            continue

        match = RECORD_PATTERN.match(line)

        if match:

            if current:
                records.append(current)

            current = {
                "id": match.group("record_id").upper(),
                "description": match.group("description").strip()
            }

            consumed.add(line_number)
            continue

        if HEADING_PATTERN.match(line):

            if current:
                records.append(current)
                current = None

            continue

        if current:
            current["description"] += " " + line
            consumed.add(line_number)

    if current:
        records.append(current)

    return records, consumed


def extract_risk_records(text):
    """Extract explicitly numbered project records."""

    return _scan_records(text)[0]


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


def _primary_risk_type(matches):
    """Category with the most matched keywords (ties: pattern order)."""

    order = list(RISK_PATTERNS)

    return max(
        matches,
        key=lambda risk_type: (len(matches[risk_type]), -order.index(risk_type))
    )


def _build_record(risk_id, evidence, matches, source):
    """One structured record for one distinct risk."""

    keywords = []

    for risk_type in RISK_PATTERNS:
        for keyword in matches.get(risk_type, []):
            if keyword not in keywords:
                keywords.append(keyword)

    return {
        "risk_id": risk_id,
        "risk_type": _primary_risk_type(matches),
        "risk_types": [t for t in RISK_PATTERNS if t in matches],
        "evidence": evidence,
        "matched_keywords": keywords,
        "source": source,
    }


# --------------------------------------------------
# RISK DETECTION
# --------------------------------------------------

def detect_project_risks(text):
    """
    Detect project risks and return ONE record per distinct risk.

    Each record has:
        risk_id           unique ID (R1, R2... for numbered risk records,
                          U1, U2... for risks found in free text)
        risk_type         main category
        risk_types        every category the risk matched
        evidence          the single statement the risk comes from
        matched_keywords  keywords found in that statement
        source            "numbered record" or "free text"

    A risk that matches several categories is still ONE record, so it
    is never counted twice. Only R-series records are accepted as
    explicit risks; A, B, T and D records are ignored.
    """

    if not isinstance(text, str) or not text.strip():
        return []

    risks = []
    seen_evidence = set()
    used_ids = {}

    def unique_id(base_id):
        used_ids[base_id] = used_ids.get(base_id, 0) + 1
        count = used_ids[base_id]
        return base_id if count == 1 else f"{base_id}.{count}"

    # --------------------------------------------------
    # 1. EXPLICITLY NUMBERED R-SERIES RECORDS
    # --------------------------------------------------

    records, consumed = _scan_records(text)

    for record in records:

        record_id = record["id"]
        description = record["description"]

        if not record_id.startswith("R") or not description:
            continue

        evidence = f"{record_id} — {description}"
        normalized = _normalize(evidence)

        if normalized in seen_evidence:
            continue

        seen_evidence.add(normalized)

        matches = classify_risk(description)

        if not matches:
            # An explicitly documented R-series item is still a risk
            # even if no known keyword matches.
            matches = {"Delivery Challenge": ["explicit risk record"]}

        risks.append(
            _build_record(
                unique_id(record_id),
                evidence,
                matches,
                "numbered record"
            )
        )

    # --------------------------------------------------
    # 2. UNNUMBERED RISK EVIDENCE (FREE TEXT)
    # --------------------------------------------------

    free_text_count = 0

    for line_number, raw_line in enumerate(text.splitlines()):

        # Lines that belong to a numbered record were handled above.
        if line_number in consumed:
            continue

        clean = re.sub(r"\s+", " ", raw_line).strip()

        if not clean or RECORD_PATTERN.match(clean):
            continue

        matches = classify_risk(clean)

        if not matches:
            continue

        normalized = _normalize(clean)

        if normalized in seen_evidence:
            continue

        seen_evidence.add(normalized)
        free_text_count += 1

        risks.append(
            _build_record(
                f"U{free_text_count}",
                clean,
                matches,
                "free text"
            )
        )

    return risks

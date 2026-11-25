import re


# --------------------------------------------------
# RISK DETECTION PATTERNS
# --------------------------------------------------
#
# These keywords describe PROJECT DELIVERY risks. Statements about the
# analysis tool itself (false positives, "may miss risks", "unvalidated",
# "incomplete evidence" ...) are not delivery risks and are no longer
# detected from free text. An explicitly numbered R-series record is still
# reported as a risk whatever it says (see detect_project_risks).

RISK_PATTERNS = {
    "Schedule Delay": [
        "delayed",
        "delay",
        "delays",
        "delaying",
        "behind schedule",
        "overdue",
        "missed deadline",
        "missed the deadline",
        "postponed",
        "timeline slippage",
        "schedule slippage",
        "running late",
    ],

    "Dependency Risk": [
        "depends on",
        "dependent on",
        "dependency",
        "dependencies",
        "waiting for",
        "waiting on",
        "blocked by",
        "pending approval",
        "approval pending",
        "external dependency",
    ],

    "Delivery Challenge": [
        "may not finish",
        "at risk",
        "shortage",
        "insufficient time",
        "resource unavailable",
        "resource constraints",
        "understaffed",
        "delivery challenge",
        "delivery risk",
        "cannot deliver",
        "unable to deliver",
        "budget overrun",
        "scope creep",
    ],
}

# Phrases that need surrounding context to be a delivery risk. Each entry
# is (label shown in matched_keywords, regular expression).
CONTEXT_PATTERNS = {
    "Schedule Delay": [],

    "Dependency Risk": [
        (
            "awaiting approval/response",
            r"awaiting\s+(?:[\w-]+\s+){0,2}?(?:approval|response|delivery|"
            r"confirmation|sign-?off|input|decision|access|clearance)"
        ),
    ],

    "Delivery Challenge": [
        (
            "may miss deadline",
            r"may\s+miss\s+(?:the\s+|a\s+|its\s+|our\s+|this\s+)?(?:[\w-]+\s+)?"
            r"(?:deadline|milestone|release|launch|target|date|go-?live|delivery)"
        ),
        (
            "unvalidated assumptions/requirements",
            r"(?:unvalidated|not\s+validated)\s+"
            r"(?:project\s+)?(?:assumptions?|requirements?|estimates?)"
        ),
        (
            "assumptions/requirements not validated",
            r"(?:assumptions?|requirements?|estimates?)\s+"
            r"(?:are\s+|is\s+|remain\s+)?(?:still\s+)?(?:unvalidated|not\s+validated)"
        ),
    ],
}

# A keyword that is too general to count as strong evidence on its own.
GENERIC_KEYWORDS = {
    "delay", "delayed", "delays", "delaying",
    "dependency", "dependencies",
    "shortage", "at risk",
}

# Software-engineering uses of the same words are not project dependencies.
EXCLUSION_PATTERNS = {
    "Dependency Risk": [
        r"\bdependency\s+(?:injection|management|manager|graph|tree|file|"
        r"resolution|version|conflict)\b",
        r"\b(?:software|package|library|libraries|python|npm|pip|maven|code|"
        r"build)\s+dependenc(?:y|ies)\b",
        r"\bdependencies\s+(?:are\s+)?(?:installed|listed\s+in)\b",
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

UPDATE_MARKER_SOURCE = re.compile(
    r"^-{3,}\s*update added\s*(?P<stamp>[\d\-: ]*?)\s*"
    r"(?:\((?P<file>.*)\))?\s*-*\s*$",
    re.IGNORECASE
)

SEPARATOR_PATTERN = re.compile(r"^[-=_*~#]{3,}$")

BULLET_PATTERN = re.compile(r"^\s*(?:[-*•▪◦]|\d{1,2}[.)])\s+")

_HEADING_SMALL_WORDS = {
    "a", "an", "and", "or", "the", "of", "to", "in", "on", "for", "with",
    "by", "at", "from", "vs", "&", "per", "as",
}


# --------------------------------------------------
# COMPILE PATTERNS
# --------------------------------------------------

def _keyword_regex(keyword):
    return re.compile(
        r"\b" + re.escape(keyword).replace(r"\ ", r"\s+") + r"\b",
        re.IGNORECASE
    )


COMPILED_PATTERNS = {
    risk_type: (
        [(keyword, _keyword_regex(keyword)) for keyword in keywords]
        + [
            (label, re.compile(r"\b" + expression + r"\b", re.IGNORECASE))
            for label, expression in CONTEXT_PATTERNS.get(risk_type, [])
        ]
    )
    for risk_type, keywords in RISK_PATTERNS.items()
}

COMPILED_EXCLUSIONS = {
    risk_type: [re.compile(expression, re.IGNORECASE) for expression in expressions]
    for risk_type, expressions in EXCLUSION_PATTERNS.items()
}

# "no delays", "not delayed", "to avoid delays", "delays are not expected"
_NEGATION_BEFORE = re.compile(
    r"\b(?:no|not|never|without|zero|nor|neither|hardly|unlikely|nothing"
    r"|avoid(?:ing|s)?|prevent(?:ing|s)?|eliminat(?:e|es|ing)|free\s+of)\b"
    r"(?:\s+(?!but\b|however\b|although\b|though\b|yet\b|except\b)[\w'-]+){0,3}"
    r"\s*$"
)

_NEGATION_AFTER = re.compile(
    r"^\W*(?:[\w'-]+\s+){0,2}?"
    r"(?:(?:is|are|was|were|will\s+be|has|have|had|does|do|did)\s+(?:not|never)"
    r"|unlikely|none|nil|ruled\s+out|not\s+expected|not\s+an?\s+issue)\b"
)

# Likelihood / impact stated in the document, e.g. "Likelihood: High".
LEVEL_FIELD_PATTERN = re.compile(
    r"\b(?P<field>likelihood|probability|impact|severity)\s*"
    r"(?:level|rating|score)?\s*[:=\-–—]\s*"
    r"(?P<value>very\s+low|very\s+high|low|medium|moderate|high|critical|"
    r"severe|[1-5](?:\s*/\s*5)?)(?!\w|\.\d)",
    re.IGNORECASE
)

# Same 1-5 scale that health_score.py uses (kept here to avoid a circular
# import).
LEVEL_WORDS = {
    "very low": 1, "low": 2, "medium": 3, "moderate": 3,
    "high": 4, "very high": 5, "critical": 5, "severe": 5,
}

# Mitigation status, only when the evidence states it.
_STATUS_OPEN = re.compile(
    r"\b(?:unresolved|still\s+open|remains?\s+open|"
    r"not\s+(?:yet\s+)?(?:resolved|mitigated|fixed|closed)|"
    r"status\s*[:=\-]\s*open)\b",
    re.IGNORECASE
)
_STATUS_IN_PROGRESS = re.compile(
    r"\b(?:in[\s-]progress|being\s+(?:addressed|mitigated|resolved|worked)|"
    r"mitigation\s+underway|underway)\b",
    re.IGNORECASE
)
_STATUS_RESOLVED = re.compile(
    r"(?:\b(?:has|have|had|was|were|is|are|now|been)\s+(?:been\s+|now\s+|fully\s+)?"
    r"(?:resolved|mitigated|closed|fixed|cleared)\b"
    r"|\((?:resolved|mitigated|closed)\)"
    r"|\bstatus\s*[:=\-]\s*(?:resolved|mitigated|closed))",
    re.IGNORECASE
)

# Common abbreviations that must not end a sentence.
_ABBREVIATIONS = (
    "e.g.", "i.e.", "etc.", "vs.", "approx.", "no.", "mr.", "mrs.", "ms.",
    "dr.", "inc.", "ltd.", "st.", "fig.", "est.",
)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def _normalize(text):
    return re.sub(r"\s+", " ", str(text)).strip().casefold()


def _prepare(text):
    """Lower-cased, single-spaced text with n't expanded to ' not'."""

    text = str(text).replace("’", "'")
    text = re.sub(r"n't\b", " not", text)
    return re.sub(r"\s+", " ", text).strip().casefold()


def _is_heading(line):
    """
    True for section headings (so they are never used as evidence):
    ALL-CAPS lines, markdown '#' headings, short Title Case lines and short
    lines ending in a colon. "Label: value" lines are NOT headings.
    """

    line = line.strip()

    if not line:
        return False

    if HEADING_PATTERN.match(line):
        return True

    if line.startswith("#"):
        return True

    # Ignore a leading section number such as "2." or "3.1)"
    stripped = re.sub(r"^\d+(?:\.\d+)*[.)]?\s+", "", line)
    words = stripped.split()

    if not words or len(words) > 10:
        return False

    if stripped.endswith(":") and ":" not in stripped[:-1]:
        return True

    # Colons ("Label: value"), commas (CSV rows) and sentence punctuation
    # mean this is content, not a heading.
    if ":" in stripped or "," in stripped or stripped[-1] in ".!?;":
        return False

    if len(words) > 8:
        return False

    significant = [
        word for word in words
        if word.casefold() not in _HEADING_SMALL_WORDS
    ]

    return bool(significant) and all(
        word[0].isupper() or not word[0].isalpha() for word in significant
    )


def _is_bullet(line):
    return bool(BULLET_PATTERN.match(line))


def _marker_source(line):
    """File name (or a label) from an incremental-update marker line."""

    match = UPDATE_MARKER_SOURCE.match(line.strip())

    if match and match.group("file"):
        return match.group("file").strip()

    stamp = match.group("stamp").strip() if match else ""
    return f"update {stamp}".strip()


def _source_label(source_document):
    return source_document or "original document"


def _continues(previous_line, raw_line, line):
    """
    Does 'line' continue the unnumbered paragraph that ended with
    'previous_line'? Hard-wrapped text continues in lower case, after a
    comma / dash / conjunction, or with an indent.
    """

    previous = previous_line.rstrip()

    if not previous:
        return False

    if raw_line[:1] in (" ", "\t") and previous[-1] not in ".!?":
        return True

    if line[:1].islower() or line[:1] in ")],":
        return True

    if previous[-1] in ",-–—(":
        return True

    return bool(re.search(
        r"\b(?:and|or|of|to|the|with|for|by|on|in|a|an)$",
        previous,
        re.IGNORECASE
    ))


def _split_sentences(paragraph):
    """Split a paragraph into sentences without breaking on abbreviations."""

    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])", paragraph.strip())
    sentences = []

    for part in parts:

        if (
            sentences
            and sentences[-1].casefold().endswith(_ABBREVIATIONS)
        ):
            sentences[-1] += " " + part
        else:
            sentences.append(part)

    return [sentence.strip() for sentence in sentences if sentence.strip()]


def _is_negated(prepared, start, end):
    """Is the keyword at prepared[start:end] negated or ruled out?"""

    before = prepared[max(0, start - 80):start]
    before = re.split(r"[.;:!?()\[\]]", before)[-1]

    if _NEGATION_BEFORE.search(before):
        return True

    after = re.split(r"[.;!?]", prepared[end:end + 60])[0]
    return bool(_NEGATION_AFTER.search(after))


def _extract_levels(evidence):
    """
    Likelihood / impact (1-5) ONLY when the evidence states them
    ("Likelihood: High", "Impact: 4/5"). Otherwise None. Never estimated.
    """

    levels = {"likelihood": None, "impact": None}

    for match in LEVEL_FIELD_PATTERN.finditer(str(evidence)):

        field = (
            "likelihood"
            if match.group("field").casefold() in ("likelihood", "probability")
            else "impact"
        )

        if levels[field] is not None:
            continue

        value = re.sub(r"\s+", " ", match.group("value").casefold())
        levels[field] = (
            int(value[0]) if value[0].isdigit() else LEVEL_WORDS.get(value)
        )

    return levels


def _extract_status(evidence):
    """
    'open', 'in progress' or 'mitigated' only if the evidence states it,
    otherwise None. Unresolved wording wins over resolved wording.
    """

    evidence = _prepare(evidence)

    if _STATUS_OPEN.search(evidence):
        return "open"

    if _STATUS_IN_PROGRESS.search(evidence):
        return "in progress"

    if _STATUS_RESOLVED.search(evidence):
        return "mitigated"

    return None


def _empty_input(text):
    return not isinstance(text, str) or not text.strip()


# --------------------------------------------------
# RECORD SCANNING
# --------------------------------------------------

def _scan_records(text):
    """
    Extract explicitly numbered project records.

    Returns (records, consumed) where consumed is the set of line
    numbers that belong to a numbered record (its first line and any
    continuation lines), so they are not analysed a second time as
    free text.

    A record ends at a blank line, a heading, a separator line, a bullet
    that is not indented, another numbered record, or an update marker.
    Each record also carries 'line' (1-based line of its first line) and
    'source_document' (file named by the preceding update marker, or None
    for the original document).
    """

    records = []
    consumed = set()
    current = None
    source_document = None

    if not isinstance(text, str):
        return records, consumed

    for line_number, raw_line in enumerate(text.splitlines()):

        line = raw_line.strip()

        if not line:

            # A blank line is a paragraph break: it ends the record.
            if current:
                records.append(current)
                current = None

            continue

        if UPDATE_MARKER_PATTERN.match(line):

            if current:
                records.append(current)
                current = None

            consumed.add(line_number)
            source_document = _marker_source(line)
            continue

        match = RECORD_PATTERN.match(line)

        if match:

            if current:
                records.append(current)

            current = {
                "id": match.group("record_id").upper(),
                "description": match.group("description").strip(),
                "line": line_number + 1,
                "source_document": source_document,
            }

            consumed.add(line_number)
            continue

        if (
            _is_heading(line)
            or SEPARATOR_PATTERN.match(line)
            or (_is_bullet(line) and raw_line[:1] not in (" ", "\t"))
        ):

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


def _free_text_blocks(text, consumed):
    """
    Paragraphs of text that are not part of a numbered record.

    Returns a list of (paragraph, first_line_number, source_document).
    Headings, separators, blank lines, bullets and update markers start a
    new block, so unrelated lines are never merged.
    """

    blocks = []
    current = None
    source_document = None

    def close():
        nonlocal current

        if current:
            blocks.append((
                " ".join(current["lines"]),
                current["line"],
                current["source_document"],
            ))

        current = None

    for line_number, raw_line in enumerate(text.splitlines()):

        line = raw_line.strip()

        if not line:
            close()
            continue

        if UPDATE_MARKER_PATTERN.match(line):
            close()
            source_document = _marker_source(line)
            continue

        if (
            line_number in consumed
            or RECORD_PATTERN.match(line)
            or _is_heading(line)
            or SEPARATOR_PATTERN.match(line)
        ):
            close()
            continue

        bullet = _is_bullet(line)
        content = BULLET_PATTERN.sub("", line) if bullet else line

        if (
            current
            and not bullet
            and _continues(current["lines"][-1], raw_line, content)
        ):
            current["lines"].append(content)
            continue

        close()
        current = {
            "lines": [content],
            "line": line_number + 1,
            "source_document": source_document,
        }

    close()

    return blocks


def extract_risk_records(text):
    """Extract explicitly numbered project records."""

    return _scan_records(text)[0]


# --------------------------------------------------
# CLASSIFICATION
# --------------------------------------------------

def classify_risk(description):
    """
    Identify risk categories from evidence.

    A keyword counts only when it is not negated ("no delays", "not
    delayed", "to avoid delays") and is not a non-project use of the word
    (for example "dependency injection"). Returns {risk_type: [keywords]}.
    """

    if not isinstance(description, str):
        return {}

    prepared = _prepare(description)

    if not prepared:
        return {}

    matches = {}

    for risk_type, patterns in COMPILED_PATTERNS.items():

        excluded = [
            match.span()
            for regex in COMPILED_EXCLUSIONS.get(risk_type, [])
            for match in regex.finditer(prepared)
        ]

        found = []

        for keyword, regex in patterns:

            for match in regex.finditer(prepared):

                if any(
                    start <= match.start() and match.end() <= end
                    for start, end in excluded
                ):
                    continue

                if _is_negated(prepared, match.start(), match.end()):
                    continue

                found.append(keyword)
                break

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


def _build_record(
    risk_id,
    evidence,
    matches,
    source,
    source_document=None,
    source_line=None,
    explicit_fallback=False
):
    """
    One structured record for one distinct risk.

    likelihood / impact / mitigation_status are taken from the evidence only
    when it states them, otherwise None (health_score.py then applies its
    own flagged estimates). 'confidence' is how sure the detector is that
    the text is a project risk; 'assessment_basis' explains where each value
    comes from. Nothing here is estimated.
    """

    keywords = []

    for risk_type in RISK_PATTERNS:
        for keyword in matches.get(risk_type, []):
            if keyword not in keywords:
                keywords.append(keyword)

    levels = _extract_levels(evidence)
    status = _extract_status(evidence)

    if source == "numbered record":
        confidence = "high"
    elif any(keyword not in GENERIC_KEYWORDS for keyword in keywords):
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "risk_id": risk_id,
        "risk_type": _primary_risk_type(matches),
        "risk_types": [t for t in RISK_PATTERNS if t in matches],
        "evidence": evidence,
        "matched_keywords": keywords,
        "source": source,
        "source_document": source_document,
        "source_line": source_line,
        "likelihood": levels["likelihood"],
        "impact": levels["impact"],
        "mitigation_status": status,
        "confidence": confidence,
        "assessment_basis": {
            "category": (
                "explicit record, no delivery keyword matched"
                if explicit_fallback else "keyword match"
            ),
            "likelihood": "stated in document" if levels["likelihood"] else None,
            "impact": "stated in document" if levels["impact"] else None,
            "mitigation_status": "stated in document" if status else None,
        },
        "also_found_in": [],
    }


# --------------------------------------------------
# RISK DETECTION
# --------------------------------------------------

def detect_project_risks(text):
    """
    Detect project risks and return ONE record per distinct risk.

    Each record has:
        risk_id           unique ID (R1, R2... for numbered risk records,
                          R1.2 ... when an ID is repeated with different
                          text, U1, U2... for risks found in free text)
        risk_type         main category
        risk_types        every category the risk matched
        evidence          the statement the risk comes from
        matched_keywords  keywords found in that statement
        source            "numbered record" or "free text"
        source_document   file named by the incremental-update marker the
                          risk sits under, None for the original document
        source_line       1-based line number in the stored text
        likelihood        1-5 if the evidence states it, else None
        impact            1-5 if the evidence states it, else None
        mitigation_status "open" / "in progress" / "mitigated" if stated,
                          else None
        confidence        "high" (numbered record), "medium" (specific
                          keyword) or "low" (only a generic keyword)
        assessment_basis  where each value above comes from
        also_found_in     other documents that contain the same evidence

    A risk that matches several categories is still ONE record, so it
    is never counted twice. Only R-series records are accepted as
    explicit risks; A, B, T and D records are ignored. Invalid or empty
    input returns an empty list.
    """

    if _empty_input(text):
        return []

    risks = []
    seen = {}
    used_ids = {}

    def unique_id(base_id):
        used_ids[base_id] = used_ids.get(base_id, 0) + 1
        count = used_ids[base_id]
        return base_id if count == 1 else f"{base_id}.{count}"

    def note_duplicate(normalized, source_document):
        existing = seen[normalized]
        label = _source_label(source_document)

        if (
            source_document != existing["source_document"]
            and label not in existing["also_found_in"]
        ):
            existing["also_found_in"].append(label)

    # --------------------------------------------------
    # 1. EXPLICITLY NUMBERED R-SERIES RECORDS
    # --------------------------------------------------

    records, consumed = _scan_records(text)

    # Text of every numbered record (including A, B, T, D) so the same
    # sentence repeated elsewhere is not reported again as free text.
    numbered_texts = {_normalize(record["description"]) for record in records}

    for record in records:

        record_id = record["id"]
        description = record["description"]

        if not record_id.startswith("R") or not description:
            continue

        evidence = f"{record_id} — {description}"
        normalized = _normalize(evidence)

        if normalized in seen:
            note_duplicate(normalized, record["source_document"])
            continue

        matches = classify_risk(description)
        explicit_fallback = not matches

        if explicit_fallback:
            # An explicitly documented R-series item is still a risk
            # even if no known keyword matches.
            matches = {"Delivery Challenge": ["explicit risk record"]}

        risk = _build_record(
            unique_id(record_id),
            evidence,
            matches,
            "numbered record",
            source_document=record["source_document"],
            source_line=record["line"],
            explicit_fallback=explicit_fallback,
        )

        seen[normalized] = risk
        risks.append(risk)

    # --------------------------------------------------
    # 2. UNNUMBERED RISK EVIDENCE (FREE TEXT)
    # --------------------------------------------------

    free_text_count = 0

    for paragraph, first_line, source_document in _free_text_blocks(text, consumed):

        for sentence in _split_sentences(paragraph):

            clean = re.sub(r"\s+", " ", sentence).strip()

            if not clean or _is_heading(clean):
                continue

            matches = classify_risk(clean)

            if not matches:
                continue

            normalized = _normalize(clean)

            if normalized in numbered_texts:
                continue

            if normalized in seen:
                note_duplicate(normalized, source_document)
                continue

            free_text_count += 1

            risk = _build_record(
                f"U{free_text_count}",
                clean,
                matches,
                "free text",
                source_document=source_document,
                source_line=first_line,
            )

            seen[normalized] = risk
            risks.append(risk)

    return risks

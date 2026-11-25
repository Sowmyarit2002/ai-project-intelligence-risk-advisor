import json
import math
import os
import re

from scope_agent import extract_scope_and_deliverables
from risk_agent import detect_project_risks
from blocker_agent import (
    identify_blockers_and_actions,
    assess_quality,
    item_weight,
    score_from_penalty,
    DECISION_WEIGHT,
)


# --------------------------------------------------
# CONSTANTS
# --------------------------------------------------

# Value shown for a dimension that has no supporting evidence. It is NOT
# used in the overall score (unassessed dimensions are excluded), it only
# keeps every legacy score key numeric (0-100) for the UI.
NEUTRAL_SCORE = 50

DIMENSIONS = ("schedule", "scope", "risk", "quality", "blocker")

# Fewer assessed dimensions than this => status "Insufficient Data"
MIN_ASSESSED_DIMENSIONS = 3

# Blocker handling. Each blocker has a severity weight (see
# blocker_agent.item_weight: critical 14, high 9, normal 6, reduced when it
# already has an owner / plan / due date). That weight is multiplied by the
# status factor below, summed, and turned into a 0-100 score with diminishing
# returns (blocker_agent.score_from_penalty). Action items that cover the open
# items earn extra credit. This replaces the old flat "20 points per blocker",
# which dropped to ~0 after only five blockers.
BLOCKER_STATUS_FACTORS = {
    "open": 1.0,
    "in_progress": 0.5,
    "resolved": 0.0,
}

# Risk handling
RISK_MAX_PENALTY = 25          # one open risk with L=5, I=5 removes 25 points
RISK_STATUS_FACTORS = {
    "open": 1.0,
    "in_progress": 0.5,
    "mitigated": 0.1,
}
DEFAULT_LIKELIHOOD = 3         # used only when a risk has no valid likelihood
DEFAULT_IMPACT = 3             # used only when a risk has no valid impact

# Typical (likelihood, impact) for known risk types when the detector gives
# none. Unknown risk types use DEFAULT_LIKELIHOOD / DEFAULT_IMPACT. All of
# these are flagged as "estimated" wherever they are used.
RISK_TYPE_DEFAULTS = {
    "Schedule Delay": (3, 4),
    "Dependency Risk": (3, 3),
}

# Timeline penalties per active risk (before the status factor is applied)
TIMELINE_PENALTIES = {
    "Schedule Delay": 30,
    "Dependency Risk": 15,
}

LEVEL_WORDS = {
    "very low": 1, "low": 2, "medium": 3, "moderate": 3,
    "high": 4, "very high": 5, "critical": 5, "severe": 5,
}

# Quality evidence
SUPPORTED_FORMATS = ("pdf", "docx", "csv", "txt")
QUALITY_EVIDENCE_CATEGORIES = (
    "unit_tests",
    "supported_formats",
    "extraction_validation",
    "retrieval_accuracy",
    "source_attribution",
    "document_quality_evidence",
    "document_text_check",
)

VALIDATION_RESULTS_ENV = "PROJECT_VALIDATION_RESULTS"
DEFAULT_VALIDATION_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "validation_results.json"
)

SCOPE_KEYS = ("goals", "deliverables", "milestones", "timelines", "responsibilities")
BLOCKER_KEYS = ("blockers", "pending_decisions", "action_items")


# --------------------------------------------------
# SMALL HELPERS
# --------------------------------------------------

def _clamp_score(value):
    """Round to an int and keep it inside 0-100 (non-finite becomes 0)."""

    if not isinstance(value, (int, float)) or not math.isfinite(value):
        return 0

    return max(0, min(100, int(round(value))))


def _is_number(value):
    """True for real, finite numbers. Booleans are NOT numbers here."""

    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _is_count(value):
    """True for non-negative integers. Booleans are rejected."""

    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _item_text(item):
    """Text of a blocker / decision (strings, or dicts with a text field)."""

    if item is None:
        return ""

    if isinstance(item, dict):
        for key in ("text", "description", "blocker", "decision", "content"):
            if item.get(key):
                return str(item[key])
        return ""

    return str(item)


def _text_key(text):
    """Normalised text used to recognise duplicates."""

    cleaned = re.sub(r"^[\s\-\*•\d.)]+", "", str(text or ""))
    cleaned = re.sub(r"[^\w\s]", " ", cleaned.casefold())
    return " ".join(cleaned.split())


def _clean_items(value):
    """
    A list of non-empty items (strings or dicts) from an agent field.
    A lone string is accepted as one item; other types give an empty list.
    """

    if isinstance(value, str):
        value = [value]

    if not isinstance(value, (list, tuple)):
        return []

    return [
        item for item in value
        if isinstance(item, (str, dict)) and _item_text(item).strip()
    ]


# --------------------------------------------------
# STATUS WORDING (shared by blockers, decisions and risks)
# --------------------------------------------------

_RESOLVE_WORDS = (
    r"resolved|fixed|completed|done|cleared|closed|addressed|unblocked"
    r"|mitigated|removed|approved|decided|finali[sz]ed|confirmed|signed[\s-]off"
)

_PARTIAL = re.compile(
    r"\b(partially|partly|mostly)\s+(resolved|complete\w*|fixed|addressed|done)\b",
    re.IGNORECASE,
)

_UNRESOLVED = re.compile(
    r"\b(unresolved|unfixed|unaddressed|outstanding|incomplete|undecided"
    r"|unapproved|unconfirmed|tbd|to\s+be\s+(decided|confirmed|determined|approved)"
    r"|still\s+(open|pending|unresolved|waiting)"
    r"|awaiting|waiting\s+(for|on)|pending"
    r"|yet\s+to\s+(be\s+)?\w+"
    r"|(not|never|no)\s+(\w+\s+){0,2}?(" + _RESOLVE_WORDS + r")"
    r"|open)\b",
    re.IGNORECASE,
)

_IN_PROGRESS = re.compile(
    r"\b(in[\s-]progress|ongoing|underway"
    r"|being\s+(addressed|worked|resolved|investigated|fixed|handled)"
    r"|working\s+on|under\s+(investigation|way))\b",
    re.IGNORECASE,
)

# Broad resolution wording, used for blockers and for risk status fields.
_RESOLVED = re.compile(
    r"\b(resolved|closed|fixed|completed|cleared|unblocked|removed|mitigated"
    r"|done|no\s+longer\s+(a\s+)?(blocker|blocked|an?\s+issue))\b",
    re.IGNORECASE,
)

# Strict resolution wording for DECISIONS: "approved" / "decided" alone is
# not enough ("approved vendor list"); the wording must say it happened.
_DECISION_RESOLVED = re.compile(
    r"\b((was|were|been|is|are|now|already)\s+(now\s+|already\s+|formally\s+|finally\s+)?"
    r"(resolved|decided|approved|finali[sz]ed|confirmed|closed|signed[\s-]off)"
    r"|(decided|approved|confirmed|finali[sz]ed)\s+(on|by)"
    r"|(decision|approval|sign[\s-]off)\s+(was\s+|has\s+been\s+)?"
    r"(made|received|granted|obtained|given|completed))\b",
    re.IGNORECASE,
)

_DECISION_LEAD_RESOLVED = re.compile(
    r"^\W*(resolved|decided|approved|closed|done)\W*[:\-–—]",
    re.IGNORECASE,
)

_OPEN_WORDS = re.compile(
    r"\b(open|new|identified|active|raised|not\s+started)\b", re.IGNORECASE
)


def _prepare_status_text(text):
    """Normalise apostrophes and expand n't so negations are matched."""

    text = str(text or "").replace("’", "'")
    return re.sub(r"n't\b", " not", text)


def _status_from_text(text, decision=False):
    """
    'open', 'in_progress', 'resolved', or None when the text has no status
    wording at all.

    Priority: partial progress, then unresolved wording, then in-progress,
    then resolved. Unresolved wording therefore always beats resolved wording.
    """

    text = _prepare_status_text(text)

    if not text.strip():
        return None

    if _PARTIAL.search(text):
        return "in_progress"

    if _UNRESOLVED.search(text):
        return "open"

    if _IN_PROGRESS.search(text):
        return "in_progress"

    if decision:
        if _DECISION_LEAD_RESOLVED.search(text) or _DECISION_RESOLVED.search(text):
            return "resolved"
        return None

    if _RESOLVED.search(text) or _DECISION_RESOLVED.search(text):
        return "resolved"

    return None


# --------------------------------------------------
# 1. SCOPE CLARITY SCORE
# --------------------------------------------------

def calculate_scope_score(scope):
    """Calculate scope clarity score out of 100."""

    scope = scope if isinstance(scope, dict) else {}

    score = 0

    if scope.get("goals"):
        score += 40

    if scope.get("deliverables"):
        score += 40

    if scope.get("milestones"):
        score += 20

    return score


# --------------------------------------------------
# 2. TIMELINE HEALTH SCORE  (risk-status aware)
# --------------------------------------------------

def calculate_timeline_score(risks):
    """
    Timeline health from schedule-related risks (0-100).

    Penalty per risk = base penalty (Schedule Delay 30, Dependency Risk 15)
    x status factor (open 1.0, in progress 0.5, mitigated 0.1; same factors
    as the risk score). A risk without status information is treated as
    open. Duplicate findings are counted once. No dates or delivery
    forecasts are derived.

    Returns None if 'risks' is not a list (assessment unavailable).
    """

    if not isinstance(risks, (list, tuple)):
        return None

    penalty = 0.0

    for record in normalize_risk_records(risks):
        base = TIMELINE_PENALTIES.get(record.get("risk_type", ""), 0)

        if base:
            status, _ = _normalize_mitigation(record)
            penalty += base * RISK_STATUS_FACTORS[status]

    return _clamp_score(100 - penalty)


def has_schedule_evidence(scope, risks):
    """
    A schedule score is only meaningful if the document says something
    about the schedule: timelines / milestones, or a schedule-related risk.
    """

    scope = scope if isinstance(scope, dict) else {}

    if scope.get("timelines") or scope.get("milestones"):
        return True

    return any(
        isinstance(risk, dict)
        and risk.get("risk_type") in TIMELINE_PENALTIES
        for risk in (risks if isinstance(risks, (list, tuple)) else [])
    )


# --------------------------------------------------
# 3. BLOCKER MANAGEMENT SCORE  (status + severity aware)
# --------------------------------------------------

def classify_item_status(item):
    """
    Return 'open', 'in_progress' or 'resolved' for a blocker.

    An explicit, recognisable 'status' field wins. Otherwise the wording of
    the text is used; unresolved wording beats resolved wording. Anything
    without status wording is treated as open.
    """

    if isinstance(item, dict):
        from_field = _status_from_text(item.get("status", ""))

        if from_field:
            return from_field

    return _status_from_text(_item_text(item)) or "open"


def classify_decision_status(item):
    """
    'resolved' only when a pending decision explicitly says it was made
    (e.g. "was approved", "decision made"); otherwise 'open'. Words such as
    "approved" or "decided" alone are not enough.
    """

    if isinstance(item, dict):
        from_field = _status_from_text(item.get("status", ""))

        if from_field:
            return from_field

    status = _status_from_text(_item_text(item), decision=True)
    return "resolved" if status == "resolved" else "open"


_STATUS_SEVERITY = {"open": 2, "in_progress": 1, "resolved": 0}


def calculate_blocker_details(blockers):
    """
    Counts and penalties behind the blocker score (explainable).

    Only 'blockers' and 'pending_decisions' are scored; action items are
    never treated as blockers (they only earn coverage credit). The same
    text is counted once (the most unresolved status wins), also across
    blockers and decisions.

    Penalty per blocker = severity weight x status factor. The total is
    converted to a 0-100 score with diminishing returns, so a handful of
    well-managed blockers no longer drives the score to ~0.
    """

    blockers = blockers if isinstance(blockers, dict) else {}

    counts = {"open": 0, "in_progress": 0, "resolved": 0}
    statuses = {}
    texts = {}

    for item in _clean_items(blockers.get("blockers")):
        key = _text_key(_item_text(item))
        status = classify_item_status(item)

        if key not in statuses or _STATUS_SEVERITY[status] > _STATUS_SEVERITY[statuses[key]]:
            statuses[key] = status
            texts[key] = _item_text(item)

    for status in statuses.values():
        counts[status] += 1

    pending_decisions = 0
    resolved_decisions = 0
    seen_decisions = set()
    duplicates = 0
    decision_penalty = 0.0

    for item in _clean_items(blockers.get("pending_decisions")):
        key = _text_key(_item_text(item))

        if key in seen_decisions or key in statuses:
            duplicates += 1
            continue

        seen_decisions.add(key)

        if classify_decision_status(item) == "resolved":
            resolved_decisions += 1
        else:
            pending_decisions += 1
            decision_penalty += item_weight(_item_text(item), DECISION_WEIGHT)

    blocker_penalty = sum(
        item_weight(texts[key]) * BLOCKER_STATUS_FACTORS[status]
        for key, status in statuses.items()
    )

    action_count = len(_clean_items(blockers.get("action_items")))
    unresolved = counts["open"] + counts["in_progress"] + pending_decisions

    score = score_from_penalty(
        blocker_penalty + decision_penalty,
        unresolved,
        action_count,
    )

    return {
        "open": counts["open"],
        "in_progress": counts["in_progress"],
        "resolved": counts["resolved"],
        "pending_decisions": pending_decisions,
        "resolved_decisions": resolved_decisions,
        "action_items": action_count,
        "blocker_penalty": round(blocker_penalty, 1),
        "decision_penalty": round(decision_penalty, 1),
        "duplicates_ignored": duplicates,
        "score": score,
    }


def calculate_blocker_score(blockers):
    """
    Calculate blocker management score out of 100.

    Severity-weighted, status-aware and with diminishing returns; resolved
    blockers cost nothing, in-progress ones half, and action items that
    cover the open items earn credit. See calculate_blocker_details().
    """

    return calculate_blocker_details(blockers)["score"]


# --------------------------------------------------
# 4. RISK SCORE (likelihood x impact x mitigation status)
# --------------------------------------------------

_ID_PREFIX = re.compile(r"^\s*([A-Za-z]\d+)\s*[—–-]\s*")


def normalize_risk_records(risks):
    """
    One record per distinct risk finding.

    * Grouped records (several statements in 'evidence') are split into one
      record per statement.
    * Records that share a risk_id but carry different evidence are DIFFERENT
      findings and are all kept.
    * A finding is a duplicate only when the same risk type has the same
      evidence text (an ID prefix such as "R1 - " is ignored); it is counted
      once so repeated evidence does not inflate penalties.
    * Entries that are not dicts are skipped. Input that is not a list gives
      an empty result.
    """

    if not isinstance(risks, (list, tuple)):
        return []

    records = []
    seen = set()
    fallback_number = 0

    for item in risks:

        if not isinstance(item, dict):
            continue

        evidence = item.get("evidence", "")

        if isinstance(evidence, (list, tuple)):
            lines = [str(part).strip() for part in evidence if str(part).strip()]
        else:
            lines = [
                line.strip() for line in str(evidence or "").splitlines()
                if line.strip()
            ]

        if item.get("risk_id"):
            candidates = [{**item, "evidence": "\n".join(lines)}]

        else:
            candidates = []

            for line in (lines or [""]):
                fallback_number += 1
                id_match = _ID_PREFIX.match(line)
                candidates.append({
                    **item,
                    "risk_id": (
                        id_match.group(1).upper()
                        if id_match else f"G{fallback_number}"
                    ),
                    "evidence": line,
                })

        for record in candidates:

            type_key = str(record.get("risk_type", "")).casefold()
            evidence_key = _text_key(_ID_PREFIX.sub("", record["evidence"]))

            # Records with no evidence are told apart by their ID.
            key = (
                (type_key, evidence_key) if evidence_key
                else (type_key, "#id", str(record["risk_id"]))
            )

            if key in seen:
                continue

            seen.add(key)
            records.append(record)

    return records


def _parse_level(value):
    """
    Parse a 1-5 likelihood / impact from a number, numeric text ("4",
    "4/5", "3 - medium") or a level word ("high"). Returns None when the
    value is missing, a boolean, non-finite, or outside 1-5.
    """

    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        if not math.isfinite(value):
            return None
        number = int(math.floor(value + 0.5))
        return number if 1 <= number <= 5 else None

    if not isinstance(value, str):
        return None

    text = re.sub(r"[\s_-]+", " ", value.strip().lower())

    if not text:
        return None

    if text in LEVEL_WORDS:
        return LEVEL_WORDS[text]

    number_match = re.match(r"^(\d+(?:\.\d+)?)\b", text)

    if number_match:
        return _parse_level(float(number_match.group(1)))

    return None


def _normalize_mitigation(record):
    """
    Return (status, given): status is 'open', 'in_progress' or 'mitigated';
    'given' says whether the record really stated it.

    Unresolved wording ("not mitigated", "unresolved") is never read as
    mitigated. Missing or unrecognised wording is treated as open and
    reported as not given.
    """

    if not isinstance(record, dict):
        return "open", False

    raw = record.get("mitigation_status") or record.get("status") or ""
    text = str(raw).strip()

    if not text:
        return "open", False

    status = _status_from_text(text)

    if status == "resolved":
        return "mitigated", True

    if status in ("open", "in_progress"):
        return status, True

    if _OPEN_WORDS.search(text):
        return "open", True

    return "open", False


def assess_risk_record(record):
    """Likelihood, impact, status and data gaps for one risk record."""

    record = record if isinstance(record, dict) else {}

    missing = []
    estimated = False

    likelihood = _parse_level(record.get("likelihood"))
    impact = _parse_level(record.get("impact"))

    # Known types have typical values; every other type uses the plain
    # defaults for BOTH values (never 0).
    default_likelihood, default_impact = RISK_TYPE_DEFAULTS.get(
        record.get("risk_type", ""), (DEFAULT_LIKELIHOOD, DEFAULT_IMPACT)
    )

    if likelihood is None:
        likelihood = default_likelihood
        missing.append("likelihood")
        estimated = True

    if impact is None:
        impact = default_impact
        missing.append("impact")
        estimated = True

    likelihood = max(1, min(5, likelihood))
    impact = max(1, min(5, impact))

    status, status_given = _normalize_mitigation(record)

    if not status_given:
        missing.append("mitigation status")

    return {
        "risk_id": record.get("risk_id", "–"),
        "risk_type": record.get("risk_type", "Unknown") or "Unknown",
        "likelihood": likelihood,
        "impact": impact,
        "score": likelihood * impact,
        "status": status,
        "missing": missing,
        "estimated": estimated,
    }


def _criticality(score):
    if score <= 4:
        return "LOW", "#10B981"
    if score <= 9:
        return "MEDIUM", "#F59E0B"
    if score <= 16:
        return "HIGH", "#F97316"
    return "CRITICAL", "#EF476F"


def _risks_usable(risks):
    """A list that is empty (valid "none detected") or has dict entries."""

    return isinstance(risks, (list, tuple)) and (
        not risks or any(isinstance(item, dict) for item in risks)
    )


def assess_risk_matrix(risks):
    """
    Risk score (Likelihood x Impact, 1-25) and criticality, independent of
    the overall health score.

    The headline likelihood / impact are those of the highest-scoring risk
    that is not yet mitigated. Mitigated risks do not drive criticality.

    Returns None when the risks could not be assessed (risks is None or not
    a list). An empty list returns a dict with risk_count 0, score 0 and
    level "NONE DETECTED" ("no risk matched the detector"; not proof that
    the project has no risks). A non-empty list with no usable record
    returns level "NOT ASSESSED".
    """

    if not isinstance(risks, (list, tuple)):
        return None

    invalid_count = sum(1 for item in risks if not isinstance(item, dict))
    records = normalize_risk_records(risks)
    assessed = [assess_risk_record(record) for record in records]

    if not assessed:
        none_detected = not risks

        return {
            "likelihood": 0,
            "impact": 0,
            "score": 0,
            "level": "NONE DETECTED" if none_detected else "NOT ASSESSED",
            "color": "#64748B",
            "top_risk": None,
            "risk_count": 0,
            "active_count": 0,
            "estimated_count": 0,
            "missing_info": [],
            "risks": [],
            "no_risks_detected": none_detected,
            "invalid_count": invalid_count,
        }

    active = [item for item in assessed if item["status"] != "mitigated"]

    if active:
        worst = max(active, key=lambda item: item["score"])
        likelihood, impact = worst["likelihood"], worst["impact"]
        top_risk = f'{worst["risk_id"]} · {worst["risk_type"]}'
    else:
        likelihood, impact, top_risk = 1, 1, None

    score = likelihood * impact
    level, color = _criticality(score)

    missing_info = []

    for field in ("likelihood", "impact", "mitigation status"):
        count = sum(1 for item in assessed if field in item["missing"])

        if count:
            noun = "risk" if count == 1 else "risks"
            note = (
                " (estimated)"
                if field in ("likelihood", "impact") else
                " (treated as open)"
            )
            missing_info.append(
                f"{count} {noun} without a valid {field}{note}"
            )

    return {
        "likelihood": likelihood,
        "impact": impact,
        "score": score,
        "level": level,
        "color": color,
        "top_risk": top_risk,
        "risk_count": len(assessed),
        "active_count": len(active),
        "estimated_count": sum(1 for item in assessed if item["estimated"]),
        "missing_info": missing_info,
        "risks": assessed,
        "no_risks_detected": False,
        "invalid_count": invalid_count,
    }


def calculate_risk_score(risks):
    """
    Risk health out of 100 (higher is healthier).

    Every risk removes up to 25 points:
        penalty = 25 x (likelihood x impact / 25) x mitigation factor
    where the factor is 1.0 open, 0.5 in progress, 0.1 mitigated.
    Missing likelihood / impact / status are filled with documented
    defaults and reported by assess_risk_matrix().

    Returns None if the risks could not be assessed (None, not a list, or
    a non-empty list without a single usable record). An empty list gives
    100 meaning "the detector found nothing", which is not proof that the
    project has no risks.
    """

    if not _risks_usable(risks):
        return None

    total_penalty = 0.0

    for item in assess_risk_matrix(risks)["risks"]:
        severity = item["score"] / 25
        factor = RISK_STATUS_FACTORS[item["status"]]
        total_penalty += RISK_MAX_PENALTY * severity * factor

    return _clamp_score(100 - total_penalty)


# --------------------------------------------------
# 5. QUALITY SCORE (evidence based)
# --------------------------------------------------

def load_validation_evidence(path=None):
    """
    Load recorded validation results, or return (None, reason).

    Expected JSON (every section is optional):
    {
      "unit_tests":            {"passed": 42, "failed": 1},
      "formats_tested":        {"pdf": true, "docx": true, "csv": true, "txt": false},
      "extraction_validation": {"passed": 9, "total": 10},
      "retrieval_accuracy":    {"correct": 8, "total": 10},   // or {"accuracy": 0.8}
      "source_attribution":    {"passed": 10, "total": 10}
    }
    Nothing is invented: a missing file or section simply means "no evidence".
    """

    path = path or os.environ.get(VALIDATION_RESULTS_ENV) or DEFAULT_VALIDATION_FILE

    if not os.path.isfile(path):
        return None, f"No validation results file found ({os.path.basename(path)})."

    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as error:
        return None, f"Validation results file could not be read: {error}"

    if not isinstance(data, dict):
        return None, "Validation results file is not a JSON object."

    return data, None


def _ratio_score(section, passed_key, total_key):
    """
    Percentage from {passed_key, total_key} counts or {"accuracy"}.

    Counts must be non-negative integers (booleans rejected), total > 0 and
    passed <= total. If either count key is present the counts are used and
    must be valid; accuracy is only used when no count key is given, and
    must lie in 0-1 (fraction) or 0-100 (percent).
    Returns (score, detail), or (None, "") when unusable.
    """

    if not isinstance(section, dict):
        return None, ""

    passed = section.get(passed_key)
    total = section.get(total_key)

    if passed is not None or total is not None:

        if _is_count(passed) and _is_count(total) and total > 0 and passed <= total:
            return 100.0 * passed / total, f"{passed}/{total} passed"

        return None, ""

    accuracy = section.get("accuracy")

    if _is_number(accuracy) and 0 <= accuracy <= 100:
        pct = accuracy * 100 if accuracy <= 1 else accuracy
        return float(pct), f"accuracy {pct:.0f}%"

    return None, ""


def _document_text_check(project_text):
    """
    Real check on the analysed document: did extraction produce usable text?
    Looks at word count, share of letters/digits, and replacement characters.
    """

    text = project_text if isinstance(project_text, str) else ""
    visible = [ch for ch in text if not ch.isspace()]

    if not visible:
        return None, ""

    words = len(text.split())
    alnum_ratio = sum(ch.isalnum() for ch in visible) / len(visible)
    garbled_ratio = text.count("�") / len(visible)

    score = (
        100.0
        * min(1.0, words / 50)
        * min(1.0, alnum_ratio / 0.7)
        * (1 - min(1.0, garbled_ratio * 20))
    )

    return score, (
        f"{words} words, {alnum_ratio:.0%} letters/digits, "
        f"{garbled_ratio:.1%} unreadable characters"
    )


def evaluate_quality(project_text, evidence=None, evidence_note=None):
    """
    Explainable quality breakdown.

    Quality PERFORMANCE is the plain average of the components that have
    valid evidence:
      * recorded validation results: unit tests, supported formats,
        extraction validation, retrieval accuracy, source attribution;
      * quality practices found in the project documents themselves
        (testing / QA, reviews, acceptance criteria, defect handling,
        standards, monitoring; see blocker_agent.assess_quality), so a
        project whose documents describe its quality process is scored
        even when no validation_results.json exists;
      * the text check on the analysed document (only added when at least
        one of the above exists).
    Evidence COVERAGE (share of the 7 categories that are available) is
    reported separately and is not a component.

    The score needs at least one of the evidence components above. The
    document text check alone only says the extraction was readable, so
    without any evidence the score is None (not assessed) instead of a
    flattering number; the text check is still reported in
    'document_check'. Invalid sections (wrong types, negative counts,
    booleans as numbers, passed > total, accuracy out of range) are ignored
    and listed in 'invalid_evidence'.
    """

    components = []
    present = set()
    invalid = []

    def add(name, key, score, detail):
        components.append({
            "name": name,
            "score": _clamp_score(score),
            "detail": detail,
        })
        present.add(key)

    evidence = evidence if isinstance(evidence, dict) else {}

    # Unit tests
    tests = evidence.get("unit_tests")
    if tests is not None:
        passed = tests.get("passed") if isinstance(tests, dict) else None
        failed = tests.get("failed") if isinstance(tests, dict) else None

        if _is_count(passed) and _is_count(failed) and passed + failed > 0:
            add(
                "Unit tests", "unit_tests",
                100.0 * passed / (passed + failed),
                f"{passed} passed, {failed} failed",
            )
        else:
            invalid.append("unit tests")

    # Supported document formats: score = share of TESTED formats that pass
    formats = evidence.get("formats_tested")
    if formats is not None:
        passing, failing = [], []

        if isinstance(formats, dict):
            for name, ok in formats.items():
                name = str(name).lower()
                if name in SUPPORTED_FORMATS and isinstance(ok, bool):
                    (passing if ok else failing).append(name)

        if passing or failing:
            tested = len(passing) + len(failing)
            add(
                "Supported formats", "supported_formats",
                100.0 * len(passing) / tested,
                f"{len(passing)}/{tested} tested formats pass "
                f"({tested}/{len(SUPPORTED_FORMATS)} supported formats tested)"
                + (f"; failing: {', '.join(sorted(failing))}" if failing else ""),
            )
        else:
            invalid.append("supported formats")

    # Extraction validation / retrieval accuracy / source attribution
    for label, key, passed_key, total_key in (
        ("Extraction validation", "extraction_validation", "passed", "total"),
        ("Retrieval accuracy", "retrieval_accuracy", "correct", "total"),
        ("Source attribution", "source_attribution", "passed", "total"),
    ):
        section = evidence.get(key)

        if section is None:
            continue

        score, detail = _ratio_score(section, passed_key, total_key)

        if score is None:
            invalid.append(label.lower())
        else:
            add(label, key, score, detail)

    # Quality practices evidenced in the project documents themselves
    document_quality = assess_quality(project_text)

    if document_quality["assessed"]:
        add(
            "Document quality practices", "document_quality_evidence",
            document_quality["score"],
            document_quality["basis"],
        )

    evidence_components = len(components)

    # Check on the document being analysed
    text_score, text_detail = _document_text_check(project_text)
    document_check = None

    if text_score is not None:
        document_check = {
            "name": "Document text check",
            "score": _clamp_score(text_score),
            "detail": text_detail,
        }
        present.add("document_text_check")

        # The readable-text check only supports recorded validation results;
        # it must not lift a score that rests on document keywords alone.
        if evidence_components > (1 if document_quality["assessed"] else 0):
            components.append(document_check)

    coverage = 100.0 * len(present) / len(QUALITY_EVIDENCE_CATEGORIES)
    missing_evidence = [
        key for key in QUALITY_EVIDENCE_CATEGORIES if key not in present
    ]

    score = (
        _clamp_score(sum(item["score"] for item in components) / len(components))
        if evidence_components else None
    )

    return {
        "score": score,
        "components": components if evidence_components else [],
        "coverage": coverage,
        "missing_evidence": missing_evidence,
        "invalid_evidence": invalid,
        "document_check": document_check,
        "document_quality": document_quality,
        "note": evidence_note,
    }


def calculate_quality_score(project_text, evidence=None):
    """
    Quality health out of 100, from recorded validation evidence, quality
    practices found in the documents, and a check of the analysed text.
    Returns None if there is no valid evidence at all.

    evidence: optional dict (see load_validation_evidence). When omitted,
    validation_results.json is loaded if it exists.
    """

    if evidence is None:
        evidence, _ = load_validation_evidence()

    return evaluate_quality(project_text, evidence)["score"]


# --------------------------------------------------
# 6. AGENT OUTPUT HANDLING
# --------------------------------------------------

def _run_agent(label, function, project_text):
    """
    Call one analysis agent. Only exceptions raised by the agent call are
    caught (the agents are an external boundary); the error is returned and
    reported in the result, never swallowed. Returns (data, error_or_None).
    """

    try:
        return function(project_text), None
    except Exception as error:  # noqa: BLE001 - reported, not hidden
        return None, f"{label} failed ({type(error).__name__}: {error})"


def _validate_scope(data, error=None):
    """Return (clean_scope_dict, None) or (None, reason)."""

    if error:
        return None, error

    if not isinstance(data, dict):
        return None, "Scope agent returned an unexpected result type."

    if not any(isinstance(data.get(key), (list, tuple)) for key in SCOPE_KEYS[:4]):
        return None, "Scope agent returned no recognisable scope fields."

    return {key: _clean_items(data.get(key)) for key in SCOPE_KEYS}, None


def _validate_risks(data, error=None):
    """Return (normalised_risk_records, None) or (None, reason)."""

    if error:
        return None, error

    if not isinstance(data, (list, tuple)):
        return None, "Risk agent returned an unexpected result type."

    if data and not any(isinstance(item, dict) for item in data):
        return None, "Risk agent returned only malformed entries."

    return normalize_risk_records(data), None


def _validate_blockers(data, error=None):
    """Return (clean_blocker_dict, None) or (None, reason)."""

    if error:
        return None, error

    if not isinstance(data, dict):
        return None, "Blocker agent returned an unexpected result type."

    if not any(isinstance(data.get(key), (list, tuple)) for key in BLOCKER_KEYS[:2]):
        return None, "Blocker agent returned no blocker or decision fields."

    return {key: _clean_items(data.get(key)) for key in BLOCKER_KEYS}, None


# --------------------------------------------------
# 7. PROJECT ASSESSMENT
# --------------------------------------------------

def build_project_assessment(
    scope,
    risks,
    blockers,
    risk_matrix=None,
    quality_details=None,
    blocker_details=None,
    data_gaps=None,
):
    """
    Generate findings and recommendations.

    scope / risks / blockers may be None (assessment unavailable) or
    malformed; this never raises on bad input. Findings that say something
    is MISSING from the documents are worded differently from findings that
    confirm a problem. 'blocker_details' is accepted for compatibility.
    """

    scope_findings = []
    timeline_findings = []
    blocker_findings = []
    risk_findings = []
    quality_findings = []
    recommendations = []

    # Scope findings
    if isinstance(scope, dict):
        for key, found, missing, advice in (
            ("goals", "Project goals have been identified.",
             "No project goals were found in the document.",
             "Clearly define the project goals."),
            ("deliverables", "Project deliverables have been identified.",
             "No project deliverables were found in the document.",
             "Document the expected project deliverables."),
            ("milestones", "Project milestones have been identified.",
             "No project milestones were found in the document.",
             "Define measurable project milestones."),
        ):
            if scope.get(key):
                scope_findings.append(found)
            else:
                scope_findings.append(missing)
                recommendations.append(advice)
    else:
        scope_findings.append(
            "Scope could not be assessed (agent unavailable or invalid output)."
        )

    # Timeline and risk findings
    records = normalize_risk_records(risks)

    if risks is None or not isinstance(risks, (list, tuple)):
        timeline_findings.append(
            "Risks could not be assessed (agent unavailable or invalid output)."
        )

    elif records:
        for risk in records:
            risk_type = risk.get("risk_type", "Unknown")
            evidence = risk.get("evidence") or "No evidence provided."
            timeline_findings.append(f"{risk_type}: {evidence}")

        if risk_matrix is None:
            risk_matrix = assess_risk_matrix(records)

        if risk_matrix and risk_matrix["active_count"]:
            recommendations.append(
                f"Review the {risk_matrix['active_count']} unmitigated "
                "risk(s) and establish mitigation plans."
            )

    elif not risks:
        timeline_findings.append(
            "No risks matched the current keyword detection rules. "
            "This is not proof that the project has no risks."
        )

    else:
        timeline_findings.append(
            "Risk entries were malformed and could not be assessed."
        )

    # Blocker findings
    if isinstance(blockers, dict):
        seen = set()
        unresolved_blockers = unresolved_decisions = 0

        for item in _clean_items(blockers.get("blockers")):
            key = _text_key(_item_text(item))
            if key in seen:
                continue
            seen.add(key)

            status = classify_item_status(item)
            unresolved_blockers += status != "resolved"
            blocker_findings.append(
                f"Blocker ({status.replace('_', ' ')}): {_item_text(item)}"
            )

        for item in _clean_items(blockers.get("pending_decisions")):
            key = _text_key(_item_text(item))
            if key in seen:
                continue
            seen.add(key)

            if classify_decision_status(item) == "resolved":
                blocker_findings.append(f"Decision (made): {_item_text(item)}")
            else:
                unresolved_decisions += 1
                blocker_findings.append(f"Pending decision: {_item_text(item)}")

        if unresolved_blockers:
            recommendations.append("Prioritize resolving the identified blockers.")

        if unresolved_decisions:
            recommendations.append("Follow up on pending project decisions.")

        if not blocker_findings:
            blocker_findings.append(
                "No blockers or pending decisions were detected."
            )

    else:
        blocker_findings.append(
            "Blockers could not be assessed (agent unavailable or invalid output)."
        )

    # Risk likelihood x impact findings
    if isinstance(risk_matrix, dict) and risk_matrix.get("risk_count"):
        risk_findings.append(
            f"Risk score {risk_matrix['score']}/25 "
            f"(likelihood {risk_matrix['likelihood']} x impact "
            f"{risk_matrix['impact']}), criticality {risk_matrix['level']}."
        )
        risk_findings.extend(risk_matrix.get("missing_info", []))

        if risk_matrix.get("missing_info"):
            recommendations.append(
                "Record likelihood, impact and mitigation status for each risk."
            )

    # Quality findings
    if isinstance(quality_details, dict):
        for item in quality_details.get("components") or []:
            quality_findings.append(
                f"{item['name']}: {item['score']}/100"
                + (f" ({item['detail']})" if item.get("detail") else "")
            )

        # Which quality practices the documents evidence (testing, reviews...)
        document_quality = quality_details.get("document_quality") or {}
        quality_findings.extend(document_quality.get("findings") or [])

        for name in quality_details.get("invalid_evidence") or []:
            quality_findings.append(
                f"Validation evidence for {name} was invalid and ignored."
            )

        check = quality_details.get("document_check")
        if check and not quality_details.get("components"):
            quality_findings.append(
                f"Document text check: {check['score']}/100 ({check['detail']})"
            )

        if quality_details.get("missing_evidence"):
            recommendations.append(
                "Add quality evidence (test plans or results, reviews, "
                "acceptance criteria, defect tracking) to the project "
                "documents or record validation results to improve quality "
                "confidence."
            )

    # Dimensions that could not be assessed
    for gap in (data_gaps or []):
        recommendations.append(str(gap))

    return {
        "scope": scope_findings,
        "timeline": timeline_findings,
        "blockers": blocker_findings,
        "risk": risk_findings,
        "quality": quality_findings,
        "recommendations": list(dict.fromkeys(recommendations))
    }


# --------------------------------------------------
# 8. OVERALL PROJECT HEALTH
# --------------------------------------------------

def _status_for(overall_score):
    if overall_score >= 80:
        return "Healthy"
    if overall_score >= 60:
        return "Moderate Risk"
    if overall_score >= 40:
        return "High Risk"
    return "Critical"


def _agent_state(error, has_findings):
    if error:
        return {"state": "unavailable", "detail": error}
    if has_findings:
        return {"state": "findings", "detail": "Analysed; findings detected."}
    return {"state": "no_findings", "detail": "Analysed; nothing detected."}


def calculate_project_health(project_text):
    """
    Calculate five-dimensional project health.

    Dimensions: schedule (timeline_score), scope, risk, quality, blocker.
    Every dimension is 0-100. A dimension without valid supporting evidence
    is reported as NEUTRAL_SCORE in its legacy key, flagged in
    'dimension_status', set to None in 'dimension_scores', and left out of
    the equally weighted overall score.

    Existing keys are unchanged. Additional keys: dimension_scores,
    assessed_dimensions, assessment_confidence, agent_status, agent_errors.
    """

    if not isinstance(project_text, str) or not project_text.strip():
        return {
            "overall_score": 0,
            "scope_score": 0,
            "timeline_score": 0,
            "risk_score": 0,
            "quality_score": 0,
            "blocker_score": 0,
            "status": "Insufficient Data",
            "dimension_status": {
                name: {"assessed": False, "basis": "No project text provided."}
                for name in DIMENSIONS
            },
            "data_gaps": ["No project text was provided."],
            "assessment": {
                "scope": [],
                "timeline": [],
                "blockers": [],
                "risk": [],
                "quality": [],
                "recommendations": []
            },
            "dimension_scores": {name: None for name in DIMENSIONS},
            "assessed_dimensions": 0,
            "assessment_confidence": "none",
            "agent_status": {},
            "agent_errors": [],
        }

    # Run existing Milestone 2 agents (detection logic is not duplicated).
    # A failing agent only disables its own dimensions.
    scope, scope_error = _validate_scope(*_run_agent(
        "Scope agent", extract_scope_and_deliverables, project_text))
    raw_risks, risk_run_error = _run_agent(
        "Risk agent", detect_project_risks, project_text)
    risks, risk_error = _validate_risks(raw_risks, risk_run_error)
    ignored_risk_entries = (
        sum(1 for item in raw_risks if not isinstance(item, dict))
        if risks is not None else 0
    )
    blockers, blocker_error = _validate_blockers(*_run_agent(
        "Blocker agent", identify_blockers_and_actions, project_text))

    agent_status = {
        "scope": _agent_state(
            scope_error, bool(scope) and any(scope.values())),
        "risk": _agent_state(risk_error, bool(risks)),
        "blocker": _agent_state(
            blocker_error,
            bool(blockers) and any(blockers.values())),
    }
    agent_errors = [
        error for error in (scope_error, risk_error, blocker_error) if error
    ]

    # Scope
    scope_assessed = scope is not None
    scope_score = calculate_scope_score(scope) if scope_assessed else NEUTRAL_SCORE

    # Blockers
    blocker_assessed = blockers is not None
    blocker_details = calculate_blocker_details(blockers) if blocker_assessed else None
    blocker_score = blocker_details["score"] if blocker_assessed else NEUTRAL_SCORE

    # Risk
    risk_matrix = assess_risk_matrix(risks) if risks is not None else None
    risk_score = calculate_risk_score(risks) if risks is not None else None
    risk_assessed = risk_score is not None

    # Schedule: needs valid risk data (penalties come from risks) and some
    # schedule evidence in the document.
    schedule_assessed = risk_assessed and has_schedule_evidence(scope, risks)
    timeline_score = (
        calculate_timeline_score(risks) if schedule_assessed else NEUTRAL_SCORE
    )

    # Quality
    evidence, evidence_note = load_validation_evidence()
    quality_details = evaluate_quality(project_text, evidence, evidence_note)
    quality_score = quality_details["score"]
    quality_assessed = quality_score is not None

    # A missing validation file is only a data gap when it left the quality
    # score without any evidence; otherwise the documents supplied it.
    if quality_assessed and evidence is None:
        evidence_note = None

    if schedule_assessed:
        schedule_basis = "Timelines, milestones or schedule risks found."
    elif not risk_assessed:
        schedule_basis = "Schedule risks could not be evaluated because risk analysis is unavailable."
    else:
        schedule_basis = "No timelines, milestones or schedule risks found in the document."

    if scope_assessed:
        scope_basis = "Goals, deliverables and milestones extracted from the document."
    else:
        scope_basis = scope_error

    if risk_assessed and risk_matrix["risk_count"]:
        risk_basis = (
            f"{risk_matrix['risk_count']} risk(s) scored by likelihood, "
            "impact and mitigation status."
        )
    elif risk_assessed:
        risk_basis = (
            "Risk detector found no risks (keyword-based; this does not "
            "prove the project has no risks)."
        )
    else:
        risk_basis = risk_error or "Risk analysis returned no usable result."

    if quality_assessed:
        quality_basis = (
            f"{len(quality_details['components'])} evidence component(s); "
            f"evidence coverage {quality_details['coverage']:.0f}% of "
            f"{len(QUALITY_EVIDENCE_CATEGORIES)} categories."
        )
    else:
        quality_basis = (
            "No quality evidence (testing, reviews, acceptance criteria or "
            "validation results) found."
        )

    if blocker_assessed:
        blocker_basis = (
            f"{blocker_details['open']} open, "
            f"{blocker_details['in_progress']} in progress, "
            f"{blocker_details['resolved']} resolved blocker(s); "
            f"{blocker_details['pending_decisions']} pending decision(s); "
            f"{blocker_details['action_items']} action item(s)."
        )
    else:
        blocker_basis = blocker_error

    def status_entry(assessed, basis, state):
        return {"assessed": assessed, "basis": basis, "state": state}

    dimension_status = {
        "schedule": status_entry(
            schedule_assessed, schedule_basis,
            "assessed" if schedule_assessed else "unavailable"
            if not risk_assessed else "insufficient_evidence"),
        "scope": status_entry(
            scope_assessed, scope_basis,
            agent_status["scope"]["state"]),
        "risk": status_entry(
            risk_assessed, risk_basis,
            agent_status["risk"]["state"]),
        "quality": status_entry(
            quality_assessed, quality_basis,
            "assessed" if quality_assessed else "insufficient_evidence"),
        "blocker": status_entry(
            blocker_assessed, blocker_basis,
            agent_status["blocker"]["state"]),
    }

    data_gaps = [
        f"{name.title()} could not be assessed: {info['basis']}"
        for name, info in dimension_status.items()
        if not info["assessed"]
    ]

    if evidence_note:
        data_gaps.append(evidence_note)

    if ignored_risk_entries:
        data_gaps.append(
            f"{ignored_risk_entries} malformed risk entr"
            f"{'y was' if ignored_risk_entries == 1 else 'ies were'} ignored."
        )

    if quality_details["invalid_evidence"]:
        data_gaps.append(
            "Invalid validation evidence ignored: "
            + ", ".join(quality_details["invalid_evidence"]) + "."
        )

    scores = {
        "schedule": timeline_score,
        "scope": scope_score,
        "risk": NEUTRAL_SCORE if risk_score is None else risk_score,
        "quality": NEUTRAL_SCORE if quality_score is None else quality_score,
        "blocker": blocker_score,
    }

    dimension_scores = {
        name: (scores[name] if dimension_status[name]["assessed"] else None)
        for name in DIMENSIONS
    }

    assessed_scores = [
        value for value in dimension_scores.values() if value is not None
    ]

    # Equal weighting across the assessed dimensions
    if assessed_scores:
        overall_score = _clamp_score(sum(assessed_scores) / len(assessed_scores))
    else:
        overall_score = NEUTRAL_SCORE

    # Nothing at all was detected by any agent: the text carries no usable
    # project information, so do not present clean-looking scores as health.
    no_project_signal = all(
        entry["state"] == "no_findings" for entry in agent_status.values()
    )

    # Determine project status
    if len(assessed_scores) < MIN_ASSESSED_DIMENSIONS or no_project_signal:
        status = "Insufficient Data"
    else:
        status = _status_for(overall_score)

    # A high or critical unmitigated risk keeps the project from being
    # labelled "Healthy", even when the equal-weight average is high.
    if (
        status == "Healthy"
        and isinstance(risk_matrix, dict)
        and risk_matrix.get("level") in ("HIGH", "CRITICAL")
    ):
        status = "Moderate Risk"
        data_gaps.append(
            f"Status capped at Moderate Risk: risk criticality is "
            f"{risk_matrix['level']}."
        )

    if len(assessed_scores) == len(DIMENSIONS):
        confidence = "full"
    elif len(assessed_scores) >= MIN_ASSESSED_DIMENSIONS:
        confidence = "partial"
    else:
        confidence = "low"

    if no_project_signal:
        data_gaps.append(
            "No scope, risk or blocker information was detected in the "
            "document, so the scores are not a reliable health indicator."
        )
    elif confidence == "partial":
        data_gaps.append(
            f"Overall score is based on {len(assessed_scores)} of "
            f"{len(DIMENSIONS)} dimensions."
        )

    # Generate assessment
    assessment = build_project_assessment(
        scope,
        risks,
        blockers,
        risk_matrix=risk_matrix,
        quality_details=quality_details,
        blocker_details=blocker_details,
        data_gaps=data_gaps,
    )

    return {
        "overall_score": overall_score,
        "scope_score": scope_score,
        "timeline_score": timeline_score,
        "risk_score": scores["risk"],
        "quality_score": scores["quality"],
        "blocker_score": blocker_score,
        "status": status,
        "assessment": assessment,
        "dimension_status": dimension_status,
        "data_gaps": data_gaps,
        "risk_details": risk_matrix,
        "quality_details": quality_details,
        "blocker_details": blocker_details,
        "dimension_scores": dimension_scores,
        "assessed_dimensions": len(assessed_scores),
        "assessment_confidence": confidence,
        "agent_status": agent_status,
        "agent_errors": agent_errors,
    }

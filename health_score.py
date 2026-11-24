import json
import os
import re

from scope_agent import extract_scope_and_deliverables
from risk_agent import detect_project_risks
from blocker_agent import identify_blockers_and_actions


# --------------------------------------------------
# CONSTANTS
# --------------------------------------------------

# Value shown for a dimension that has no supporting evidence. It is NOT
# used in the overall score (unassessed dimensions are excluded), it only
# keeps every dimension numeric (0-100) for the UI.
NEUTRAL_SCORE = 50

DIMENSIONS = ("schedule", "scope", "risk", "quality", "blocker")

# Blocker penalties (points removed from 100 per item)
BLOCKER_PENALTIES = {
    "open": 20,
    "in_progress": 10,
    "resolved": 0,
}
DECISION_PENALTY = 10          # pending decision (separate from blockers)

# Risk handling
RISK_MAX_PENALTY = 25          # one open risk with L=5, I=5 removes 25 points
RISK_STATUS_FACTORS = {
    "open": 1.0,
    "in_progress": 0.5,
    "mitigated": 0.1,
}
DEFAULT_LIKELIHOOD = 3         # used only when a risk has no likelihood
DEFAULT_IMPACT = 3             # used only when a risk has no impact

# Typical (likelihood, impact) when the detector gives none. These are
# flagged as "estimated" everywhere they are used.
RISK_TYPE_DEFAULTS = {
    "Schedule Delay": (3, 4),
    "Dependency Risk": (3, 3),
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
    "document_text_check",
)

VALIDATION_RESULTS_ENV = "PROJECT_VALIDATION_RESULTS"
DEFAULT_VALIDATION_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "validation_results.json"
)


# --------------------------------------------------
# SMALL HELPERS
# --------------------------------------------------

def _clamp_score(value):
    return max(0, min(100, int(round(value))))


def _item_text(item):
    """Text of a blocker / decision (strings, or dicts with a text field)."""

    if isinstance(item, dict):
        for key in ("text", "description", "blocker", "decision", "content"):
            if item.get(key):
                return str(item[key])
        return ""

    return str(item)


# --------------------------------------------------
# 1. SCOPE CLARITY SCORE  (unchanged)
# --------------------------------------------------

def calculate_scope_score(scope):
    """Calculate scope clarity score out of 100."""

    score = 0

    if scope.get("goals"):
        score += 40

    if scope.get("deliverables"):
        score += 40

    if scope.get("milestones"):
        score += 20

    return score


# --------------------------------------------------
# 2. TIMELINE HEALTH SCORE  (unchanged)
# --------------------------------------------------

def calculate_timeline_score(risks):
    """Calculate timeline health based on actual schedule-related risks."""

    score = 100

    penalties = {
        "Schedule Delay": 30,
        "Dependency Risk": 15
    }

    for risk in risks:
        risk_type = risk.get("risk_type", "")
        score -= penalties.get(risk_type, 0)

    return max(0, score)


def has_schedule_evidence(scope, risks):
    """
    A schedule score is only meaningful if the document says something
    about the schedule: timelines / milestones, or a schedule-related risk.
    """

    scope = scope or {}

    if scope.get("timelines") or scope.get("milestones"):
        return True

    return any(
        isinstance(risk, dict)
        and risk.get("risk_type") in ("Schedule Delay", "Dependency Risk")
        for risk in (risks or [])
    )


# --------------------------------------------------
# 3. BLOCKER MANAGEMENT SCORE  (status aware)
# --------------------------------------------------

_NOT_RESOLVED = re.compile(
    r"\b(unresolved|not\s+(yet\s+)?(resolved|fixed|completed|done|cleared)"
    r"|yet\s+to\s+be\s+(resolved|fixed))\b",
    re.IGNORECASE,
)
_RESOLVED = re.compile(
    r"\b(resolved|closed|fixed|completed|unblocked|cleared|done"
    r"|approved|decided|signed[\s-]off)\b",
    re.IGNORECASE,
)
_IN_PROGRESS = re.compile(
    r"\b(in[\s-]progress|ongoing|underway|being\s+(addressed|worked|resolved"
    r"|investigated|fixed)|working\s+on|partially\s+(resolved|complete\w*))\b",
    re.IGNORECASE,
)


def classify_item_status(item):
    """
    Return 'open', 'in_progress' or 'resolved' for a blocker or decision.

    An explicit 'status' field wins. Otherwise the wording of the text is
    used. Anything without status wording is treated as open.
    """

    status_field = ""

    if isinstance(item, dict):
        status_field = str(item.get("status", "") or "")

    text = status_field or _item_text(item)

    if _NOT_RESOLVED.search(text):
        return "open"

    if _IN_PROGRESS.search(text):
        return "in_progress"

    if _RESOLVED.search(text):
        return "resolved"

    return "open"


def calculate_blocker_details(blockers):
    """Counts and penalties behind the blocker score (explainable)."""

    blockers = blockers or {}

    counts = {"open": 0, "in_progress": 0, "resolved": 0}

    for item in blockers.get("blockers", []) or []:
        counts[classify_item_status(item)] += 1

    pending_decisions = 0
    resolved_decisions = 0

    for item in blockers.get("pending_decisions", []) or []:
        if classify_item_status(item) == "resolved":
            resolved_decisions += 1
        else:
            pending_decisions += 1

    blocker_penalty = sum(
        counts[state] * BLOCKER_PENALTIES[state] for state in counts
    )
    decision_penalty = pending_decisions * DECISION_PENALTY

    return {
        "open": counts["open"],
        "in_progress": counts["in_progress"],
        "resolved": counts["resolved"],
        "pending_decisions": pending_decisions,
        "resolved_decisions": resolved_decisions,
        "blocker_penalty": blocker_penalty,
        "decision_penalty": decision_penalty,
        "score": max(0, 100 - blocker_penalty - decision_penalty),
    }


def calculate_blocker_score(blockers):
    """
    Calculate blocker management score out of 100.

    Open blockers cost 20 points, in-progress blockers 10, resolved 0.
    Each pending decision costs a separate 10 points.
    """

    return calculate_blocker_details(blockers)["score"]


# --------------------------------------------------
# 4. RISK SCORE (likelihood x impact x mitigation status)
# --------------------------------------------------

def normalize_risk_records(risks):
    """
    One record per distinct risk. Grouped records (several statements in
    'evidence') are split per statement; duplicates are counted once.
    Mirrors the de-duplication used by the dashboard.
    """

    records = []
    seen_ids = set()
    seen_text = set()
    fallback_number = 0

    for item in (risks or []):

        if not isinstance(item, dict):
            continue

        if item.get("risk_id"):
            candidates = [item]

        else:
            lines = [
                line.strip()
                for line in str(item.get("evidence", "")).splitlines()
                if line.strip()
            ] or [""]

            candidates = []

            for line in lines:
                fallback_number += 1
                id_match = re.match(r"^([A-Za-z]\d+)\s*[—–-]", line)
                candidates.append({
                    **item,
                    "risk_id": (
                        id_match.group(1).upper()
                        if id_match else f"G{fallback_number}"
                    ),
                    "evidence": line,
                })

        for record in candidates:

            text_key = " ".join(
                str(record.get("evidence", "")).split()
            ).casefold()

            if record["risk_id"] in seen_ids:
                continue

            if text_key and text_key in seen_text:
                continue

            seen_ids.add(record["risk_id"])

            if text_key:
                seen_text.add(text_key)

            records.append(record)

    return records


def _parse_level(value):
    """Parse a 1-5 likelihood/impact (number or word). None if unusable."""

    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        return int(max(1, min(5, round(value))))

    text = str(value).strip().lower()

    if text.isdigit():
        return int(max(1, min(5, int(text))))

    return LEVEL_WORDS.get(text)


def _normalize_mitigation(record):
    """Return 'open' / 'in_progress' / 'mitigated' and whether it was given."""

    raw = (
        record.get("mitigation_status")
        or record.get("status")
        or ""
    )
    text = str(raw).strip().lower()

    if not text:
        return "open", False

    if re.search(r"resolv|mitigat|closed|done|complete", text):
        return "mitigated", True

    if re.search(r"progress|ongoing|underway", text):
        return "in_progress", True

    return "open", True


def assess_risk_record(record):
    """Likelihood, impact, status and data gaps for one risk record."""

    missing = []
    estimated = False

    likelihood = _parse_level(record.get("likelihood"))
    impact = _parse_level(record.get("impact"))

    type_defaults = RISK_TYPE_DEFAULTS.get(record.get("risk_type", ""))

    if likelihood is None:
        likelihood = (type_defaults or (DEFAULT_LIKELIHOOD, 0))[0]
        missing.append("likelihood")
        estimated = True

    if impact is None:
        impact = (type_defaults or (0, DEFAULT_IMPACT))[1]
        missing.append("impact")
        estimated = True

    status, status_given = _normalize_mitigation(record)

    if not status_given:
        missing.append("mitigation status")

    return {
        "risk_id": record.get("risk_id", "–"),
        "risk_type": record.get("risk_type", "Unknown"),
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


def assess_risk_matrix(risks):
    """
    Risk score (Likelihood x Impact, 1-25) and criticality, independent of
    the overall health score.

    The headline likelihood / impact are those of the highest-scoring risk
    that is not yet mitigated. Mitigated risks do not drive criticality.
    Returns None when risk analysis has not been run (risks is None).
    """

    if risks is None:
        return None

    records = normalize_risk_records(risks)
    assessed = [assess_risk_record(record) for record in records]

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
                " (estimated from risk type)"
                if field in ("likelihood", "impact") else
                " (treated as open)"
            )
            missing_info.append(
                f"{count} {noun} without {field}{note}"
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
    }


def calculate_risk_score(risks):
    """
    Risk health out of 100 (higher is healthier).

    Every risk removes up to 25 points:
        penalty = 25 x (likelihood x impact / 25) x mitigation factor
    where the factor is 1.0 open, 0.5 in progress, 0.1 mitigated.
    Missing likelihood / impact / status are filled with documented
    defaults and reported by assess_risk_matrix().

    Returns None if risk analysis has not been run (risks is None).
    """

    if risks is None:
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
    """Percentage from {passed,total} (or {accuracy}); None if unusable."""

    if not isinstance(section, dict):
        return None, ""

    passed = section.get(passed_key)
    total = section.get(total_key)

    if (
        isinstance(passed, (int, float)) and isinstance(total, (int, float))
        and total > 0 and 0 <= passed <= total
    ):
        return 100.0 * passed / total, f"{int(passed)}/{int(total)} passed"

    accuracy = section.get("accuracy")

    if isinstance(accuracy, (int, float)) and 0 <= accuracy <= 100:
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

    Components (each 0-100, only those with evidence are used):
      unit tests, supported formats, extraction validation, retrieval
      accuracy, source attribution, a text check on the analysed document,
      and validation coverage = share of the 6 evidence categories present.
    The quality score is the plain average of the components.
    """

    components = []
    present = set()

    def add(name, key, score, detail):
        if score is not None:
            components.append({
                "name": name,
                "score": _clamp_score(score),
                "detail": detail,
            })
            present.add(key)

    evidence = evidence if isinstance(evidence, dict) else {}

    # Unit tests
    tests = evidence.get("unit_tests")
    if isinstance(tests, dict):
        passed, failed = tests.get("passed"), tests.get("failed")
        if (
            isinstance(passed, int) and isinstance(failed, int)
            and passed >= 0 and failed >= 0 and passed + failed > 0
        ):
            add(
                "Unit tests", "unit_tests",
                100.0 * passed / (passed + failed),
                f"{passed} passed, {failed} failed",
            )

    # Supported document formats
    formats = evidence.get("formats_tested")
    if isinstance(formats, dict) and formats:
        passing = [
            name.lower() for name, ok in formats.items()
            if ok is True and name.lower() in SUPPORTED_FORMATS
        ]
        failing = [
            name.lower() for name, ok in formats.items()
            if ok is False and name.lower() in SUPPORTED_FORMATS
        ]
        if passing or failing:
            add(
                "Supported formats", "supported_formats",
                100.0 * len(passing) / len(SUPPORTED_FORMATS),
                f"{len(passing)}/{len(SUPPORTED_FORMATS)} formats validated"
                + (f"; failing: {', '.join(failing)}" if failing else ""),
            )

    # Extraction validation / retrieval accuracy / source attribution
    for label, key, passed_key, total_key in (
        ("Extraction validation", "extraction_validation", "passed", "total"),
        ("Retrieval accuracy", "retrieval_accuracy", "correct", "total"),
        ("Source attribution", "source_attribution", "passed", "total"),
    ):
        score, detail = _ratio_score(evidence.get(key), passed_key, total_key)
        add(label, key, score, detail)

    # Check on the document being analysed
    score, detail = _document_text_check(project_text)
    add("Document text check", "document_text_check", score, detail)

    if not components:
        return {
            "score": None,
            "components": [],
            "coverage": 0.0,
            "missing_evidence": list(QUALITY_EVIDENCE_CATEGORIES),
            "note": evidence_note,
        }

    coverage = 100.0 * len(present) / len(QUALITY_EVIDENCE_CATEGORIES)

    components.append({
        "name": "Validation coverage",
        "score": _clamp_score(coverage),
        "detail": (
            f"{len(present)}/{len(QUALITY_EVIDENCE_CATEGORIES)} "
            "evidence categories available"
        ),
    })

    score = _clamp_score(
        sum(item["score"] for item in components) / len(components)
    )

    return {
        "score": score,
        "components": components,
        "coverage": coverage,
        "missing_evidence": [
            key for key in QUALITY_EVIDENCE_CATEGORIES if key not in present
        ],
        "note": evidence_note,
    }


def calculate_quality_score(project_text, evidence=None):
    """
    Quality health out of 100, from recorded validation evidence plus a
    check of the analysed text. Returns None if there is no evidence at all.

    evidence: optional dict (see load_validation_evidence). When omitted,
    validation_results.json is loaded if it exists.
    """

    if evidence is None:
        evidence, _ = load_validation_evidence()

    return evaluate_quality(project_text, evidence)["score"]


# --------------------------------------------------
# 6. PROJECT ASSESSMENT
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
    """Generate findings and recommendations."""

    scope_findings = []
    timeline_findings = []
    blocker_findings = []
    risk_findings = []
    quality_findings = []
    recommendations = []

    # Scope findings
    if scope.get("goals"):
        scope_findings.append("Project goals have been identified.")
    else:
        scope_findings.append("Project goals are missing.")
        recommendations.append(
            "Clearly define the project goals."
        )

    if scope.get("deliverables"):
        scope_findings.append("Project deliverables have been identified.")
    else:
        scope_findings.append("Project deliverables are missing.")
        recommendations.append(
            "Document the expected project deliverables."
        )

    if scope.get("milestones"):
        scope_findings.append("Project milestones have been identified.")
    else:
        scope_findings.append("Project milestones are missing.")
        recommendations.append(
            "Define measurable project milestones."
        )

    # Timeline and risk findings
    if risks:
        for risk in risks:
            risk_type = risk.get("risk_type", "Unknown")
            evidence = risk.get("evidence", "No evidence provided.")

            timeline_findings.append(
                f"{risk_type}: {evidence}"
            )

        recommendations.append(
            "Review detected risks and establish mitigation plans."
        )
    else:
        timeline_findings.append(
            "No risks matched the current detection rules."
        )

    # Blocker findings
    detected_blockers = blockers.get("blockers", [])
    pending_decisions = blockers.get("pending_decisions", [])

    if detected_blockers:
        blocker_findings.extend(
            [
                f"Blocker ({classify_item_status(item).replace('_', ' ')}): "
                f"{_item_text(item)}"
                for item in detected_blockers
            ]
        )
        recommendations.append(
            "Prioritize resolving the identified blockers."
        )

    if pending_decisions:
        blocker_findings.extend(
            [f"Pending decision: {_item_text(item)}" for item in pending_decisions]
        )
        recommendations.append(
            "Follow up on pending project decisions."
        )

    if not detected_blockers and not pending_decisions:
        blocker_findings.append(
            "No blockers or pending decisions were detected."
        )

    # Risk likelihood x impact findings
    if risk_matrix and risk_matrix["risk_count"]:
        risk_findings.append(
            f"Risk score {risk_matrix['score']}/25 "
            f"(likelihood {risk_matrix['likelihood']} x impact "
            f"{risk_matrix['impact']}), criticality {risk_matrix['level']}."
        )
        risk_findings.extend(risk_matrix["missing_info"])

        if risk_matrix["missing_info"]:
            recommendations.append(
                "Record likelihood, impact and mitigation status for each risk."
            )

    # Quality findings
    if quality_details and quality_details.get("components"):
        for item in quality_details["components"]:
            quality_findings.append(
                f"{item['name']}: {item['score']}/100"
                + (f" ({item['detail']})" if item["detail"] else "")
            )

        if quality_details.get("missing_evidence"):
            recommendations.append(
                "Record validation results (unit tests, formats, extraction, "
                "retrieval accuracy, source attribution) to improve quality "
                "confidence."
            )

    # Dimensions that could not be assessed
    for gap in (data_gaps or []):
        recommendations.append(gap)

    return {
        "scope": scope_findings,
        "timeline": timeline_findings,
        "blockers": blocker_findings,
        "risk": risk_findings,
        "quality": quality_findings,
        "recommendations": list(dict.fromkeys(recommendations))
    }


# --------------------------------------------------
# 7. OVERALL PROJECT HEALTH
# --------------------------------------------------

def _status_for(overall_score):
    if overall_score >= 80:
        return "Healthy"
    if overall_score >= 60:
        return "Moderate Risk"
    if overall_score >= 40:
        return "High Risk"
    return "Critical"


def calculate_project_health(project_text):
    """
    Calculate five-dimensional project health.

    Dimensions: schedule (timeline_score), scope, risk, quality, blocker.
    Every dimension is 0-100. A dimension without supporting evidence is
    reported as NEUTRAL_SCORE, flagged in 'dimension_status' and left out
    of the equally weighted overall score.
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
            }
        }

    # Run existing Milestone 2 agents (detection logic is not duplicated)
    scope = extract_scope_and_deliverables(project_text)
    risks = detect_project_risks(project_text)
    blockers = identify_blockers_and_actions(project_text)

    # Dimension scores
    scope_score = calculate_scope_score(scope)
    blocker_details = calculate_blocker_details(blockers)
    blocker_score = blocker_details["score"]

    schedule_assessed = has_schedule_evidence(scope, risks)
    timeline_score = (
        calculate_timeline_score(risks) if schedule_assessed else NEUTRAL_SCORE
    )

    risk_matrix = assess_risk_matrix(risks)
    risk_score = calculate_risk_score(risks)

    evidence, evidence_note = load_validation_evidence()
    quality_details = evaluate_quality(project_text, evidence, evidence_note)
    quality_score = quality_details["score"]

    dimension_status = {
        "schedule": {
            "assessed": schedule_assessed,
            "basis": (
                "Timelines, milestones or schedule risks found."
                if schedule_assessed else
                "No timelines, milestones or schedule risks found in the document."
            ),
        },
        "scope": {
            "assessed": True,
            "basis": "Goals, deliverables and milestones extracted from the document.",
        },
        "risk": {
            "assessed": risk_score is not None,
            "basis": (
                f"{risk_matrix['risk_count']} risk(s) scored by likelihood, "
                "impact and mitigation status."
                if risk_score is not None else
                "Risk analysis returned no result."
            ),
        },
        "quality": {
            "assessed": quality_score is not None,
            "basis": (
                f"{len(quality_details['components']) - 1} evidence "
                "component(s) available."
                if quality_score is not None else
                "No validation evidence available."
            ),
        },
        "blocker": {
            "assessed": True,
            "basis": (
                f"{blocker_details['open']} open, "
                f"{blocker_details['in_progress']} in progress, "
                f"{blocker_details['resolved']} resolved blocker(s); "
                f"{blocker_details['pending_decisions']} pending decision(s)."
            ),
        },
    }

    data_gaps = [
        f"{name.title()} could not be assessed: {info['basis']}"
        for name, info in dimension_status.items()
        if not info["assessed"]
    ]

    if evidence_note:
        data_gaps.append(evidence_note)

    scores = {
        "schedule": timeline_score,
        "scope": scope_score,
        "risk": NEUTRAL_SCORE if risk_score is None else risk_score,
        "quality": NEUTRAL_SCORE if quality_score is None else quality_score,
        "blocker": blocker_score,
    }

    assessed_scores = [
        scores[name] for name in DIMENSIONS
        if dimension_status[name]["assessed"]
    ]

    # Equal weighting across the assessed dimensions
    if assessed_scores:
        overall_score = round(sum(assessed_scores) / len(assessed_scores))
    else:
        overall_score = NEUTRAL_SCORE

    # Determine project status
    if len(assessed_scores) < 3:
        status = "Insufficient Data"
    else:
        status = _status_for(overall_score)

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
    }


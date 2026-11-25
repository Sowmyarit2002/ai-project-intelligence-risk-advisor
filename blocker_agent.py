import math
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


# --------------------------------------------------
# RECORD EXTRACTION (unchanged behaviour)
# --------------------------------------------------

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


# --------------------------------------------------
# BLOCKER SCORING
# --------------------------------------------------
# Tunable constants. Higher score = healthier (fewer / better-managed
# blockers). The old logic subtracted a flat amount per blocker, so 4
# blockers already meant 20/100. The new score:
#   1. weights each blocker by severity,
#   2. ignores blockers that are already resolved,
#   3. gives credit when a blocker has an owner / plan / due date,
#   4. gives credit when action items exist to clear the blockers,
#   5. uses diminishing returns so the score never collapses to ~0.

CRITICAL_PATTERN = re.compile(
    r"critical|show[- ]?stopper|cannot proceed|can't proceed|halted|"
    r"stalled|no access|unavailable|outage|failed|legal|security|"
    r"compliance",
    re.IGNORECASE,
)

HIGH_PATTERN = re.compile(
    r"delay|waiting|awaiting|dependen|approval|pending|not yet|missing|"
    r"unresolved|overdue|budget|vendor|shortage",
    re.IGNORECASE,
)

RESOLVED_PATTERN = re.compile(
    r"\b(resolved|closed|cleared|completed|unblocked|no longer)\b",
    re.IGNORECASE,
)

MITIGATION_PATTERN = re.compile(
    r"\b(owner|owned by|assigned|mitigat\w*|workaround|plan|due|target|"
    r"eta|escalat\w*|scheduled|by \d{1,2}|by (?:mon|tue|wed|thu|fri|jan|"
    r"feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec))\b",
    re.IGNORECASE,
)

CRITICAL_WEIGHT = 14
HIGH_WEIGHT = 9
NORMAL_WEIGHT = 6
DECISION_WEIGHT = 5

MITIGATION_DISCOUNT = 0.75      # blocker already has owner/plan/date
ACTION_COVERAGE_CREDIT = 0.30   # up to 30% off when actions cover blockers
DECAY_SCALE = 35.0              # larger = more forgiving
MIN_SCORE = 10


def item_weight(description, base_weight=None):
    """Penalty weight for one blocker or pending decision."""

    if RESOLVED_PATTERN.search(description):
        return 0.0

    if base_weight is not None:
        weight = float(base_weight)
    elif CRITICAL_PATTERN.search(description):
        weight = CRITICAL_WEIGHT
    elif HIGH_PATTERN.search(description):
        weight = HIGH_WEIGHT
    else:
        weight = NORMAL_WEIGHT

    if MITIGATION_PATTERN.search(description):
        weight *= MITIGATION_DISCOUNT

    return weight


def score_from_penalty(penalty, open_items, action_count):
    """
    Turn a total penalty into a 0-100 blocker score.

    Action items that cover the open items reduce the penalty, and the
    score decays smoothly so it never collapses to ~0.
    """

    if penalty <= 0:
        return 100

    coverage = min(action_count / max(open_items, 1), 1.0)
    penalty *= 1.0 - ACTION_COVERAGE_CREDIT * coverage

    score = round(100 * math.exp(-penalty / DECAY_SCALE))
    return max(MIN_SCORE, min(100, score))


def calculate_blocker_score(blockers, pending_decisions, action_items):
    """Return (score 0-100, basis text)."""

    blockers = blockers or []
    pending_decisions = pending_decisions or []
    action_items = action_items or []

    if not blockers and not pending_decisions:
        return 100, "No blockers or pending decisions detected."

    penalty = sum(item_weight(item) for item in blockers)
    penalty += sum(
        item_weight(item, DECISION_WEIGHT)
        for item in pending_decisions
    )

    score = score_from_penalty(
        penalty,
        len(blockers) + len(pending_decisions),
        len(action_items),
    )

    basis = (
        f"{len(blockers)} blocker(s), {len(pending_decisions)} pending "
        f"decision(s), {len(action_items)} action item(s) to resolve them."
    )

    return score, basis


# --------------------------------------------------
# QUALITY SCORING
# --------------------------------------------------
# Quality is scored from evidence in the document text. Each category
# below counts once when at least one of its terms appears. Negative
# signals (failed tests, open defects, rework) reduce the score.

QUALITY_CATEGORIES = {
    "Testing / QA": re.compile(
        r"\b(test(?:s|ing|ed)?|qa|quality assurance|uat|user acceptance|"
        r"unit test\w*|integration test\w*|regression|test cases?|"
        r"test plan|smoke test\w*)\b",
        re.IGNORECASE,
    ),
    "Reviews / sign-off": re.compile(
        r"\b(review(?:s|ed)?|code review|peer review|inspection|audit\w*|"
        r"sign[- ]?off|approved|walkthrough)\b",
        re.IGNORECASE,
    ),
    "Acceptance criteria": re.compile(
        r"\b(acceptance criteria|definition of done|exit criteria|"
        r"success criteria|kpis?|metrics?|sla|targets?)\b",
        re.IGNORECASE,
    ),
    "Defect management": re.compile(
        r"\b(defects?|bugs?|issue log|bug tracking|root cause|"
        r"corrective action|fix(?:es|ed)?)\b",
        re.IGNORECASE,
    ),
    "Standards / compliance": re.compile(
        r"\b(standards?|iso ?\d*|compliance|compliant|checklist|"
        r"validation|verification|certif\w+|guidelines?)\b",
        re.IGNORECASE,
    ),
    "Performance / monitoring": re.compile(
        r"\b(performance|benchmark\w*|monitor\w*|load test\w*|"
        r"stress test\w*|reliability|uptime)\b",
        re.IGNORECASE,
    ),
}

QUALITY_NEGATIVE_PATTERN = re.compile(
    r"(failed (?:test|qa|uat|review|audit)|test(?:s)? failed|"
    r"open defects?|critical (?:defect|bug)s?|defect leakage|"
    r"rework|quality (?:issue|concern|problem)s?|"
    r"not (?:been )?tested|untested|failed validation)",
    re.IGNORECASE,
)

QUALITY_BASE = 35
QUALITY_PER_CATEGORY = 10
QUALITY_MENTION_BONUS_MAX = 10
QUALITY_NEGATIVE_PENALTY = 6
QUALITY_NEGATIVE_CAP = 30
QUALITY_MIN_MENTIONS = 2        # a category needs 2+ keyword hits to count
QUALITY_MAX_SCORE = 88          # keyword evidence alone can never reach 100


def assess_quality(text):
    """
    Return a dict:
      score    - 0-100 (50 when there is no evidence)
      assessed - False when the document has no quality evidence
      basis    - short explanation
      findings - list of human-readable findings
    """

    if not isinstance(text, str) or not text.strip():
        return {
            "score": 50,
            "assessed": False,
            "basis": "No document text available.",
            "findings": [],
        }

    findings = []
    mentions = 0

    for category, pattern in QUALITY_CATEGORIES.items():
        hits = pattern.findall(text)
        if len(hits) >= QUALITY_MIN_MENTIONS:
            mentions += len(hits)
            findings.append(
                f"{category}: evidence found ({len(hits)} mention(s))."
            )

    categories_found = len(findings)

    if categories_found == 0:
        return {
            "score": 50,
            "assessed": False,
            "basis": "No quality evidence (testing, reviews, "
                     "acceptance criteria) found in the documents.",
            "findings": [],
        }

    negatives = QUALITY_NEGATIVE_PATTERN.findall(text)
    negative_penalty = min(
        len(negatives) * QUALITY_NEGATIVE_PENALTY,
        QUALITY_NEGATIVE_CAP,
    )

    if negatives:
        findings.append(
            f"Quality concerns: {len(negatives)} negative signal(s) "
            "such as failed tests, open defects or rework."
        )

    bonus = min(mentions // 3, QUALITY_MENTION_BONUS_MAX)

    score = (
        QUALITY_BASE
        + categories_found * QUALITY_PER_CATEGORY
        + bonus
        - negative_penalty
    )
    score = max(10, min(QUALITY_MAX_SCORE, score))

    return {
        "score": score,
        "assessed": True,
        "basis": f"{categories_found} of {len(QUALITY_CATEGORIES)} "
                 "quality practices evidenced.",
        "findings": findings,
    }


# --------------------------------------------------
# MAIN ENTRY POINT
# --------------------------------------------------

def identify_blockers_and_actions(text):
    """
    Extract blockers, pending decisions and action items.

    B-series: blockers or unresolved decisions.
    A-series: action items.
    Other record types are excluded.

    Also returns "blocker_score" (0-100) and "blocker_basis".
    """

    result = {
        "blockers": [],
        "pending_decisions": [],
        "action_items": [],
        "blocker_score": 100,
        "blocker_basis": "No blockers or pending decisions detected."
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
    for category in ("blockers", "pending_decisions", "action_items"):
        result[category] = list(
            dict.fromkeys(result[category])
        )

    score, basis = calculate_blocker_score(
        result["blockers"],
        result["pending_decisions"],
        result["action_items"],
    )
    result["blocker_score"] = score
    result["blocker_basis"] = basis

    return result



from scope_agent import extract_scope_and_deliverables
from risk_agent import detect_project_risks
from blocker_agent import identify_blockers_and_actions


# --------------------------------------------------
# 1. SCOPE CLARITY SCORE
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
# 2. TIMELINE HEALTH SCORE
# --------------------------------------------------

def calculate_timeline_score(risks):
    """Calculate timeline health based on detected risks."""

    score = 100

    penalties = {
        "Schedule Delay": 30,
        "Dependency Risk": 15,
        "Delivery Challenge": 20
    }

    for risk in risks:
        risk_type = risk.get("risk_type", "")
        score -= penalties.get(risk_type, 0)

    return max(0, score)


# --------------------------------------------------
# 3. BLOCKER MANAGEMENT SCORE
# --------------------------------------------------

def calculate_blocker_score(blockers):
    """Calculate blocker management score out of 100."""

    blocker_count = len(blockers.get("blockers", []))
    decision_count = len(blockers.get("pending_decisions", []))

    score = 100 - (blocker_count * 20) - (decision_count * 10)

    return max(0, score)


# --------------------------------------------------
# 4. PROJECT ASSESSMENT
# --------------------------------------------------

def build_project_assessment(scope, risks, blockers):
    """Generate findings and recommendations."""

    scope_findings = []
    timeline_findings = []
    blocker_findings = []
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
            [f"Blocker: {item}" for item in detected_blockers]
        )
        recommendations.append(
            "Prioritize resolving the identified blockers."
        )

    if pending_decisions:
        blocker_findings.extend(
            [f"Pending decision: {item}" for item in pending_decisions]
        )
        recommendations.append(
            "Follow up on pending project decisions."
        )

    if not detected_blockers and not pending_decisions:
        blocker_findings.append(
            "No blockers or pending decisions were detected."
        )

    return {
        "scope": scope_findings,
        "timeline": timeline_findings,
        "blockers": blocker_findings,
        "recommendations": list(dict.fromkeys(recommendations))
    }


# --------------------------------------------------
# 5. OVERALL PROJECT HEALTH
# --------------------------------------------------

def calculate_project_health(project_text):
    """Calculate project health and return detailed assessment."""

    if not isinstance(project_text, str) or not project_text.strip():
        return {
            "overall_score": 0,
            "scope_score": 0,
            "timeline_score": 0,
            "blocker_score": 0,
            "status": "Insufficient Data",
            "assessment": {
                "scope": [],
                "timeline": [],
                "blockers": [],
                "recommendations": []
            }
        }

    # Run existing Milestone 2 agents
    scope = extract_scope_and_deliverables(project_text)
    risks = detect_project_risks(project_text)
    blockers = identify_blockers_and_actions(project_text)

    # Calculate dimension scores
    scope_score = calculate_scope_score(scope)
    timeline_score = calculate_timeline_score(risks)
    blocker_score = calculate_blocker_score(blockers)

    # Equal weighting across the three required dimensions
    overall_score = round(
        (scope_score + timeline_score + blocker_score) / 3
    )

    # Determine project status
    if overall_score >= 80:
        status = "Healthy"
    elif overall_score >= 60:
        status = "Moderate Risk"
    elif overall_score >= 40:
        status = "High Risk"
    else:
        status = "Critical"

    # Generate assessment
    assessment = build_project_assessment(
        scope,
        risks,
        blockers
    )

    return {
        "overall_score": overall_score,
        "scope_score": scope_score,
        "timeline_score": timeline_score,
        "blocker_score": blocker_score,
        "status": status,
        "assessment": assessment
    }
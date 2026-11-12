

from scope_agent import extract_scope_and_deliverables
from risk_agent import detect_project_risks
from blocker_agent import identify_blockers_and_actions


def generate_user_stories(project_text):
    """Generate user stories from identified project goals and deliverables."""

    scope = extract_scope_and_deliverables(project_text)

    stories = []

    for goal in scope.get("goals", []):
        stories.append(
            f"As a project stakeholder, I want {goal} "
            "so that the project objective can be achieved."
        )

    for deliverable in scope.get("deliverables", []):
        stories.append(
            f"As a user, I want {deliverable} "
            "so that I can use the project functionality."
        )

    return list(dict.fromkeys(stories))


def get_risk_mitigation(risk_type):
    """Return a mitigation recommendation based on the risk category."""

    mitigation_actions = {
        "Schedule Delay": (
            "Review the project schedule, identify delayed tasks, "
            "and revise deadlines or resource allocation."
        ),
        "Dependency Risk": (
            "Identify the dependent tasks, follow up with responsible "
            "stakeholders, and establish a dependency resolution plan."
        ),
        "Delivery Challenge": (
            "Review the delivery deadline, assess available resources, "
            "and prepare a corrective delivery plan."
        )
    }

    return mitigation_actions.get(
        risk_type,
        "Review the identified risk and prepare an appropriate mitigation plan."
    )


def generate_risk_register(project_text):
    """Generate a structured risk register from detected project risks."""

    detected_risks = detect_project_risks(project_text)

    risk_register = []

    for risk in detected_risks:
        risk_type = risk.get("risk_type", "Unknown")

        risk_register.append({
            "risk_type": risk_type,
            "description": risk.get(
                "evidence",
                "No supporting evidence available."
            ),
            "matched_keywords": risk.get("matched_keywords", []),
            "status": "Open",
            "mitigation": get_risk_mitigation(risk_type)
        })

    return risk_register


def generate_action_items(project_text):
    """Generate structured blockers, decisions, and action items."""

    results = identify_blockers_and_actions(project_text)

    return {
        "blockers": results.get("blockers", []),
        "pending_decisions": results.get("pending_decisions", []),
        "action_items": results.get("action_items", [])
    }


def generate_documentation(project_text):
    """Generate all project documentation sections."""

    empty_result = {
        "user_stories": [],
        "risk_register": [],
        "action_items": {
            "blockers": [],
            "pending_decisions": [],
            "action_items": []
        }
    }

    if not isinstance(project_text, str) or not project_text.strip():
        return empty_result

    return {
        "user_stories": generate_user_stories(project_text),
        "risk_register": generate_risk_register(project_text),
        "action_items": generate_action_items(project_text)
    }
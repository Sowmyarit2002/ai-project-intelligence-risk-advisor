"""
Unit tests for the five-dimensional health scoring and radar integration.

Run from the project folder:   python -m pytest tests -v
"""

import ast
import html
import json
import os
import re
import sys
import textwrap
import types

import pytest

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

# The Milestone 2 agents are replaced by stubs only if they are not
# importable (so the real ones are used inside the actual project).
for module_name, function_name in (
    ("scope_agent", "extract_scope_and_deliverables"),
    ("risk_agent", "detect_project_risks"),
    ("blocker_agent", "identify_blockers_and_actions"),
):
    try:
        __import__(module_name)
    except ImportError:
        stub = types.ModuleType(module_name)
        setattr(stub, function_name, lambda text: {})
        sys.modules[module_name] = stub

import health_score as hs  # noqa: E402


# --------------------------------------------------
# SCOPE SCORING
# --------------------------------------------------

def test_scope_score_full_partial_and_empty():
    full = {"goals": ["g"], "deliverables": ["d"], "milestones": ["m"]}
    assert hs.calculate_scope_score(full) == 100
    assert hs.calculate_scope_score({"goals": ["g"], "deliverables": ["d"]}) == 80
    assert hs.calculate_scope_score({"milestones": ["m"]}) == 20
    assert hs.calculate_scope_score({}) == 0


# --------------------------------------------------
# TIMELINE SCORING
# --------------------------------------------------

def test_timeline_score_penalties_and_floor():
    assert hs.calculate_timeline_score([]) == 100
    assert hs.calculate_timeline_score([{"risk_type": "Schedule Delay"}]) == 70
    assert hs.calculate_timeline_score([{"risk_type": "Dependency Risk"}]) == 85
    assert hs.calculate_timeline_score([{"risk_type": "Budget"}]) == 100
    assert hs.calculate_timeline_score(
        [{"risk_type": "Schedule Delay"}] * 5
    ) == 0


def test_schedule_evidence_detection():
    assert not hs.has_schedule_evidence({}, [])
    assert not hs.has_schedule_evidence({"goals": ["g"]}, [{"risk_type": "Budget"}])
    assert hs.has_schedule_evidence({"milestones": ["m"]}, [])
    assert hs.has_schedule_evidence({"timelines": ["t"]}, [])
    assert hs.has_schedule_evidence({}, [{"risk_type": "Schedule Delay"}])


# --------------------------------------------------
# BLOCKER SCORING
# --------------------------------------------------

def test_blocker_status_classification():
    assert hs.classify_item_status("Vendor API access is missing") == "open"
    assert hs.classify_item_status("Server migration is in progress") == "in_progress"
    assert hs.classify_item_status("Licence issue resolved last week") == "resolved"
    assert hs.classify_item_status("Issue not yet resolved") == "open"
    assert hs.classify_item_status({"text": "x", "status": "Resolved"}) == "resolved"


def test_blocker_score_depends_on_status():
    open_only = {"blockers": ["API access missing"]}
    in_progress = {"blockers": ["API access fix in progress"]}
    resolved = {"blockers": ["API access issue resolved"]}

    assert hs.calculate_blocker_score(open_only) == 80
    assert hs.calculate_blocker_score(in_progress) == 90
    assert hs.calculate_blocker_score(resolved) == 100


def test_blocker_score_pending_decisions_are_separate():
    data = {
        "blockers": ["API access missing"],
        "pending_decisions": ["Choose cloud vendor", "Approve budget"],
    }
    details = hs.calculate_blocker_details(data)

    assert details["blocker_penalty"] == 20
    assert details["decision_penalty"] == 20
    assert details["score"] == 60


def test_blocker_score_backward_compatible_and_floored():
    assert hs.calculate_blocker_score({}) == 100
    assert hs.calculate_blocker_score(
        {"blockers": ["a", "b", "c"], "pending_decisions": ["d"]}
    ) == 30
    assert hs.calculate_blocker_score({"blockers": ["x"] * 9}) == 0


# --------------------------------------------------
# RISK SCORING
# --------------------------------------------------

def test_risk_score_none_when_not_analyzed():
    assert hs.calculate_risk_score(None) is None
    assert hs.assess_risk_matrix(None) is None


def test_risk_score_no_risks_detected_is_full():
    assert hs.calculate_risk_score([]) == 100
    info = hs.assess_risk_matrix([])
    assert (info["likelihood"], info["impact"], info["score"]) == (1, 1, 1)
    assert info["level"] == "LOW"


def test_risk_score_uses_likelihood_and_impact_not_count():
    one_severe = [{
        "risk_id": "R1", "risk_type": "Budget",
        "likelihood": 5, "impact": 5, "status": "open",
    }]
    many_minor = [
        {"risk_id": f"R{i}", "risk_type": "Budget",
         "likelihood": 1, "impact": 1, "status": "open"}
        for i in range(5)
    ]

    assert hs.calculate_risk_score(one_severe) == 75
    assert hs.calculate_risk_score(many_minor) == 95
    assert hs.assess_risk_matrix(one_severe)["level"] == "CRITICAL"
    assert hs.assess_risk_matrix(many_minor)["level"] == "LOW"


def test_risk_score_mitigation_status_factor():
    base = {"risk_id": "R1", "risk_type": "Budget", "likelihood": 5, "impact": 5}

    open_score = hs.calculate_risk_score([{**base, "status": "open"}])
    progress = hs.calculate_risk_score([{**base, "status": "in progress"}])
    mitigated = hs.calculate_risk_score([{**base, "status": "mitigated"}])

    assert open_score < progress < mitigated
    assert open_score == 75
    assert mitigated == 98  # 100 - 25 * 0.1 = 97.5 -> 98


def test_mitigated_risk_does_not_drive_criticality():
    risks = [
        {"risk_id": "R1", "risk_type": "Budget", "likelihood": 5,
         "impact": 5, "status": "mitigated"},
        {"risk_id": "R2", "risk_type": "Budget", "likelihood": 2,
         "impact": 2, "status": "open"},
    ]
    info = hs.assess_risk_matrix(risks)

    assert info["score"] == 4
    assert info["level"] == "LOW"
    assert info["active_count"] == 1


def test_missing_risk_information_is_reported():
    risks = [{"risk_id": "R1", "risk_type": "Schedule Delay", "evidence": "x"}]
    info = hs.assess_risk_matrix(risks)

    assert info["estimated_count"] == 1
    assert (info["likelihood"], info["impact"]) == hs.RISK_TYPE_DEFAULTS["Schedule Delay"]
    joined = " ".join(info["missing_info"])
    assert "likelihood" in joined and "impact" in joined and "mitigation status" in joined


def test_risk_levels_accept_words():
    risks = [{"risk_id": "R1", "risk_type": "Budget",
              "likelihood": "high", "impact": "very high", "status": "open"}]
    info = hs.assess_risk_matrix(risks)

    assert (info["likelihood"], info["impact"]) == (4, 5)
    assert info["estimated_count"] == 0


def test_grouped_risk_records_are_split_and_deduplicated():
    grouped = [
        {"risk_type": "Schedule Delay",
         "evidence": "R1 — deadline slipping\nR2 — vendor late"},
        {"risk_type": "Schedule Delay", "evidence": "R1 — deadline slipping"},
    ]
    assert len(hs.normalize_risk_records(grouped)) == 2


# --------------------------------------------------
# QUALITY SCORING
# --------------------------------------------------

GOOD_TEXT = ("The project will deliver a reporting platform. " * 20).strip()


def test_quality_none_without_any_evidence():
    result = hs.evaluate_quality("", {})
    assert result["score"] is None
    assert hs.calculate_quality_score("", evidence={}) is None


def test_quality_document_check_only_is_limited_by_coverage():
    result = hs.evaluate_quality(GOOD_TEXT, {})
    names = [item["name"] for item in result["components"]]

    assert "Document text check" in names
    assert "Validation coverage" in names
    # Only 1 of 6 evidence categories exists: not 100 and not 0.
    assert 0 < result["score"] < 100
    assert "unit_tests" in result["missing_evidence"]


def test_quality_uses_recorded_validation_results():
    evidence = {
        "unit_tests": {"passed": 9, "failed": 1},
        "formats_tested": {"pdf": True, "docx": True, "csv": True, "txt": False},
        "extraction_validation": {"passed": 8, "total": 10},
        "retrieval_accuracy": {"correct": 7, "total": 10},
        "source_attribution": {"passed": 10, "total": 10},
    }
    result = hs.evaluate_quality(GOOD_TEXT, evidence)
    by_name = {item["name"]: item["score"] for item in result["components"]}

    assert by_name["Unit tests"] == 90
    assert by_name["Supported formats"] == 75
    assert by_name["Extraction validation"] == 80
    assert by_name["Retrieval accuracy"] == 70
    assert by_name["Source attribution"] == 100
    assert by_name["Validation coverage"] == 100
    assert result["missing_evidence"] == []
    assert 0 < result["score"] < 100


def test_quality_failing_tests_lower_the_score():
    passing = hs.evaluate_quality(GOOD_TEXT, {"unit_tests": {"passed": 10, "failed": 0}})
    failing = hs.evaluate_quality(GOOD_TEXT, {"unit_tests": {"passed": 2, "failed": 8}})

    assert failing["score"] < passing["score"]


def test_quality_ignores_invalid_evidence_instead_of_inventing_it():
    evidence = {
        "unit_tests": {"passed": 0, "failed": 0},
        "retrieval_accuracy": {"correct": 12, "total": 10},
        "formats_tested": {"xyz": True},
    }
    result = hs.evaluate_quality(GOOD_TEXT, evidence)
    names = [item["name"] for item in result["components"]]

    assert "Unit tests" not in names
    assert "Retrieval accuracy" not in names
    assert "Supported formats" not in names


def test_quality_accuracy_field_accepts_fraction_and_percent():
    a = hs.evaluate_quality(GOOD_TEXT, {"retrieval_accuracy": {"accuracy": 0.8}})
    b = hs.evaluate_quality(GOOD_TEXT, {"retrieval_accuracy": {"accuracy": 80}})
    pick = lambda r: next(i["score"] for i in r["components"] if i["name"] == "Retrieval accuracy")

    assert pick(a) == pick(b) == 80


def test_quality_garbled_text_scores_poorly():
    garbled = "�" * 400
    assert hs.evaluate_quality(garbled, {})["components"][0]["score"] < 20


def test_load_validation_evidence(tmp_path):
    missing, note = hs.load_validation_evidence(str(tmp_path / "none.json"))
    assert missing is None and "No validation results" in note

    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    assert hs.load_validation_evidence(str(bad))[0] is None

    good = tmp_path / "good.json"
    good.write_text(json.dumps({"unit_tests": {"passed": 1, "failed": 0}}))
    data, note = hs.load_validation_evidence(str(good))
    assert data["unit_tests"]["passed"] == 1 and note is None


# --------------------------------------------------
# OVERALL HEALTH
# --------------------------------------------------

@pytest.fixture
def patch_agents(monkeypatch, tmp_path):
    """Replace the Milestone 2 agents and isolate the validation file."""

    monkeypatch.setenv(hs.VALIDATION_RESULTS_ENV, str(tmp_path / "absent.json"))

    def apply(scope, risks, blockers):
        monkeypatch.setattr(hs, "extract_scope_and_deliverables", lambda text: scope)
        monkeypatch.setattr(hs, "detect_project_risks", lambda text: risks)
        monkeypatch.setattr(hs, "identify_blockers_and_actions", lambda text: blockers)

    return apply


def test_health_returns_all_five_dimensions(patch_agents):
    patch_agents(
        {"goals": ["g"], "deliverables": ["d"], "milestones": ["m"]},
        [],
        {"blockers": [], "pending_decisions": []},
    )
    health = hs.calculate_project_health(GOOD_TEXT)

    for key in (
        "overall_score", "scope_score", "timeline_score", "risk_score",
        "quality_score", "blocker_score", "status", "assessment",
    ):
        assert key in health

    for key in ("scope_score", "timeline_score", "risk_score",
                "quality_score", "blocker_score", "overall_score"):
        assert 0 <= health[key] <= 100


def test_overall_is_equal_weight_of_assessed_dimensions(patch_agents):
    patch_agents(
        {"goals": ["g"], "deliverables": ["d"], "milestones": ["m"]},
        [{"risk_id": "R1", "risk_type": "Schedule Delay",
          "likelihood": 4, "impact": 4, "status": "open"}],
        {"blockers": ["API access missing"], "pending_decisions": []},
    )
    health = hs.calculate_project_health(GOOD_TEXT)

    parts = [
        health["scope_score"], health["timeline_score"], health["risk_score"],
        health["quality_score"], health["blocker_score"],
    ]
    assert health["overall_score"] == round(sum(parts) / 5)
    assert health["scope_score"] == 100
    assert health["timeline_score"] == 70
    assert health["risk_score"] == 84   # 100 - 25 * 16/25
    assert health["blocker_score"] == 80


def test_unassessed_schedule_is_neutral_and_excluded(patch_agents):
    patch_agents(
        {"goals": ["g"], "deliverables": ["d"]},   # no milestones / timelines
        [],
        {"blockers": [], "pending_decisions": []},
    )
    health = hs.calculate_project_health(GOOD_TEXT)

    assert health["dimension_status"]["schedule"]["assessed"] is False
    assert health["timeline_score"] == hs.NEUTRAL_SCORE
    assert health["timeline_score"] not in (0, 100)

    assessed = [
        health[key] for key, name in (
            ("scope_score", "scope"), ("risk_score", "risk"),
            ("quality_score", "quality"), ("blocker_score", "blocker"),
        )
    ]
    assert health["overall_score"] == round(sum(assessed) / 4)
    assert any("Schedule" in gap for gap in health["data_gaps"])


def test_health_status_bands():
    assert hs._status_for(85) == "Healthy"
    assert hs._status_for(65) == "Moderate Risk"
    assert hs._status_for(45) == "High Risk"
    assert hs._status_for(10) == "Critical"


def test_empty_input_is_insufficient_data():
    for value in ("", "   ", None, 42):
        health = hs.calculate_project_health(value)
        assert health["status"] == "Insufficient Data"
        assert "risk_score" in health and "quality_score" in health


def test_assessment_contains_new_sections(patch_agents):
    patch_agents(
        {"goals": ["g"]},
        [{"risk_id": "R1", "risk_type": "Schedule Delay", "evidence": "late"}],
        {"blockers": ["API fix in progress"], "pending_decisions": ["Pick vendor"]},
    )
    assessment = hs.calculate_project_health(GOOD_TEXT)["assessment"]

    assert assessment["risk"] and assessment["quality"]
    assert any("in progress" in line for line in assessment["blockers"])
    assert any("likelihood" in line.lower() for line in assessment["recommendations"])


# --------------------------------------------------
# FIVE-DIMENSIONAL RADAR INTEGRATION (app.py helpers)
# --------------------------------------------------

APP_PATH = os.path.join(PROJECT_DIR, "app.py")
DASH_FUNCTIONS = (
    "esc", "dash_clamp", "dash_status_color", "dash_score_color",
    "dash_radar_svg", "dash_factor_list", "dash_radar_card",
)


@pytest.fixture(scope="module")
def dash():
    """Load the dashboard helper functions from app.py without Streamlit."""

    source = open(APP_PATH, encoding="utf-8").read()
    tree = ast.parse(source)
    namespace = {"html": html}

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in DASH_FUNCTIONS:
            code = textwrap.dedent(ast.get_source_segment(source, node))
            exec(code, namespace)

    missing = [name for name in DASH_FUNCTIONS if name not in namespace]
    assert not missing, f"Missing dashboard helpers: {missing}"
    return namespace


FIVE_FACTORS = [
    ("📅", "Schedule", 70, True),
    ("🎯", "Scope", 100, True),
    ("⚠️", "Risk", 84, True),
    ("✅", "Quality", 58, True),
    ("🚧", "Blockers", 80, True),
]


def test_radar_has_five_axes_and_labels(dash):
    svg = dash["dash_radar_svg"](
        [(label, value, assessed) for _, label, value, assessed in FIVE_FACTORS],
        "78",
    )

    for _, label, value, _ in FIVE_FACTORS:
        assert f">{label}</text>" in svg
        assert f">{value}/100</text>" in svg

    # one axis line per dimension + outer ring has five vertices
    assert len(re.findall(r'<line x1="230"', svg)) == 5
    outer_ring = re.findall(r'<polygon points="([^"]+)" fill="none"', svg)[-1]
    assert len(outer_ring.split()) == 5


def test_radar_labels_do_not_overlap(dash):
    svg = dash["dash_radar_svg"](
        [(label, value, assessed) for _, label, value, assessed in FIVE_FACTORS],
        "78",
    )

    boxes = []
    for match in re.finditer(
        r'<text x="([\d.]+)" y="([\d.]+)" text-anchor="(\w+)" '
        r'font-size="(1[12])"[^>]*>([^<]+)</text>', svg
    ):
        x, y, anchor, size, text = match.groups()
        x, y, size = float(x), float(y), float(size)
        width = len(text) * size * 0.6
        left = x - width / 2 if anchor == "middle" else x if anchor == "start" else x - width
        boxes.append((left, y - size, left + width, y + 2, text))

    assert len(boxes) == 10   # name + score line for each of five axes

    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            overlap = not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])
            assert not overlap, f"labels overlap: {a[4]} / {b[4]}"

    for left, top, right, bottom, text in boxes:
        assert 0 <= left and right <= 460 and 0 <= top and bottom <= 360, text


def test_radar_marks_unassessed_dimension(dash):
    factors = [
        ("📅", "Schedule", 50, False),
        ("🎯", "Scope", 100, True),
        ("⚠️", "Risk", 84, True),
        ("✅", "Quality", 58, True),
        ("🚧", "Blockers", 80, True),
    ]
    card = dash["dash_radar_card"](factors, "Healthy", 80)

    assert "no evidence" in card
    assert "(no evidence)" in card
    assert "Project Health Radar – Five Dimensions" in card


def test_radar_card_lists_all_five_scores(dash):
    card = dash["dash_radar_card"](FIVE_FACTORS, "Moderate Risk", 78)

    for _, label, value, _ in FIVE_FACTORS:
        assert label in card
        assert f"{value}/100" in card

    assert "Health score 78/100" in card


def test_radar_accepts_legacy_three_item_factors(dash):
    card = dash["dash_radar_card"](
        [("📅", "Schedule", 70), ("🎯", "Scope", 100), ("🚧", "Blockers", 80)],
        "Healthy", 83,
    )
    assert "Schedule" in card and "80/100" in card


def test_health_output_feeds_radar(patch_agents, dash):
    patch_agents(
        {"goals": ["g"], "deliverables": ["d"], "milestones": ["m"]},
        [{"risk_id": "R1", "risk_type": "Schedule Delay",
          "likelihood": 3, "impact": 3, "status": "open"}],
        {"blockers": ["API access missing"], "pending_decisions": []},
    )
    health = hs.calculate_project_health(GOOD_TEXT)

    factors = [
        ("📅", "Schedule", health["timeline_score"], True),
        ("🎯", "Scope", health["scope_score"], True),
        ("⚠️", "Risk", health["risk_score"], True),
        ("✅", "Quality", health["quality_score"], True),
        ("🚧", "Blockers", health["blocker_score"], True),
    ]
    card = dash["dash_radar_card"](factors, health["status"], health["overall_score"])

    for _, label, value, _ in factors:
        assert f"{value}/100" in card

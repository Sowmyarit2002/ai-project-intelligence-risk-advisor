from health_score import calculate_project_health


def test_project_health():

    sample_text = """
    Project Goal: Build an AI Project Intelligence Platform.
    Deliverable: Document Ingestion Module.
    Milestone 3: Complete documentation generation.
    The project is delayed by 3 days.
    Approval is pending for the project.
    Ravi must complete the testing task.
    """

    result = calculate_project_health(sample_text)

    assert 0 <= result["overall_score"] <= 100
    assert 0 <= result["scope_score"] <= 100
    assert 0 <= result["timeline_score"] <= 100
    assert 0 <= result["blocker_score"] <= 100

    assert result["status"] in [
        "Healthy",
        "Moderate Risk",
        "Critical"
    ]

    print("Project Health Scoring test passed!")
    print(result)


if __name__ == "__main__":
    test_project_health()
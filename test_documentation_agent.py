from documentation_agent import generate_documentation


def test_documentation_generation():

    sample_text = """
    Project Goal: Build an AI Project Intelligence Platform.
    Deliverable: Document Ingestion Module.
    Milestone 3: Complete documentation generation.
    The project is delayed by 3 days.
    Approval is pending for the project.
    Ravi must complete the testing task.
    """

    result = generate_documentation(sample_text)

    assert len(result["user_stories"]) > 0
    assert len(result["risk_register"]) > 0
    assert len(result["action_items"]["blockers"]) > 0
    assert len(result["action_items"]["pending_decisions"]) > 0
    assert len(result["action_items"]["action_items"]) > 0

    print("Documentation Agent test passed!")


if __name__ == "__main__":
    test_documentation_generation()
from conversational_agent import answer_project_question


def test_conversational_agent():

    question = "What are the project milestones?"

    result = answer_project_question(question)

    assert result["question"] == question
    assert isinstance(result["answer"], str)
    assert len(result["answer"]) > 0
    assert isinstance(result["sources"], list)

    print("Conversational Agent test passed!")
    print("\nQuestion:", result["question"])
    print("\nAnswer:", result["answer"])
    print("\nSources:", result["sources"])


def test_empty_question():

    result = answer_project_question("")

    assert result["sources"] == []
    assert "valid project question" in result["answer"]

    print("\nEmpty question test passed!")


if __name__ == "__main__":
    test_conversational_agent()
    test_empty_question()
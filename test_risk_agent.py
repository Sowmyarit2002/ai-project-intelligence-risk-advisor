from risk_agent import detect_project_risks

sample_text = """
Task A is delayed by three days.
Task B depends on Task A.
The project deadline may be at risk.
The team is waiting for pending approval.
"""

risks = detect_project_risks(sample_text)

for risk in risks:
    print(risk)
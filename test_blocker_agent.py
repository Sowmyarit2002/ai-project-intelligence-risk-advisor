from blocker_agent import identify_blockers_and_actions

sample_text = """
The login bug prevents completion of authentication testing.
Database integration is delayed.
Client approval is pending.
Backend developer: fix the login bug within two days.
QA tester: rerun authentication tests after the fix.
"""

results = identify_blockers_and_actions(sample_text)

print("BLOCKERS:")
for item in results["blockers"]:
    print("-", item)

print("\nPENDING DECISIONS:")
for item in results["pending_decisions"]:
    print("-", item)

print("\nACTION ITEMS:")
for item in results["action_items"]:
    print("-", item)

assert results["blockers"], "No blockers detected!"
assert results["pending_decisions"], "No pending decisions detected!"
assert results["action_items"], "No action items detected!"

print("\nAll three checks passed!")
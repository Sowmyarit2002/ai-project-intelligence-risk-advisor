def identify_blockers_and_actions(text):
    blockers = []
    action_items = []
    pending_decisions = []

    blocker_keywords = [
        "blocked", "blocker", "unresolved",
        "issue", "unable to proceed", "waiting for",
        "bug", "delayed", "delay", "dependency",
        "not available", "not completed", "prevents",
        "still pending", "configuration is pending"
    ]

    decision_keywords = [
        "pending decision", "decision pending",
        "awaiting approval", "pending approval",
        "approval is pending", "not been approved",
        "must decide", "decision"
    ]

    action_keywords = [
        "action item", "will complete", "must complete",
        "assigned to", "responsible for", "follow up",
        "fix", "complete", "obtain", "rerun",
        "review", "must", "should", "team:"
    ]

    for line in text.splitlines():
        clean = line.strip()

        if not clean:
            continue

        lower = clean.lower()

        if any(word in lower for word in blocker_keywords):
            blockers.append(clean)

        if any(word in lower for word in decision_keywords):
            pending_decisions.append(clean)

        if any(word in lower for word in action_keywords):
            action_items.append(clean)

    return {
        "blockers": list(dict.fromkeys(blockers)),
        "pending_decisions": list(dict.fromkeys(pending_decisions)),
        "action_items": list(dict.fromkeys(action_items))
    }
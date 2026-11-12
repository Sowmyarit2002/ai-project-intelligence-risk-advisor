

import re

from embedding import generate_embeddings
from vector_store import search_chunks, collection


# ==================================================
# CONFIGURATION
# ==================================================

DEFAULT_RESULTS = 40

RECORD_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])"
    r"(?P<record_id>[ABDMR]\d+)"
    r"\s*[-—–:]\s*",
    re.IGNORECASE
)

TEST_RECORD_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])T\d+\s*[-—–:]",
    re.IGNORECASE
)

SECTION_PATTERN = re.compile(
    r"\b(?:"
    r"RESPONSIBILITIES|"
    r"PROJECT STATUS|"
    r"RISKS|"
    r"BLOCKERS AND PENDING DECISIONS|"
    r"ACTION ITEMS|"
    r"ACCEPTANCE\s*/\s*MILESTONE\s*3\s*TESTS|"
    r"IMPORTANT DATE NOTE|"
    r"END OF TEST DOCUMENT"
    r")\b",
    re.IGNORECASE
)

STOP_WORDS = {
    "what", "is", "are", "the", "a", "an", "of", "to",
    "in", "on", "for", "and", "or", "who", "when",
    "where", "how", "which", "was", "were", "do",
    "does", "did", "about", "me", "please", "tell",
    "show", "give", "explain", "project"
}


# ==================================================
# TEXT HELPERS
# ==================================================

def clean_text(text):
    """Normalize text without removing useful project information."""

    if not text:
        return ""

    text = str(text)
    text = text.replace("\x00", " ")
    text = text.replace("\ufffd", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_question(question):
    """Normalize a user question."""

    return clean_text(question).lower()


def unique_items(items):
    """Remove duplicate strings while preserving order."""

    result = []
    seen = set()

    for item in items:

        item = clean_text(item)

        if not item:
            continue

        key = item.lower()

        if key not in seen:
            seen.add(key)
            result.append(item)

    return result


def merge_overlapping_text(previous, incoming, min_overlap=20):
    """
    Merge consecutive text chunks while removing repeated
    text at the boundary between them.
    """

    previous = clean_text(previous)
    incoming = clean_text(incoming)

    if not previous:
        return incoming

    if not incoming:
        return previous

    if incoming.lower() in previous.lower():
        return previous

    max_overlap = min(
        len(previous),
        len(incoming),
        2000
    )

    for size in range(max_overlap, min_overlap - 1, -1):

        if previous[-size:].lower() == incoming[:size].lower():

            return previous + incoming[size:]

    return previous + " " + incoming


def remove_section_tail(text):
    """Remove content belonging to the next major document section."""

    text = clean_text(text)

    match = SECTION_PATTERN.search(text)

    if match:
        text = clean_text(text[:match.start()])

    return text


# ==================================================
# QUESTION CLASSIFICATION
# ==================================================

def classify_issue(question):
    """Identify the main subject of a project question."""

    q = normalize_question(question)

    if any(word in q for word in [
        "deadline",
        "completion date",
        "finish date",
        "due date",
        "when will the project finish",
        "project completion",
        "overall completion",
    ]):
        return "deadline"

    if any(word in q for word in [
        "milestone",
        "milestones",
        "week 1",
        "week 2",
        "week 3",
        "week 4",
        "week 5",
        "week 6",
        "project timeline",
        "timeline",
    ]):
        return "milestone"

    if any(word in q for word in [
        "risk",
        "risks",
        "threat",
        "threats",
        "delivery challenge",
        "schedule delay",
        "dependency risk",
    ]):
        return "risk"

    if any(word in q for word in [
        "blocker",
        "blockers",
        "blocked",
        "obstacle",
        "obstacles",
        "pending decision",
        "pending approval",
    ]):
        return "blocker"

    if any(word in q for word in [
        "action item",
        "action items",
        "next step",
        "next steps",
        "what should",
        "what needs to be done",
        "tasks to complete",
    ]):
        return "action"

    if any(word in q for word in [
        "deliverable",
        "deliverables",
        "output",
        "outputs",
        "module",
        "modules",
    ]):
        return "deliverable"

    if any(word in q for word in [
        "responsible",
        "responsibility",
        "responsibilities",
        "owner",
        "owners",
        "assigned to",
    ]):
        return "responsibility"

    if any(word in q for word in [
        "goal",
        "goals",
        "objective",
        "objectives",
        "scope",
        "purpose",
    ]):
        return "scope"

    return "general"


# ==================================================
# RETRIEVAL
# ==================================================

def retrieve_project_context(
    question,
    n_results=DEFAULT_RESULTS,
    filename=None
):
    """
    Retrieve relevant project evidence.

    When a filename is selected, retrieve its stored chunks
    in their original order and merge overlapping text.

    Without a selected filename, use semantic search.
    """

    # --------------------------------------------------
    # DIRECT DOCUMENT RETRIEVAL
    # --------------------------------------------------

    if filename:

        try:

            results = collection.get(
                where={"filename": filename},
                include=["documents", "metadatas"]
            )

            documents = results.get("documents") or []
            metadatas = results.get("metadatas") or []

            chunks = []

            for index, document in enumerate(documents):

                if not document:
                    continue

                metadata = (
                    metadatas[index]
                    if index < len(metadatas)
                    else {}
                ) or {}

                chunk_index = metadata.get(
                    "chunk_index",
                    index
                )

                try:
                    chunk_index = int(chunk_index)
                except (TypeError, ValueError):
                    chunk_index = index

                chunks.append({
                    "content": document,
                    "filename": metadata.get(
                        "filename",
                        filename
                    ),
                    "chunk_index": chunk_index
                })

            # Restore original document order.
            chunks.sort(
                key=lambda item: item["chunk_index"]
            )

            if chunks:

                combined_content = ""

                for item in chunks:

                    combined_content = merge_overlapping_text(
                        combined_content,
                        item["content"]
                    )

                return [{
                    "content": combined_content,
                    "filename": filename
                }]

        except Exception:
            # Fall back to semantic retrieval.
            pass

    # --------------------------------------------------
    # SEMANTIC RETRIEVAL
    # --------------------------------------------------

    question_type = classify_issue(question)

    search_queries = [question]

    if question_type == "deadline":

        search_queries.extend([
            "M3 Milestone 3 project completion target",
            "Project final completion target and calendar deadline",
            "Milestone 3 target Week"
        ])

    elif question_type == "milestone":

        search_queries.extend([
            "M1 M2 M3 project milestone targets and timelines",
            "Milestone descriptions and target weeks"
        ])

    elif question_type == "risk":

        search_queries.extend([
            "R1 R2 R3 R4 R5 project risks and evidence",
            "Project schedule dependency delivery risks"
        ])

    elif question_type == "blocker":

        search_queries.extend([
            "B1 B2 B3 B4 B5 project blockers and pending decisions",
            "Project unresolved issues and approvals"
        ])

    elif question_type == "action":

        search_queries.extend([
            "A1 A2 A3 A4 A5 A6 A7 A8 project action items",
            "Project next steps owners and action status"
        ])

    elif question_type == "deliverable":

        search_queries.extend([
            "D1 D2 project deliverables and modules",
            "Project expected outputs and deliverables"
        ])

    search_queries = unique_items(search_queries)

    collected = []
    seen = set()

    for search_query in search_queries:

        try:

            embeddings = generate_embeddings([search_query])

            if embeddings is None or len(embeddings) == 0:
                continue

            results = search_chunks(
                embeddings[0],
                n_results=n_results,
                filename=filename
            )

            if not isinstance(results, dict):
                continue

            documents = results.get("documents") or [[]]
            metadatas = results.get("metadatas") or [[]]

            document_list = (
                documents[0] if documents else []
            )

            metadata_list = (
                metadatas[0] if metadatas else []
            )

            for index, document in enumerate(document_list):

                content = clean_text(document)

                if not content:
                    continue

                metadata = (
                    metadata_list[index]
                    if index < len(metadata_list)
                    else {}
                ) or {}

                source = metadata.get(
                    "filename",
                    filename or "Unknown document"
                )

                key = (content.lower(), source.lower())

                if key in seen:
                    continue

                seen.add(key)

                collected.append({
                    "content": content,
                    "filename": source
                })

        except Exception:
            # One unsuccessful search should not stop other searches.
            continue

    return collected


# ==================================================
# EVIDENCE EXTRACTION
# ==================================================

def extract_evidence_units(context):
    """
    Extract project records from retrieved chunks.

    Recognizes:
    M = milestones
    D = deliverables
    R = risks
    B = blockers
    A = action items

    Natural milestone headings are converted into M records.
    Test records beginning with T are excluded.
    """

    records = {}
    ordinary_evidence = []

    for item in context:

        content = clean_text(
            item.get("content", "")
        )

        filename = item.get(
            "filename",
            "Unknown document"
        )

        if not content:
            continue

        # Convert natural milestone headings into record IDs.
        # Example: "Milestone 3 —" becomes "M3 —".
        content = re.sub(
            r"\bMilestone\s+(\d+)\s*[—–:-]\s*",
            r"M\1 — ",
            content,
            flags=re.IGNORECASE
        )

        matches = list(
            RECORD_PATTERN.finditer(content)
        )

        if not matches:

            if not TEST_RECORD_PATTERN.search(content):

                ordinary_evidence.append({
                    "content": remove_section_tail(content),
                    "filename": filename,
                    "record_id": None
                })

            continue

        for index, match in enumerate(matches):

            record_id = match.group(
                "record_id"
            ).upper()

            start = match.end()

            if index + 1 < len(matches):
                end = matches[index + 1].start()
            else:
                end = len(content)

            record_content = clean_text(
                content[start:end]
            )

            # Prevent the current record from absorbing
            # the next major document section.
            record_content = remove_section_tail(
                record_content
            )

            if not record_content:
                continue

            if record_id.startswith("T"):
                continue

            # Store the first occurrence.
            if record_id not in records:

                records[record_id] = {
                    "content": record_content,
                    "filename": filename,
                    "record_id": record_id
                }

            else:

                old_content = records[record_id]["content"]

                records[record_id]["content"] = (
                    merge_overlapping_text(
                        old_content,
                        record_content
                    )
                )

    # Remove duplicate ordinary evidence.
    unique_ordinary = []
    seen_ordinary = set()

    for item in ordinary_evidence:

        content = clean_text(item["content"])

        if not content:
            continue

        key = (
            content.lower(),
            item["filename"].lower()
        )

        if key in seen_ordinary:
            continue

        seen_ordinary.add(key)

        item["content"] = content
        unique_ordinary.append(item)

    return list(records.values()) + unique_ordinary


# ==================================================
# RELEVANCE FILTERING
# ==================================================

def rank_relevant_sentences(question, evidence):
    """Rank evidence according to the question category."""

    question_type = classify_issue(question)

    ranked = []

    preferred_prefixes = {
        "deadline": ("M3",),
        "milestone": ("M",),
        "risk": ("R",),
        "blocker": ("B",),
        "action": ("A",),
        "deliverable": ("D",),
        "scope": ("D",),
        "responsibility": ("A", "M", "D")
    }

    preferred = preferred_prefixes.get(
        question_type,
        ()
    )

    for item in evidence:

        content = clean_text(
            item.get("content", "")
        )

        record_id = item.get("record_id")

        if not content:
            continue

        score = 0

        if record_id:

            if question_type == "deadline":

                if record_id == "M3":
                    score += 100

                elif record_id.startswith("M"):
                    score -= 30

            elif record_id.startswith(preferred):

                score += 50

            else:

                score -= 20

        lower_content = content.lower()

        if question_type == "deadline":

            if re.search(
                r"\b(target|completion|deadline)\b",
                lower_content
            ):
                score += 10

            if re.search(
                r"\bweek\s*\d+\b",
                lower_content
            ):
                score += 15

            if "calendar date" in lower_content:
                score += 5

        elif question_type == "milestone":

            if re.search(
                r"\bweek\s*\d+\b",
                lower_content
            ):
                score += 10

        elif question_type == "risk":

            if any(word in lower_content for word in [
                "delay", "dependency", "risk",
                "false positive", "false negative",
                "delivery", "approval"
            ]):
                score += 10

        elif question_type == "blocker":

            if any(word in lower_content for word in [
                "pending", "blocked", "open",
                "approval", "decision", "waiting"
            ]):
                score += 10

        elif question_type == "action":

            if any(word in lower_content for word in [
                "action", "owner", "status",
                "complete", "review", "test"
            ]):
                score += 10

        elif question_type == "deliverable":

            if any(word in lower_content for word in [
                "module", "deliverable", "output",
                "document", "search"
            ]):
                score += 10

        ranked.append((score, item))

    ranked.sort(
        key=lambda pair: pair[0],
        reverse=True
    )

    return [
        item
        for score, item in ranked
        if score > 0
    ]


# ==================================================
# ANSWER GENERATION
# ==================================================

def build_deadline_answer(evidence):
    """
    Answer the project completion question using M3 evidence.

    Earlier milestones and test-case expected answers are
    not used as substitutes for the final milestone record.
    """

    milestone_three = [
        item for item in evidence
        if item.get("record_id") == "M3"
    ]

    if not milestone_three:

        return (
            "I could not find the actual Milestone 3 record "
            "in the retrieved project evidence. "
            "Please verify the source document."
        ), []

    selected = milestone_three[0]

    content = selected["content"]

    week_match = re.search(
        r"\b(?:target\s*:\s*)?week\s*(\d+)\b",
        content,
        re.IGNORECASE
    )

    if week_match:

        week = week_match.group(1)

        answer = (
            f"The project completion target is Week {week} "
            "(Milestone 3). The document does not specify "
            "an exact calendar deadline."
        )

    else:

        answer = (
            "Milestone 3 is the final project milestone, "
            "but its exact target week could not be confirmed "
            "from the retrieved evidence. The document does "
            "not establish an exact calendar deadline."
        )

    return answer, [selected]


def build_category_answer(question_type, evidence):
    """Generate a concise answer from category-specific records."""

    if question_type == "deadline":
        return build_deadline_answer(evidence)

    if question_type == "milestone":

        selected = [
            item for item in evidence
            if (item.get("record_id") or "").startswith("M")
        ]

        if not selected:

            return (
                "No milestone records were found in the "
                "retrieved project evidence."
            ), []

        answer_lines = []

        for item in selected:

            record_id = item["record_id"]

            answer_lines.append(
                f"{record_id} — {item['content']}"
            )

        return (
            "The project milestones identified in the document are:\n\n"
            + "\n".join(
                f"• {line}" for line in answer_lines
            )
        ), selected

    if question_type == "risk":

        selected = [
            item for item in evidence
            if (item.get("record_id") or "").startswith("R")
        ]

        if not selected:

            return (
                "No explicit risk records were found in the "
                "retrieved project evidence."
            ), []

        answer = "The identified project risks are:\n\n"

        answer += "\n".join(
            f"• {item['record_id']} — {item['content']}"
            for item in selected
        )

        return answer, selected

    if question_type == "blocker":

        selected = [
            item for item in evidence
            if (item.get("record_id") or "").startswith("B")
        ]

        if not selected:

            return (
                "No explicit blocker records were found in the "
                "retrieved project evidence."
            ), []

        answer = "The identified blockers and pending issues are:\n\n"

        answer += "\n".join(
            f"• {item['record_id']} — {item['content']}"
            for item in selected
        )

        return answer, selected

    if question_type == "action":

        selected = [
            item for item in evidence
            if (item.get("record_id") or "").startswith("A")
        ]

        if not selected:

            return (
                "No explicit action-item records were found in "
                "the retrieved project evidence."
            ), []

        answer = "The identified project action items are:\n\n"

        answer += "\n".join(
            f"• {item['record_id']} — {item['content']}"
            for item in selected
        )

        return answer, selected

    if question_type == "deliverable":

        selected = [
            item for item in evidence
            if (item.get("record_id") or "").startswith("D")
        ]

        if not selected:

            return (
                "No explicit deliverable records were found in "
                "the retrieved project evidence."
            ), []

        answer = "The project deliverables are:\n\n"

        answer += "\n".join(
            f"• {item['record_id']} — {item['content']}"
            for item in selected
        )

        return answer, selected

    if question_type == "scope":

        selected = [
            item for item in evidence
            if (item.get("record_id") or "").startswith("D")
        ]

        if not selected:
            selected = evidence[:5]

        if not selected:

            return (
                "I could not find sufficient evidence about "
                "the project scope."
            ), []

        answer = "The available project scope evidence is:\n\n"

        answer += "\n".join(
            f"• {item['content']}"
            for item in selected
        )

        return answer, selected

    if question_type == "responsibility":

        selected = [
            item for item in evidence
            if any(
                word in item["content"].lower()
                for word in [
                    "responsible", "owner", "assigned"
                ]
            )
        ]

        if not selected:

            return (
                "I could not find a clear responsibility assignment "
                "in the retrieved evidence."
            ), []

        answer = "The responsibility information found is:\n\n"

        answer += "\n".join(
            f"• {item['content']}"
            for item in selected
        )

        return answer, selected

    # General questions.
    selected = evidence[:5]

    if not selected:

        return (
            "I could not find relevant supporting information "
            "in the selected project document."
        ), []

    answer = "Based on the selected project document:\n\n"

    answer += "\n".join(
        f"• {item['content']}"
        for item in selected
    )

    return answer, selected


# ==================================================
# MAIN PROJECT QUESTION ANSWER FUNCTION
# ==================================================

def answer_project_question(
    question,
    n_results=3,
    filename=None
):
    """
    Answer a project question using document-grounded retrieval.

    Returns:
        question: Original question
        answer: Generated answer
        sources: Source document names
        evidence: Supporting evidence dictionaries
    """

    question = clean_text(question)

    if not question:

        return {
            "question": question,
            "answer": "Please enter a question.",
            "sources": [],
            "evidence": []
        }

    try:

        question_type = classify_issue(question)

        # Retrieve more candidates than the final display count.
        retrieval_count = max(
            DEFAULT_RESULTS,
            n_results
        )

        context = retrieve_project_context(
            question,
            n_results=retrieval_count,
            filename=filename
        )

        if not context:

            return {
                "question": question,
                "answer": (
                    "I could not find relevant information in the "
                    "selected project document. Please check that "
                    "the document has been processed and indexed."
                ),
                "sources": [],
                "evidence": []
            }

        evidence_units = extract_evidence_units(context)

        ranked_evidence = rank_relevant_sentences(
            question,
            evidence_units
        )

        answer, selected_evidence = build_category_answer(
            question_type,
            ranked_evidence
        )

        sources = unique_items([
            item.get(
                "filename",
                "Unknown document"
            )
            for item in selected_evidence
        ])

        # Limit evidence shown in the interface.
        selected_evidence = selected_evidence[:10]

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "evidence": selected_evidence
        }

    except Exception as error:

        return {
            "question": question,
            "answer": (
                "An error occurred while answering the question: "
                + str(error)
            ),
            "sources": [],
            "evidence": []
        }
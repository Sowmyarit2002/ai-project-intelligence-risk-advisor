from scope_agent import extract_scope_and_deliverables

sample_text = """
Project Goal: Build an AI Project Intelligence Platform.
Milestone 2 should be completed by 30 November 2026.
Feature: Document Ingestion Module.
Module: Semantic Search.
Assigned to Ravi.
"""

result = extract_scope_and_deliverables(sample_text)

print(result)
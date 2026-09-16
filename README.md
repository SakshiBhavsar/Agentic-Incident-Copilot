# Agentic Incident Copilot

An agentic incident-response control plane: RAG-grounded root-cause diagnosis + confidence-aware remediation.

When an incident fires, an agent retrieves relevant context (runbooks, past incidents, logs) via RAG, proposes a root cause, and if it's confident enough, takes a bounded remediation action (retry / restart / rollback) on its own. Anything low-confidence or high-risk gets escalated to a human instead of acted on automatically.

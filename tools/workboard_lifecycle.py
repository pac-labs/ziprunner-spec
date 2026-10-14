"""Illustrative, dependency-free workboard *projection* contract.

This is not integrated with ZipRunner. Inputs `trusted_review` and `artifact_hash`
MUST be obtained/authorized by the application, not from the update ZIP.
Persist the board and event journal transactionally in the actual application.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any


class WorkboardLifecycleError(ValueError):
    """Conflicting or unauthorized task transition."""


def import_built_source(
    board: dict[str, dict[str, Any]],
    source_update: dict,
    *,
    artifact_hash: str,
    build_succeeded: bool,
    imported_hashes: set[str],
) -> tuple[dict[str, dict[str, Any]], set[str], dict[str, int]]:
    """Project v1 reported changes by original IDs; never self-approve Done.

    Caller must validate the ZIP/JSON and verify artifact_hash from actual bytes.
    Returns copies; on build failure it changes no durable workboard records.
    """
    result = deepcopy(board)
    hashes = set(imported_hashes)
    counts = {"created": 0, "updated": 0, "closed": 0, "blocked": 0, "awaiting_verification": 0}
    if not build_succeeded or artifact_hash in hashes:
        return result, hashes, counts
    ids = [x["id"] for key in ("implemented", "remaining") for x in source_update[key]]
    if len(ids) != len(set(ids)):
        raise WorkboardLifecycleError("duplicate work item IDs")
    # Prepare all mutations before committing this projection.
    for row in source_update["remaining"]:
        key = row["id"]
        old = result.get(key)
        if old and old.get("status") == "done":
            raise WorkboardLifecycleError(f"cannot silently reopen previously verified Done task: {key}")
        if old is None:
            result[key] = {"id": key, "title": row["title"], "status": "todo", "notes": [row["summary"]], "acceptance_criteria": []}
            counts["created"] += 1
        else:
            old.setdefault("notes", []).append(row["summary"])
            counts["updated"] += 1
    for row in source_update["implemented"]:
        key = row["id"]
        old = result.get(key)
        if old is None:
            result[key] = {"id": key, "title": row["title"], "status": "awaiting_verification", "acceptance_criteria": [], "notes": []}
            old = result[key]
            counts["created"] += 1
        else:
            counts["updated"] += 1
            # Never downgrade a task already independently verified.
            if old.get("status") != "done":
                old["status"] = "awaiting_verification"
        old.setdefault("reported_implementations", []).append({
            "sha256": artifact_hash, "version": source_update["version"],
            "summary": row["summary"], "operator_checks": list(row["operator_checks"])
        })
        if old["status"] == "awaiting_verification":
            counts["awaiting_verification"] += 1
    hashes.add(artifact_hash)
    return result, hashes, counts


def apply_trusted_review(
    board: dict[str, dict[str, Any]],
    task_id: str,
    review: dict,
    *,
    authorized: bool,
) -> dict[str, dict[str, Any]]:
    """Close original ID only on independently authorized QA/operator acceptance.

    The application MUST authenticate reviewers, bind evidence to real test results,
    and record immutable review event/timestamp outside source ZIPs.
    """
    if not authorized:
        raise WorkboardLifecycleError("unauthorized review")
    if task_id not in board:
        raise WorkboardLifecycleError(f"unknown original work item: {task_id}")
    new_board = deepcopy(board)
    task = new_board[task_id]
    if review.get("qa_approved") is True and review.get("operator_verified") is True and review.get("acceptance_criteria_passed") is True:
        evidence = review.get("evidence")
        if not isinstance(evidence, list) or not evidence or any(not isinstance(e, str) or not e.strip() for e in evidence):
            raise WorkboardLifecycleError("verified Done requires evidence")
        if not review.get("actor") or not review.get("timestamp"):
            raise WorkboardLifecycleError("verified Done requires reviewer and timestamp")
        task["status"] = "done"
        task["verified_review"] = deepcopy(review)
    elif review.get("blocked") is True:
        if not (review.get("reason") and review.get("unblock_when")):
            raise WorkboardLifecycleError("Blocked requires reason and unblock condition")
        if task.get("status") == "done":
            raise WorkboardLifecycleError("cannot reopen previously verified Done")
        task["status"] = "blocked"
        task["blocker"] = {"reason": review["reason"], "unblock_when": review["unblock_when"]}
    elif task.get("status") != "done":
        task["status"] = "in_progress"
        task["outstanding_criteria"] = list(review.get("outstanding_criteria", []))
    return new_board


def release_readiness_errors(board: dict[str, dict[str, Any]], release_task_ids: set[str]) -> list[str]:
    """Scope to functionality represented as delivered in this release."""
    errors = []
    for task_id in sorted(release_task_ids):
        task = board.get(task_id)
        if not task:
            errors.append(f"{task_id}: missing task identity in workboard")
        elif task.get("status") != "done":
            errors.append(f"{task_id}: delivered task unresolved ({task.get('status', 'unknown')})")
        elif not task.get("verified_review"):
            errors.append(f"{task_id}: Done without independent verification evidence")
    # Also surface verified-but-not-closed projection inconsistencies.
    for task_id, task in board.items():
        if task.get("verified_review") and task.get("status") != "done":
            errors.append(f"{task_id}: verified task has not transitioned to Done")
    return errors

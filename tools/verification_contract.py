"""Portable, non-executing functional-verification and feedback reference checks.

Validation cannot certify a real function, invoke a trusted project runner, grant QA
approval, or send browser messages. Those are separate consumer responsibilities.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MAX_PLAN = 262_144


def errors_for_schema(doc: dict, name: str) -> list[str]:
    from validate import validate_schema_subset
    schema = json.loads((ROOT / 'schemas' / name).read_text(encoding='utf-8'))
    return validate_schema_subset(doc, schema)


def parse_plan_bytes(data: bytes) -> dict:
    if len(data) > MAX_PLAN:
        raise ValueError('verification plan larger than 256 KiB')
    def unique_pairs(pairs):
        result = {}
        for k, v in pairs:
            if k in result:
                raise ValueError('duplicate verification-plan JSON key: ' + k)
            result[k] = v
        return result
    def bad_constant(value):
        raise ValueError('nonstandard JSON constant: ' + value)
    try:
        obj = json.loads(data.decode('utf-8-sig'), object_pairs_hook=unique_pairs, parse_constant=bad_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError('verification plan must be UTF-8 JSON: ' + str(exc)) from exc
    if not isinstance(obj, dict):
        raise ValueError('verification plan must be a JSON object')
    return obj


def _duplicates(values):
    return len(values) != len(set(values))


def validate_plan(plan: dict, workboard: dict | None = None, *, project: str | None = None,
                  version: str | None = None, available: set[str] | None = None) -> list[str]:
    """Check schema and source-package task/criterion/check alignment.

    This cannot compare against historical trusted criteria without consumer data.
    """
    errors = errors_for_schema(plan, 'verification-plan.schema.json')
    if project is not None and plan.get('project') != project:
        errors.append('verification plan project does not match target: ' + str(project))
    if version is not None and plan.get('version') != version:
        errors.append('verification plan version does not match delivered version')
    tasks = plan.get('tasks', [])
    checks = plan.get('checks', [])
    if not isinstance(tasks, list) or not isinstance(checks, list):
        return errors
    task_ids = [r.get('id') for r in tasks if isinstance(r, dict) and isinstance(r.get('id'), str)]
    check_ids = [r.get('id') for r in checks if isinstance(r, dict) and isinstance(r.get('id'), str)]
    if _duplicates(task_ids):
        errors.append('duplicate task IDs in verification plan')
    if _duplicates(check_ids):
        errors.append('duplicate check IDs in verification plan')
    check_map = {r['id']: r for r in checks if isinstance(r, dict) and isinstance(r.get('id'), str)}
    used = set()
    for task in tasks:
        if not isinstance(task, dict):
            continue
        criteria = task.get('criteria', [])
        if not isinstance(criteria, list):
            continue
        cids = [x.get('id') for x in criteria if isinstance(x, dict) and isinstance(x.get('id'), str)]
        if _duplicates(cids):
            errors.append(f'{task.get("id")}: duplicate criterion IDs')
        for criterion in criteria:
            if not isinstance(criterion, dict):
                continue
            ref_ids = criterion.get('checks', [])
            if not isinstance(ref_ids, list):
                continue
            if len(ref_ids) != len(set(x for x in ref_ids if isinstance(x, str))):
                errors.append(f'{task.get("id")}/{criterion.get("id")}: duplicate linked checks')
            kinds = set()
            for ref in ref_ids:
                if ref not in check_map:
                    errors.append(f'{task.get("id")}: missing declared check {ref!r}')
                    continue
                used.add(ref)
                kinds.add(check_map[ref].get('kind'))
            expected = {'automated': {'automated'}, 'manual': {'manual'}, 'mixed': {'automated', 'manual'}}.get(criterion.get('mode'))
            if expected is not None and not expected <= kinds:
                errors.append(f'{task.get("id")}/{criterion.get("id")}: missing {sorted(expected-kinds)} check coverage')
            if expected is not None and kinds - expected:
                errors.append(f'{task.get("id")}/{criterion.get("id")}: mode does not match linked check kinds')
    for row in checks:
        if not isinstance(row, dict):
            continue
        cid = row.get('id')
        if row.get('kind') == 'automated':
            if not isinstance(row.get('runner_ref'), str) or not row['runner_ref'].strip():
                errors.append(f'{cid}: automated check missing trusted runner_ref')
            if not isinstance(row.get('assertions'), list) or not row['assertions']:
                errors.append(f'{cid}: automated check must state feature assertions')
            from validate import archive_path_error
            ref = row.get('test_ref')
            if not isinstance(ref, str) or archive_path_error(ref):
                errors.append(f'{cid}: automated check requires a safe relative test_ref')
            elif available is not None and ref not in available:
                errors.append(f'{cid}: referenced test implementation missing from package: {ref}')
            if 'instructions' in row:
                errors.append(f'{cid}: automated check must not embed manual instructions')
        elif row.get('kind') == 'manual':
            if not isinstance(row.get('instructions'), str) or not row['instructions'].strip():
                errors.append(f'{cid}: manual check missing instructions')
            if 'runner_ref' in row or 'assertions' in row or 'test_ref' in row:
                errors.append(f'{cid}: manual check must not configure executable runners')
        if cid not in used:
            errors.append(f'{cid}: unlinked verification check')
    if workboard is not None:
        if workboard.get('project') != plan.get('project') or workboard.get('version') != plan.get('version'):
            errors.append('verification plan and mandatory workboard identity/version disagree')
        implemented = workboard.get('implemented', [])
        remaining = workboard.get('remaining', [])
        a = {r['id'] for r in implemented if isinstance(r, dict) and isinstance(r.get('id'), str)} if isinstance(implemented, list) else set()
        b = {r['id'] for r in remaining if isinstance(r, dict) and isinstance(r.get('id'), str)} if isinstance(remaining, list) else set()
        if set(task_ids) != a:
            errors.append(f'verification task IDs must equal delivered implemented IDs (missing={sorted(a-set(task_ids))}, extra={sorted(set(task_ids)-a)})')
        if set(task_ids) & b:
            errors.append('unfinished work must not be described as delivered in the verification plan')
    return errors


def validate_report(report: dict, plan: dict, *, artifact_sha256: str, plan_sha256: str | None = None) -> list[str]:
    """Check report consistency. Caller must establish consumer provenance separately."""
    errors = errors_for_schema(report, 'verification-report.schema.json')
    if report.get('project') != plan.get('project') or report.get('version') != plan.get('version'):
        errors.append('verification report and plan project/version disagree')
    if report.get('artifact_sha256') != artifact_sha256:
        errors.append('stale or mismatched artifact hash in verification report')
    if plan_sha256 is not None and report.get('plan_sha256') != plan_sha256:
        errors.append('mismatched verification plan digest')
    actual = report.get('checks', [])
    if not isinstance(actual, list):
        return errors
    results = {r.get('id'): r for r in actual if isinstance(r, dict) and isinstance(r.get('id'), str)}
    check_refs = {r.get('id') for r in plan.get('checks', []) if isinstance(r, dict)}
    if len(actual) != len(results) or set(results) != check_refs:
        errors.append('report must have exactly one outcome for every declared check')
    declared = {x['id']: x for x in plan.get('checks', []) if isinstance(x, dict) and isinstance(x.get('id'), str)}
    build = report.get('build', {})
    build_passed = isinstance(build, dict) and build.get('status') == 'passed'
    for cid, row in results.items():
        if row.get('status') == 'passed':
            if not build_passed:
                errors.append(f'{cid}: cannot pass with failed, blocked or missing build')
            if row.get('provenance') not in ('consumer_observed', 'operator_observed'):
                errors.append(f'{cid}: producer report cannot prove passing functionality')
            if not isinstance(row.get('evidence'), list) or not row['evidence']:
                errors.append(f'{cid}: passed check requires observed evidence and digest')
            if declared.get(cid, {}).get('kind') == 'automated':
                if row.get('provenance') != 'consumer_observed':
                    errors.append(f'{cid}: automated check must be consumer-observed')
                if row.get('runner_ref') != declared[cid].get('runner_ref'):
                    errors.append(f'{cid}: observed runner does not match trusted runner reference')
            if declared.get(cid, {}).get('kind') == 'manual' and row.get('provenance') != 'operator_observed':
                errors.append(f'{cid}: passed manual check must be operator-observed')
        if row.get('status') in ('failed', 'blocked', 'not_run') and not isinstance(row.get('reason'), str):
            errors.append(f'{cid}: unresolved check must document reason')
    return errors


def covered_task_ids(plan: dict, report: dict) -> set[str]:
    """Candidate IDs with every declared check passed; NEVER an approval to close."""
    if report.get('build', {}).get('status') != 'passed':
        return set()
    results = {r.get('id'): r for r in report.get('checks', []) if isinstance(r, dict)}
    covered = set()
    for task in plan.get('tasks', []):
        if not isinstance(task, dict):
            continue
        criteria = task.get('criteria', [])
        if criteria and all(all(results.get(cid, {}).get('status') == 'passed' and results[cid].get('evidence') and results[cid].get('provenance') in ('consumer_observed', 'operator_observed') for cid in item['checks']) for item in criteria):
            covered.add(task['id'])
    return covered


def validate_feedback(envelope: dict, report: dict, *, trusted_request_id: str | None = None) -> list[str]:
    errors = errors_for_schema(envelope, 'origin-feedback.schema.json')
    for key in ('run_id', 'project', 'version', 'artifact_sha256'):
        if envelope.get(key) != report.get(key):
            errors.append(f'feedback {key} mismatches observed report')
    if trusted_request_id is not None and envelope.get('origin_request_id') != trusted_request_id:
        errors.append('feedback origin request does not match trusted intake')
    states = envelope.get('delivery', {})
    if isinstance(states, dict) and states.get('state') in ('queued', 'submitted', 'acknowledged') and envelope.get('destination_binding') != 'verified':
        errors.append('unverified origin cannot be queued, submitted or acknowledged')
    if isinstance(states, dict) and states.get('state') == 'acknowledged' and not states.get('acknowledged_at'):
        errors.append('acknowledged requires acknowledgement timestamp')
    return errors


def feedback_id(run_id: str, request_id: str, report_sha256: str) -> str:
    """Deterministic idempotency key; binding verification still required."""
    return 'ZRMSG-' + hashlib.sha256((run_id + '\x00' + request_id + '\x00' + report_sha256).encode('utf-8')).hexdigest()[:40]


def delivery_transition(state: str, event: str, *, origin_verified: bool, acknowledged: bool = False) -> str:
    """Pure reference transport state; never transmits messages."""
    if event == 'bind_failed':
        return 'waiting_for_origin'
    if event == 'retry' and state in ('retryable_failure', 'waiting_for_origin'):
        return 'queued' if origin_verified else 'waiting_for_origin'
    if event == 'submit' and state == 'queued' and origin_verified:
        return 'submitted'
    if event == 'ack' and state == 'submitted' and acknowledged and origin_verified:
        return 'acknowledged'
    if event == 'error' and state in ('queued', 'submitted'):
        return 'retryable_failure'
    if event == 'block':
        return 'blocked'
    return state

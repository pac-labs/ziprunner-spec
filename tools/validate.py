#!/usr/bin/env python3
"""Independent ZipRunner spec v2 validator. Stdlib only; never extracts or executes a ZIP.

Usage:
  python tools/validate.py manifest examples/ziprunner-manifest.json --root examples
  python tools/validate.py workboard examples/ziprunner-workboard-update.example.json --expected-project example-project
  python tools/validate.py package update.zip --expected-project my-project
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import stat
import sys
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit

SCHEMA = 'ziprunner.update-manifest/v1'
WORKBOARD_SCHEMA = 'ziprunner.workboard-update.v1'
WORKBOARD_ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.:-]{0,119}$')
HEX64 = re.compile(r'^[a-fA-F0-9]{64}$')
IDENT = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{1,127}$')
VERSION = re.compile(r'^1\.[0-9]+\.[0-9]+$')
UNSAFE_WIN = re.compile(r'[<>:"|?*\x00-\x1f]')
RESERVED = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}
MAX_ENTRIES = 20000
MAX_UNPACKED = 4 * 1024**3
MAX_FILE = 2 * 1024**3
MAX_MANIFEST = 256 * 1024
MAX_RATIO = 1000


def load_json(text: str, label: str) -> dict:
    try:
        data = json.loads(text)
    except (ValueError, UnicodeError) as exc:
        raise ValueError(f'{label}: invalid UTF-8 JSON: {exc}') from exc
    if not isinstance(data, dict):
        raise ValueError(f'{label}: expected JSON object')
    return data


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict:
    """A duplicate key would make package interpretation parser-dependent."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def read_workboard_bytes(raw: bytes, label: str = '.ziprunner-workboard-update.json') -> dict:
    """Strict UTF-8, bounded parser for an untrusted root-level Work board file."""
    if len(raw) > MAX_MANIFEST:
        raise ValueError(f'{label}: size exceeds 256 KiB')
    try:
        parsed = json.loads(raw.decode('utf-8', errors='strict'), object_pairs_hook=_unique_pairs)
    except (UnicodeError, ValueError) as exc:
        raise ValueError(f'{label}: invalid UTF-8 JSON: {exc}') from exc
    if not isinstance(parsed, dict):
        raise ValueError(f'{label}: expected object')
    return parsed


def validate_workboard(board: dict, expected_project: str | None = None,
                       expected_version: str | None = None) -> list[str]:
    """Standalone shape and cross-item validation; does not assert ZipRunner parser parity."""
    schema_file = Path(__file__).resolve().parents[1] / 'schemas' / 'ziprunner-workboard-update.schema.json'
    schema = load_json(schema_file.read_text(encoding='utf-8'), str(schema_file))
    errors = validate_schema_subset(board, schema)
    if board.get('schema') != WORKBOARD_SCHEMA:
        errors.append(f'workboard schema must be exactly {WORKBOARD_SCHEMA}')
    if expected_project and str(board.get('project', '')).casefold() != expected_project.casefold():
        errors.append(f'workboard project mismatch: expected {expected_project}, got {board.get("project")!r}')
    if expected_version and board.get('version') != expected_version:
        errors.append(f'workboard version mismatch: expected {expected_version}, got {board.get("version")!r}')
    for field, limit in [('project', 120), ('version', 100), ('summary', 4000)]:
        val = board.get(field)
        if not isinstance(val, str) or not val.strip() or len(val) > limit:
            errors.append(f'workboard {field}: nonblank text of at most {limit} characters required')
    # The authoritative JSON Schema uses allOf/$ref for items. This stdlib
    # subset validator supplies their constraints explicitly here.
    seen = set()
    for section in ('implemented', 'remaining'):
        items = board.get(section, [])
        if not isinstance(items, list):
            continue
        if len(items) > 150:
            errors.append(f'workboard {section}: too many items (150 maximum)')
        for pos, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            ident = item.get('id')
            if not isinstance(ident, str) or not WORKBOARD_ID.fullmatch(ident):
                errors.append(f'workboard {section}[{pos}]: invalid task id')
                continue
            if ident in seen:
                errors.append(f'workboard duplicate task id across implemented/remaining: {ident}')
            seen.add(ident)
            for field, limit in (('title', 240), ('summary', 2000)):
                val = item.get(field)
                if not isinstance(val, str) or not val.strip() or len(val) > limit:
                    errors.append(f'workboard {section}[{pos}].{field}: nonblank max {limit} required')
            if section == 'implemented':
                checks = item.get('operator_checks')
                if not isinstance(checks, list) or not 1 <= len(checks) <= 20:
                    errors.append(f'workboard implemented[{pos}]: 1-20 operator_checks required')
                elif any(not isinstance(c, str) or not c.strip() or len(c) > 500 for c in checks):
                    errors.append(f'workboard implemented[{pos}]: invalid operator_checks text')
            elif item.get('priority', 'medium') not in ('critical', 'high', 'medium', 'low'):
                errors.append(f'workboard remaining[{pos}]: invalid priority')
    return errors


def archive_path_error(name: str) -> str | None:
    """Strict portable member names; no local filesystem accesses."""
    if not isinstance(name, str) or not name or len(name) > 1024:
        return 'empty or overly long path'
    if '\\' in name or name.startswith('/') or name.startswith('//'):
        return 'absolute or backslash path'
    if name.endswith('/'):
        name = name[:-1]
    if not name:
        return 'empty path'
    parts = name.split('/')
    if any(p in ('', '.', '..') for p in parts):
        return 'empty, dot or traversal component'
    for part in parts:
        if UNSAFE_WIN.search(part):
            return 'Windows-unsafe path component'
        if part.endswith(('.', ' ')):
            return 'trailing dot or whitespace'
        if part.split('.')[0].upper() in RESERVED:
            return 'reserved Windows device name'
    if len(name) > 240:
        return 'portable path length limit exceeded'
    return None


def local_reference_error(ref: str, available: set[str] | None) -> str | None:
    if not isinstance(ref, str) or not ref:
        return 'missing reference'
    u = urlsplit(ref)
    if u.scheme:
        if u.scheme != 'https' or not u.netloc or u.username or u.password:
            return 'external evidence must use HTTPS without credentials'
        return None
    reason = archive_path_error(ref)
    if reason:
        return reason
    if available is not None and ref not in available:
        return 'referenced evidence file not present in package/root'
    return None


def validate_schema_subset(value: Any, schema: dict, where: str = '$') -> list[str]:
    """Enforce the JSON Schema keywords used by the bundled contract, using stdlib."""
    errors: list[str] = []
    typ = schema.get('type')
    allowed = [typ] if isinstance(typ, str) else (typ or [])
    test_type = {
        'object': lambda v: isinstance(v,dict),
        'array': lambda v: isinstance(v,list),
        'string': lambda v: isinstance(v,str),
        'integer': lambda v: isinstance(v,int) and not isinstance(v,bool),
        'boolean': lambda v: isinstance(v,bool),
        'null': lambda v: v is None,
    }
    if allowed and not any(test_type.get(x,lambda _:False)(value) for x in allowed):
        return [f'{where}: type must be {allowed}']
    if 'const' in schema and value != schema['const']:
        errors.append(f'{where}: must equal {schema["const"]!r}')
    if 'enum' in schema and value not in schema['enum']:
        errors.append(f'{where}: must be one of {schema["enum"]}')
    if isinstance(value, str):
        if len(value)<schema.get('minLength',0):errors.append(f'{where}: text too short')
        if 'pattern' in schema and re.search(schema['pattern'],value) is None:
            errors.append(f'{where}: invalid string pattern')
        if schema.get('format')=='date-time':
            try:
                when=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
                if when.utcoffset() is None:raise ValueError('no offset')
            except ValueError:errors.append(f'{where}: must be offset-aware date-time')
        if schema.get('format')=='uri' and not urlsplit(value).scheme:
            errors.append(f'{where}: not a valid URI')
    if isinstance(value,dict):
        for k in schema.get('required',[]):
            if k not in value:errors.append(f'{where}: missing {k}')
        properties=schema.get('properties',{})
        for k,v in value.items():
            if k in properties:errors.extend(validate_schema_subset(v,properties[k],where+'.'+k))
            elif schema.get('additionalProperties') is False:
                errors.append(f'{where}: unsupported field {k}')
    if isinstance(value,list):
        if len(value)<schema.get('minItems',0):errors.append(f'{where}: too few items')
        if 'maxItems' in schema and len(value)>schema['maxItems']:
            errors.append(f'{where}: too many items')
        for i,v in enumerate(value):
            errors.extend(validate_schema_subset(v,schema.get('items',{}),f'{where}[{i}]'))
    if isinstance(value,int) and not isinstance(value,bool):
        if 'minimum' in schema and value<schema['minimum']:errors.append(f'{where}: below minimum')
        if 'maximum' in schema and value>schema['maximum']:errors.append(f'{where}: above maximum')
    return errors


def validate_manifest(m: dict, *, available: set[str] | None = None,
                      expected_project: str | None = None) -> list[str]:
    schema_file=Path(__file__).resolve().parents[1]/'schemas'/'ziprunner-manifest.schema.json'
    schema=load_json(schema_file.read_text(encoding='utf-8'),str(schema_file))
    errors: list[str] = validate_schema_subset(m,schema)
    def bad(what: str): errors.append(what)
    if m.get('schema') != SCHEMA:
        bad('schema must be '+SCHEMA)
    if not VERSION.fullmatch(str(m.get('spec_version', ''))):
        bad('spec_version must be compatible 1.x.y')
    proj = m.get('project')
    if not isinstance(proj, dict):
        bad('project must be an object'); proj = {}
    key = proj.get('key')
    if not isinstance(key, str) or not IDENT.fullmatch(key):
        bad('project.key must be a stable nonempty identifier')
    if not isinstance(proj.get('version'), str) or not proj['version'].strip():
        bad('project.version required')
    if expected_project and key != expected_project:
        bad(f'project.key mismatch: expected {expected_project}, got {key!r}')
    update = m.get('update')
    if not isinstance(update, dict):
        bad('update must be an object');update = {}
    if not isinstance(update.get('id'),str) or not IDENT.fullmatch(update['id']):
        bad('update.id required and must be valid')
    if update.get('kind') not in ('source_update','progress_update'):
        bad('update.kind must be source_update or progress_update')
    if not isinstance(update.get('summary'),str) or not update['summary'].strip():
        bad('update.summary required')
    try:
        stamp = dt.datetime.fromisoformat(update['created_at'].replace('Z','+00:00'))
        if stamp.utcoffset() is None: bad('update.created_at must contain timezone')
    except (KeyError,TypeError,ValueError):
        bad('update.created_at must be ISO 8601 with timezone')
    p, d, t = (m.get(k) for k in ('planned_work','done_work','todo_work'))
    for k,v in (('planned_work',p),('done_work',d),('todo_work',t)):
        if not isinstance(v,list): bad(k+' must be an array')
    p=p if isinstance(p,list) else []
    d=d if isinstance(d,list) else []
    t=t if isinstance(t,list) else []
    def ids(kind: str, rows: list) -> list[str]:
        out=[]
        for index,x in enumerate(rows):
            if not isinstance(x,dict):
                bad(f'{kind}[{index}]: expected object');continue
            ident=x.get('id')
            if not isinstance(ident,str) or not IDENT.fullmatch(ident):
                bad(f'{kind}[{index}]: missing or invalid id')
            else: out.append(ident)
        if len(out)!=len(set(out)):
            bad(f'{kind}: duplicate work item IDs')
        return out
    pi,di,ti=ids('planned_work',p),ids('done_work',d),ids('todo_work',t)
    if set(di)&set(ti): bad('done_work and todo_work must be disjoint')
    if set(pi)!=set(di)|set(ti):
        bad(f'planned_work IDs must equal done+todo IDs (unaccounted: {sorted(set(pi)-set(di)-set(ti))}, extra: {sorted((set(di)|set(ti))-set(pi))})')
    for i,item in enumerate(p):
        if not isinstance(item,dict):continue
        if not isinstance(item.get('title'),str) or not item['title'].strip():bad(f'planned_work[{i}].title required')
        if not isinstance(item.get('acceptance_criteria'),str) or not item['acceptance_criteria'].strip():bad(f'planned_work[{i}].acceptance_criteria required')
    for i,item in enumerate(d):
        if not isinstance(item,dict):continue
        if not isinstance(item.get('summary'),str) or not item['summary'].strip():bad(f'done_work[{i}].summary required')
        refs=item.get('evidence')
        if not isinstance(refs,list) or not refs:bad(f'done_work[{i}].evidence must be a nonempty array');continue
        for j,e in enumerate(refs):
            if not isinstance(e,dict):bad(f'done_work[{i}].evidence[{j}] must be object');continue
            if e.get('kind') not in ('source','test','log','diff','manual','review','documentation'):
                bad(f'done_work[{i}].evidence[{j}] invalid kind')
            if not isinstance(e.get('description'),str) or not e['description'].strip():
                bad(f'done_work[{i}].evidence[{j}] requires description')
            error=local_reference_error(e.get('ref'),available)
            if error:bad(f'done_work[{i}].evidence[{j}].ref: {error}')
    for i,item in enumerate(t):
        if not isinstance(item,dict):continue
        if item.get('status') not in ('planned','in_progress','review','blocked','deferred'):
            bad(f'todo_work[{i}].status invalid')
        if not isinstance(item.get('next_action'),str) or not item['next_action'].strip():
            bad(f'todo_work[{i}].next_action required')
        if item.get('status')=='blocked' and not item.get('blockers'):
            bad(f'todo_work[{i}].blockers required when blocked')
    v=m.get('validation')
    if not isinstance(v,dict):bad('validation must be object');v={}
    if v.get('model_reported') not in ('passed','partial','failed','not_run'):
        bad('validation.model_reported invalid')
    checks=v.get('checks')
    if not isinstance(checks,list):bad('validation.checks must be array');checks=[]
    for i,c in enumerate(checks):
        if not isinstance(c,dict):bad(f'validation.checks[{i}] must be object');continue
        if c.get('status') not in ('passed','failed','not_run','blocked'):
            bad(f'validation.checks[{i}].status invalid')
        if not isinstance(c.get('id'),str) or not IDENT.fullmatch(c['id']):
            bad(f'validation.checks[{i}].id invalid')
        if not isinstance(c.get('description'),str) or not c['description'].strip():
            bad(f'validation.checks[{i}].description required')
        if c.get('status') in ('not_run','blocked') and not c.get('reason'):
            bad(f'validation.checks[{i}] must give reason when not run or blocked')
        if c.get('status')=='passed' and not c.get('evidence_ref'):
            bad(f'validation.checks[{i}] passed requires evidence_ref')
        if c.get('evidence_ref'):
            error=local_reference_error(c['evidence_ref'],available)
            if error: bad(f'validation.checks[{i}].evidence_ref: {error}')
    if any(isinstance(c,dict) and c.get('status')=='failed' for c in checks) and v.get('model_reported')=='passed':
        bad('validation cannot report passed with failed checks')
    hand=m.get('handover')
    if not isinstance(hand,dict):bad('handover must be object');hand={}
    if not isinstance(hand.get('next_pass'),str) or not hand['next_pass'].strip():bad('handover.next_pass required')
    for k in ('risks','blockers'):
        if not isinstance(hand.get(k),list):bad('handover.'+k+' must be array')
    if not isinstance(m.get('operator_actions'),list):bad('operator_actions must be array')
    else:
        for i,a in enumerate(m['operator_actions']):
            if not isinstance(a,dict) or a.get('status') not in ('required','optional','not_required'):
                bad(f'operator_actions[{i}] invalid or pre-approved')
    rel=m.get('release')
    if not isinstance(rel,dict) or rel.get('requires_operator_approval') is not True or not isinstance(rel.get('requested'),bool):
        bad('release must state requested boolean and requires_operator_approval=true')
    changes=m.get('plan_changes',[])
    if not isinstance(changes,list):bad('plan_changes must be array')
    else:
        for change in changes:
            if not isinstance(change,dict) or change.get('id') not in set(pi) or not change.get('reason'):
                bad('plan_changes must reference planned IDs and a nonempty reason')
    return errors


def validate_looprd_link(link: dict, *, available: set[str] | None = None, root: Path | None = None, expected_project: str | None = None, read_file=None) -> list[str]:
    """Check optional ZipRunner producer link, not the full external Looprd YAML semantics."""
    errors=[]
    schema_path=Path(__file__).resolve().parents[1]/'schemas'/'ziprunner-looprd-link.schema.json'
    schema=load_json(schema_path.read_text(encoding='utf-8'), str(schema_path))
    errors.extend(validate_schema_subset(link,schema))
    if expected_project and link.get('project')!=expected_project:
        errors.append(f'Looprd project mismatch: expected {expected_project}, got {link.get("project")!r}')
    name=link.get('specification')
    if not isinstance(name,str):return errors
    problem=archive_path_error(name)
    if problem:
        errors.append(f'Looprd specification unsafe path {name!r}: {problem}')
        return errors
    if name.casefold()=='ziprunner.looprd.json':
        errors.append('Looprd specification must name a separate YAML file')
    if not name.endswith(('.yaml','.yml')):
        errors.append('Looprd specification must be YAML')
    if available is not None and name not in available:
        errors.append('Looprd specification missing from package/root: '+name)
        return errors
    if root is not None and read_file is None:
        try:
            candidate=root.joinpath(*name.split('/'))
            if any(p.is_symlink() for p in (candidate,*candidate.parents) if p!=root and p.is_relative_to(root)):
                errors.append('Looprd specification must not pass through a symlink')
                return errors
            resolved=candidate.resolve(strict=True)
            if not resolved.is_relative_to(root.resolve()):
                errors.append('Looprd specification escapes root')
                return errors
            if not resolved.is_file():
                errors.append('Looprd specification is not a normal file')
                return errors
            content=resolved.read_bytes()
        except (OSError,RuntimeError) as exc:
            errors.append(f'cannot read Looprd specification: {exc}')
            return errors
    elif read_file is not None:
        try:content=read_file(name)
        except (OSError,KeyError,RuntimeError,ValueError) as exc:
            errors.append(f'cannot read Looprd specification: {exc}')
            return errors
    else:
        return errors
    if len(content)>1024*1024:
        errors.append('Looprd specification exceeds upstream 1 MiB limit')
    digest=hashlib.sha256(content).hexdigest()
    if digest!=link.get('specification_sha256'):
        errors.append('Looprd specification SHA-256 mismatch')
    # Full Looprd YAML validation intentionally delegated to pinned DAPI CLI.
    return errors


def inspect_archive(path: Path, expected_project: str | None = None) -> list[str]:
    errors: list[str]=[]
    try:
        with zipfile.ZipFile(path) as z:
            infos=z.infolist()
            if len(infos)>MAX_ENTRIES:errors.append('too many ZIP entries')
            names=[];case_names=[]
            total=0
            for i in infos:
                name=i.filename
                err=archive_path_error(name)
                if err:errors.append(f'unsafe ZIP path {name!r}: {err}')
                clean=name.rstrip('/')
                case_names.append(clean.casefold());names.append(clean)
                mode=(i.external_attr>>16)&0xffff
                file_type=stat.S_IFMT(mode)
                if file_type not in (0,stat.S_IFDIR,stat.S_IFREG):
                    errors.append(f'nonregular archive entry forbidden: {name}')
                if i.file_size>MAX_FILE:errors.append(f'archive entry too large: {name}')
                total+=i.file_size
                if i.file_size>1024*1024 and i.compress_size and i.file_size/i.compress_size>MAX_RATIO:
                    errors.append(f'excessive compression ratio: {name}')
                if clean.casefold().split('/')[-1]=='ziprunner.config.json':
                    errors.append(f'active ziprunner.config.json must not be shipped: {name}')
                if clean.casefold().split('/')[-1] in ('.env','.env.local'):
                    errors.append(f'likely secret file must not be shipped: {name}')
            if total>MAX_UNPACKED:errors.append('decompressed ZIP size exceeds limit')
            duplicates=[n for n,count in Counter(case_names).items() if count>1]
            if duplicates:errors.append(f'case-insensitive duplicate paths: {duplicates[:5]}')
            available={i.filename for i in infos if not i.is_dir()}
            if 'ziprunner-manifest.json' not in available:
                errors.append('missing supplemental ziprunner-manifest.json (this ZIP is not full v2 producer-conformant)')
                if '.ziprunner-workboard-update.json' not in available:
                    errors.append('missing required root-level .ziprunner-workboard-update.json (source ZIP gate)')
                return errors
            if z.getinfo('ziprunner-manifest.json').file_size>MAX_MANIFEST:
                errors.append('work manifest is too large');return errors
            try:
                manifest=load_json(z.read('ziprunner-manifest.json').decode('utf8'),'ziprunner-manifest.json')
            except (UnicodeError,ValueError) as exc:errors.append(str(exc));return errors
            errors.extend(validate_manifest(manifest,available=available,expected_project=expected_project))
            kind=manifest.get('update',{}).get('kind') if isinstance(manifest.get('update'),dict) else None
            project=manifest.get('project',{}).get('key') if isinstance(manifest.get('project'),dict) else None
            if kind=='source_update':
                if '.ziprunner-workboard-update.json' not in available:
                    errors.append('missing required root-level .ziprunner-workboard-update.json (source ZIP gate)')
                else:
                    try:
                        wb=read_workboard_bytes(z.read('.ziprunner-workboard-update.json')) if z.getinfo('.ziprunner-workboard-update.json').file_size <= MAX_MANIFEST else None
                        if wb is None:
                            errors.append('.ziprunner-workboard-update.json: size exceeds 256 KiB')
                        else:
                            version=manifest.get('project',{}).get('version') if isinstance(manifest.get('project'),dict) else None
                            errors.extend(validate_workboard(wb, expected_project=expected_project or project, expected_version=version))
                    except (UnicodeError, ValueError, RuntimeError) as exc:
                        errors.append(str(exc))
                if 'project.zr' not in available:errors.append('source_update must include project.zr for standalone conformance')
                else:
                    try:
                        recipe=load_json(z.read('project.zr').decode('utf8'),'project.zr')
                        if recipe.get('project_key')!=project:errors.append('project.zr project_key disagrees with work manifest')
                        if recipe.get('schema')!='ziprunner.zr/v1':errors.append('project.zr has wrong recipe schema')
                    except (UnicodeError,ValueError) as exc:errors.append(str(exc))
            if kind=='progress_update':
                for name in available:
                    if name in ('ziprunner-manifest.json','ziprunner.project-state.json','ZIPRUNNER_HANDOFF.md') or name.startswith('docs/') and not name.endswith('/'):
                        if name.startswith('docs/') and Path(name).suffix.lower() not in ('.md','.txt','.json','.adoc'):
                            errors.append('progress_update docs must be inert text: '+name)
                        continue
                    errors.append('progress_update cannot ship source, recipes, commands or executables: '+name)
            if '.ziprunner-package-manifest.json' in available:
                try:
                    inventory=load_json(z.read('.ziprunner-package-manifest.json').decode('utf8'),'self-source inventory')
                    if inventory.get('schema')!='ziprunner.source-package-manifest.v1':
                        errors.append('unsupported self-source inventory schema')
                    rows=inventory.get('entries')
                    if not isinstance(rows,list):errors.append('inventory entries must be array');rows=[]
                    if inventory.get('file_count')!=len(rows):errors.append('inventory file_count mismatch')
                    listed=set()
                    for entry in rows:
                        if not isinstance(entry,dict):errors.append('invalid inventory row');continue
                        n=entry.get('path')
                        if not isinstance(n,str) or n in listed:errors.append('invalid/duplicate inventory path');continue
                        listed.add(n)
                        if n not in available:errors.append('inventory declares missing file '+n);continue
                        if not HEX64.fullmatch(str(entry.get('sha256',''))):errors.append('invalid digest for '+n);continue
                        data=z.read(n)
                        if hashlib.sha256(data).hexdigest().lower()!=entry['sha256'].lower() or len(data)!=entry.get('size'):
                            errors.append('inventory digest/size mismatch for '+n)
                    missing=(available- {'.ziprunner-package-manifest.json'})-listed
                    extra=listed-(available- {'.ziprunner-package-manifest.json'})
                    if missing or extra:errors.append(f'inventory does not cover archive (missing={len(missing)}, extra={len(extra)})')
                except (ValueError,UnicodeError,RuntimeError) as exc:errors.append(str(exc))
            if kind=='source_update' and 'ziprunner.looprd.json' in available:
                try:
                    link_bytes=z.read('ziprunner.looprd.json') if z.getinfo('ziprunner.looprd.json').file_size<=MAX_MANIFEST else None
                    if link_bytes is None:
                        errors.append('ziprunner.looprd.json exceeds 256 KiB')
                    else:
                        link=load_json(link_bytes.decode('utf-8'), 'ziprunner.looprd.json')
                        errors.extend(validate_looprd_link(link, available=available, expected_project=expected_project or project, read_file=z.read))
                except (UnicodeError,ValueError,RuntimeError) as exc:
                    errors.append(str(exc))
            return errors
    except (FileNotFoundError,zipfile.BadZipFile,OSError,RuntimeError) as exc:
        return [f'cannot read ZIP: {exc}']


def run() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='mode',required=True)
    manifest=sub.add_parser('manifest',help='validate a work manifest')
    manifest.add_argument('path',type=Path)
    manifest.add_argument('--root',type=Path,help='directory containing evidence refs')
    manifest.add_argument('--expected-project',default=None)
    workboard=sub.add_parser('workboard',help='validate a mandatory Work board update JSON')
    workboard.add_argument('path',type=Path)
    workboard.add_argument('--expected-project',default=None)
    workboard.add_argument('--expected-version',default=None)
    looprd=sub.add_parser('looprd',help='validate optional Looprd link and bound source file (not YAML semantics)')
    looprd.add_argument('path',type=Path)
    looprd.add_argument('--root',type=Path,required=True)
    looprd.add_argument('--expected-project',default=None)
    package=sub.add_parser('package',help='inspect a ZIP without extracting or executing')
    package.add_argument('path',type=Path)
    package.add_argument('--expected-project',default=None)
    args=parser.parse_args()
    try:
        if args.mode=='package':errors=inspect_archive(args.path,args.expected_project)
        elif args.mode=='looprd':
            link=load_json(args.path.read_text(encoding='utf-8'),str(args.path))
            errors=validate_looprd_link(link,root=args.root,expected_project=args.expected_project)
        elif args.mode=='workboard':
            workboard_doc=read_workboard_bytes(args.path.read_bytes(),str(args.path))
            errors=validate_workboard(workboard_doc,expected_project=args.expected_project,expected_version=args.expected_version)
        else:
            doc=load_json(args.path.read_text(encoding='utf-8'),str(args.path))
            available=None
            if args.root is not None:
                root=args.root.resolve()
                available={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
            errors=validate_manifest(doc,available=available,expected_project=args.expected_project)
    except (OSError,ValueError) as exc:errors=[str(exc)]
    if errors:
        for err in errors:print('ERROR:',err,file=sys.stderr)
        print(f'FAIL: {len(errors)} issue(s)',file=sys.stderr)
        return 1
    print('PASS: ZipRunner v2.1 '+args.mode+' validated')
    return 0


if __name__=='__main__':
    raise SystemExit(run())

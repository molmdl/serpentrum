#!/usr/bin/env python3.6
"""Requirements-ledger integrity checker (DOCS-05 traceability half).

Audits ``.planning/REQUIREMENTS.md`` mechanically so the v1 ledger stays
honest: ID uniqueness, exact row count (the canonical 46 are hardcoded so
count drift — the stale '44' class — fails loudly, Pitfall 8),
Evidence-cited file/exec paths exist on disk, and the checkbox list
agrees with the
traceability table status of every ID. ``--release`` additionally asserts
ZERO Pending rows (GATE V / 08-11 close-out mode; default mode allows the
10 Phase-8 Pending rows).

Both importable (``run_checks``) and runnable as a CLI — the
tools/check_purity.py dual CLI/import precedent::

    python3.6 tools/audit_requirements.py              # default ledger
    python3.6 tools/audit_requirements.py --release    # GATE V mode
    python3.6 tools/audit_requirements.py FILE.md      # explicit ledger

``run_checks(md_text, repo_root, release=False)`` returns a list of
``(check_name, ok, message)`` tuples. stdlib only, py3.6-compatible.
NO tools/__init__.py (plugin-path safety gate).

Ledger grammar parsed:

- Traceability table rows: markdown table rows whose FIRST cell is an
  ID token (``[A-Z]+-NN``). Cells: Requirement | Phase | Status |
  [Evidence]. Both 3-cell (pre-Evidence) and 4-cell shapes parse.
- Status normalization: a status string that STARTS with 'Complete'
  (e.g. 'Complete (owner-amended contract - see note)') counts as
  Complete; one starting with 'Pending' counts as Pending; anything
  else fails the agreement check with the row named.
- Checkbox rows: ``- [x] **ID**:`` / ``- [ ] **ID**:`` lines.
- Evidence path tokens: a whitespace token counts as a repo path iff it
  contains '/' AND (ends with a known suffix OR starts with a known
  dir). Prose ('GATE V (08-11) approval') and extensionless non-path
  tokens are never path-checked; glob tokens ('*') are skipped.
"""
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Hardcoded canonical list — count drift fails loudly (Pitfall 8).
# 8 + 11 + 6 + 6 + 4 + 6 + 5 = 46.
CANONICAL_IDS = tuple(
    ['SETUP-%02d' % i for i in range(1, 9)] +
    ['GAME-%02d' % i for i in range(1, 12)] +
    ['STACK-%02d' % i for i in range(1, 7)] +
    ['SPECTRA-%02d' % i for i in range(1, 7)] +
    ['DATA-%02d' % i for i in range(1, 5)] +
    ['INFRA-%02d' % i for i in range(1, 7)] +
    ['DOCS-%02d' % i for i in range(1, 6)])
REQUIRED_COUNT = 46

_ID_RE = re.compile(r'^[A-Z]+-\d\d$')
_CHECKBOX_RE = re.compile(r'^- \[(.)\] \*\*([A-Z]+-\d\d)\*\*', re.M)

# Path-token shape: conservative — a token is a repo path iff it contains
# '/' AND (ends with a known suffix OR starts with a known dir).
_KNOWN_SUFFIXES = ('.py', '.md', '.json', '.sdf', '.txt', '.sh', '.bat',
                   '.out')
_KNOWN_DIRS = ('smoke/', 'tests/', 'serpentrum/', 'tools/', '.planning/')
_TOKEN_STRIP = '`"\'<>()[]{},;:'

DEFAULT_LEDGER = os.path.join(REPO_ROOT, '.planning', 'REQUIREMENTS.md')


def _parse_table_rows(md_text):
    """Yield (req_id, status, evidence) for every traceability-row line
    whose first cell is an ID token."""
    rows = []
    for line in md_text.split('\n'):
        s = line.strip()
        if not s.startswith('|'):
            continue
        cells = [c.strip() for c in s.strip('|').split('|')]
        if not cells or not _ID_RE.match(cells[0]):
            continue  # header ('Requirement'), separators, prose tables
        if len(cells) < 3:
            continue
        evidence = cells[3] if len(cells) > 3 else ''
        rows.append((cells[0], cells[2], evidence))
    return rows


def _parse_checkboxes(md_text):
    """{req_id: checked_bool} from '- [x] **ID**:' / '- [ ] **ID**:' lines."""
    boxes = {}
    for mark, rid in _CHECKBOX_RE.findall(md_text):
        boxes[rid] = mark.lower() == 'x'
    return boxes


def _normalize_status(status):
    """'Complete' / 'Pending' or None (unknown value)."""
    if status.startswith('Complete'):
        return 'Complete'
    if status.startswith('Pending'):
        return 'Pending'
    return None


def _looks_like_path(token):
    if '/' not in token or '*' in token:
        return False
    return (token.startswith(_KNOWN_DIRS) or token.endswith(_KNOWN_SUFFIXES))


def _extract_paths(evidence):
    """Whitespace tokens of an Evidence cell that look like repo paths."""
    tokens = []
    for raw in evidence.split():
        token = raw.strip(_TOKEN_STRIP)
        if _looks_like_path(token):
            tokens.append(token)
    return tokens


def _check_ids_unique(rows):
    counts = {}
    for rid, _status, _ev in rows:
        counts[rid] = counts.get(rid, 0) + 1
    problems = []
    for rid in CANONICAL_IDS:
        n = counts.get(rid, 0)
        if n == 0:
            problems.append('%s missing from traceability table' % rid)
        elif n > 1:
            problems.append('%s appears %d times in traceability table'
                            % (rid, n))
    extra = sorted(r for r in counts if r not in CANONICAL_IDS)
    for rid in extra:
        problems.append('unknown ID %s in traceability table' % rid)
    if problems:
        return False, '; '.join(problems)
    return True, 'all %d canonical IDs appear exactly once' % REQUIRED_COUNT


def _check_row_count(rows):
    n = len(rows)
    if n != REQUIRED_COUNT:
        return False, ('traceability table has %d ID rows, expected %d '
                       '(count drift — the canonical list is hardcoded)'
                       % (n, REQUIRED_COUNT))
    return True, 'traceability table has exactly %d ID rows' % n


def _check_evidence_paths(rows, repo_root):
    missing = []
    checked = 0
    for rid, _status, evidence in rows:
        for token in _extract_paths(evidence):
            checked += 1
            if not os.path.exists(os.path.join(repo_root, token)):
                missing.append('%s -> %s' % (rid, token))
    if missing:
        return False, ('Evidence path(s) not found on disk: '
                       + '; '.join(missing))
    return True, 'all %d cited Evidence path(s) exist' % checked


def _check_checkbox_agreement(rows, boxes):
    problems = []
    for rid, status, _ev in rows:
        norm = _normalize_status(status)
        if norm is None:
            problems.append('%s has unrecognized status %r '
                            '(expected Complete*/Pending*)' % (rid, status))
            continue
        if rid not in boxes:
            problems.append('%s has no checkbox-list entry' % rid)
            continue
        if norm == 'Complete' and not boxes[rid]:
            problems.append('%s is Complete in the table but [ ] checked'
                            % rid)
        elif norm == 'Pending' and boxes[rid]:
            problems.append('%s is Pending in the table but [x] checked'
                            % rid)
    if problems:
        return False, '; '.join(problems)
    return True, ('checkbox list and table statuses agree for all '
                  '%d IDs' % len(rows))


def _check_no_pending(rows):
    pending = sorted(rid for rid, status, _ev in rows
                     if _normalize_status(status) == 'Pending')
    if pending:
        return False, ('release mode: %d Pending row(s) remain: %s'
                       % (len(pending), ', '.join(pending)))
    return True, 'release mode: zero Pending rows'


def run_checks(md_text, repo_root=REPO_ROOT, release=False):
    """Run the integrity checks; returns [(check_name, ok, message), ...]."""
    rows = _parse_table_rows(md_text)
    boxes = _parse_checkboxes(md_text)
    results = [('ids-unique',) + _check_ids_unique(rows),
               ('row-count',) + _check_row_count(rows),
               ('evidence-paths',) + _check_evidence_paths(rows, repo_root),
               ('checkbox-agreement',) + _check_checkbox_agreement(rows,
                                                                   boxes)]
    if release:
        results.append(('no-pending',) + _check_no_pending(rows))
    return results


def main(argv=None):
    """CLI: print PASS/FAIL lines (flushed), exit 0 when all green."""
    argv = list(sys.argv[1:]) if argv is None else list(argv)
    release = False
    if '--release' in argv:
        argv.remove('--release')
        release = True
    path = argv[0] if argv else DEFAULT_LEDGER
    with open(path, encoding='utf-8') as fh:
        md_text = fh.read()
    results = run_checks(md_text, REPO_ROOT, release=release)
    ok_all = True
    for name, ok, message in results:
        ok_all = ok_all and ok
        print('%s %s: %s' % ('PASS' if ok else 'FAIL', name, message),
              flush=True)
    print('AUDIT-%s requirements-ledger' % ('OK' if ok_all else 'FAIL'),
          flush=True)
    return 0 if ok_all else 1


if __name__ == '__main__':
    sys.exit(main())

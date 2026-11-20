#!/usr/bin/env python3
"""A tag run leaves a draft: no workflow here publishes a release.

Publication is a person's step. This reads every workflow and refuses the
spellings that un-draft or create a public release, and a job that exists to
publish. python3 only."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = sorted((ROOT / '.github/workflows').glob('*.yml'))

PUBLIC = [
    (re.compile(r'draft\s*[=:]\s*false', re.I), 'sets draft to false'),
    (re.compile(r'gh\s+release\s+create(?![^\n]*--draft)'), 'creates a release that is not a draft'),
    (re.compile(r'gh\s+release\s+edit[^\n]*--draft\s*=?\s*false'), 'un-drafts a release'),
    (re.compile(r'--prerelease\s*=?\s*false'), 'marks a release final'),
]


def code_lines(path):
    for n, line in enumerate(path.read_text().splitlines(), 1):
        if not line.lstrip().startswith('#'):
            yield n, line


def violations():
    found = []
    for path in WORKFLOWS:
        rel = path.relative_to(ROOT)
        text = '\n'.join(line for _, line in code_lines(path))
        for pattern, why in PUBLIC:
            for _, line in code_lines(path):
                if pattern.search(line):
                    found.append(f'{rel}: {why}: {line.strip()}')
        if re.search(r'^  publish:\n', text, re.M):
            found.append(f'{rel}: has a job named publish')
    return found


def main():
    bad = violations()
    for item in bad:
        print(f'FAIL release-draft: {item}')
    if not WORKFLOWS:
        print('FAIL release-draft: no workflows read')
        return 1
    if bad:
        return 1
    release = (ROOT / '.github/workflows/release.yml').read_text()
    if not re.search(r'draft=true', release):
        print('FAIL release-draft: release.yml never creates a draft')
        return 1
    print(f'PASS release-draft: {len(WORKFLOWS)} workflows, none publishes; release.yml creates a draft')
    return 0


if __name__ == '__main__':
    sys.exit(main())

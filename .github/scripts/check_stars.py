"""Read PR Markdown as data; execute only the checker from the trusted base commit."""
import base64
import json
import os
import re
import sys
from urllib.parse import quote, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

MIN_STARS = 25
FILES = ('README.md', 'README.zh-CN.md')
STARTS = {'awesome-skills': ('## Skill Ecosystem', '## Skill 生态'),
          'awesome-projects': ('## Project Discovery', '## 项目发现')}
ENDS = {'## Scope', '## 收录范围', '## Contributing', '## 参与贡献',
        '## License', '## 许可证'}
ENTRY = re.compile(r'^\s*[-*+]\s+(?:\*\*)?\[([^\[\]]+)\]\(([^\s()]+)\)(?:\*\*)?\s+[—–-]\s+\S.*$')
REPO = re.compile(r'[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+')


class CheckError(Exception):
    pass


def identity(url):
    """Repository subpaths count against the containing source repository."""
    parsed = urlsplit(url)
    if parsed.scheme in ('https', 'http') and parsed.netloc.lower() == 'github.com':
        parts = parsed.path.strip('/').split('/')
        if len(parts) < 2:
            raise CheckError('GitHub link must identify a source repository')
        repo = re.sub(r'\.git$', '', '/'.join(parts[:2]), flags=re.IGNORECASE)
        if not REPO.fullmatch(repo) or parts[1] in ('.', '..'):
            raise CheckError('Invalid GitHub repository link')
        if len(parts) > 2 and parts[2] not in ('tree', 'blob'):
            raise CheckError('Use the repository or a tree/blob source link')
        return 'github:' + repo.lower()
    # Exact URL identity grandfathers existing website/internal entries only.
    return 'other:' + url


def entries(markdown, start):
    lines = markdown.splitlines()
    if lines.count(start) != 1:
        raise CheckError('Missing or duplicated catalogue start heading: ' + start)
    result = set()
    inside = False
    for line in lines:
        if line == start:
            inside = True
            continue
        if line in ENDS:
            inside = False
        match = ENTRY.fullmatch(line)
        if match:
            result.add(identity(match[2]))
            continue
        if not inside or not line.strip() or re.fullmatch(r'#{2,6} [^<>]+', line):
            continue
        raise CheckError('Unsupported catalogue syntax; use one inline project link and description per bullet')
    return result


def candidates(base, head, repo_name):
    old, new = set(), set()
    for path, start in zip(FILES, STARTS[repo_name]):
        for line in set(head[path].splitlines()) - set(base[path].splitlines()):
            # Do not silently ignore an alternative listing syntax outside the catalogue.
            suspicious = re.match(r'\s*(?:[-*+] |[0-9]+[.)] |<|\|)', line)
            navigation = re.fullmatch(r'\s*[-*+] \[[^]]+\]\(#[^\s)]+\)', line)
            if suspicious and ('[' in line or '<' in line or 'http' in line):
                if not ENTRY.fullmatch(line) and not navigation:
                    raise CheckError('Unrecognized new linked list/HTML/table syntax; use a standard entry')
        old.update(entries(base[path], start))
        new.update(entries(head[path], start))
    return sorted(new - old)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise CheckError('API redirect requires source-link verification')


def api(path):
    # No URLs from the PR are requested. Token goes only to this fixed API origin.
    req = Request('https://api.github.com' + path, headers={
        'Authorization': 'Bearer ' + os.environ['GITHUB_TOKEN'],
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'awesome-minimum-stars-check'})
    with build_opener(NoRedirect).open(req, timeout=30) as response:
        data = response.read(2_000_001)
    if len(data) > 2_000_000:
        raise CheckError('API response exceeds safe size limit')
    return json.loads(data)


def read_readmes(repo, sha):
    if not REPO.fullmatch(repo) or not re.fullmatch(r'[0-9a-f]{40}', sha):
        raise CheckError('Invalid repository or commit identity')
    docs = {}
    for path in FILES:
        item = api(f'/repos/{repo}/contents/{quote(path)}?ref={sha}')
        if item.get('type') != 'file' or item.get('encoding') != 'base64':
            raise CheckError('README must be a regular UTF-8 file returned in full')
        docs[path] = base64.b64decode(''.join(item['content'].split()), validate=True).decode('utf-8')
    return docs


def check(items, fetch=api):
    failures = []
    for item in items:
        if not item.startswith('github:'):
            failures.append('Cannot verify GitHub stars for ' + item)
            continue
        repo = item.removeprefix('github:')
        try:
            metadata = fetch('/repos/' + repo)
            stars = metadata.get('stargazers_count')
            if (metadata.get('full_name', '').lower() != repo
                    or type(stars) is not int or stars < 0):
                raise CheckError('Invalid or mismatched repository metadata')
            print(f'{repo}: {stars} stars (minimum {MIN_STARS})')
            if stars < MIN_STARS:
                failures.append(f'{repo}: {stars} < {MIN_STARS}')
        except Exception as error:
            # Avoid printing response bodies or credentials; continue to check all projects.
            failures.append(f'{repo}: unable to verify ({type(error).__name__})')
    return failures


def main():
    with open(os.environ['GITHUB_EVENT_PATH'], encoding='utf-8') as source:
        event = json.load(source)
    pr = event['pull_request']
    repo = event['repository']['full_name']
    if repo not in ('ningzimu/awesome-skills', 'ningzimu/awesome-projects'):
        raise CheckError('Unexpected target repository')
    if pr['base']['repo']['full_name'] != repo:
        raise CheckError('Base repository mismatch')
    base = read_readmes(repo, pr['base']['sha'])
    head = read_readmes(pr['head']['repo']['full_name'], pr['head']['sha'])
    items = candidates(base, head, repo.split('/')[1])
    failures = check(items)
    for failure in failures:
        # JSON quoting prevents newlines / workflow-command injection through URLs.
        print('FAIL: ' + json.dumps(failure, ensure_ascii=True))
    print(f'Checked {len(items)} new unique source(s); {len(failures)} failure(s).')
    return bool(failures)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print('FAIL: Could not reliably inspect PR (' + type(error).__name__ + ').')
        sys.exit(1)

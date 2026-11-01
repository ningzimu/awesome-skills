from datetime import datetime, timedelta, timezone
import importlib.util
import pathlib
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('check_stars', ROOT / '.github/scripts/check_stars.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def row(url, name='Project'):
    return f'- **[{name}]({url})** — Description.'


def docs(rows=''):
    return {p: heading + '\n' + rows for p, heading in zip(m.FILES, m.STARTS['awesome-skills'])}


class StarsTests(unittest.TestCase):
    NOW = datetime(2026, 11, 1, tzinfo=timezone.utc)

    def fetcher(self, stars=25, age=30, activity=90, **overrides):
        metadata = {'full_name': 'a/b', 'private': False, 'archived': False,
                    'stargazers_count': stars, 'default_branch': 'main',
                    'created_at': (self.NOW - timedelta(days=age)).isoformat()}
        metadata.update(overrides)
        commit = {'sha': 'a' * 40, 'commit': {'committer': {
            'date': (self.NOW - timedelta(days=activity)).isoformat()}}}
        return lambda path: commit if '/commits/' in path else metadata

    def test_boundaries(self):
        for args, failed in (({'stars': 24}, True), ({'stars': 25}, False),
                             ({'age': 29}, True), ({'age': 30}, False),
                             ({'activity': 90}, False), ({'activity': 90 + 1/86400}, True),
                             ({'activity': -1}, True), ({'age': -1}, True),
                             ({'archived': True}, True), ({'private': True}, True)):
            with self.subTest(args=args):
                self.assertEqual(bool(m.check(['github:a/b'], self.fetcher(**args), self.NOW)), failed)

    def test_commit_failure_and_pushed_at_never_substitutes(self):
        for response in ({}, [], {'sha': 'a'*40, 'commit': {'committer': {'date': None}}},
                         {'sha': 'a'*40, 'commit': {'committer': {'date': '2026-11-01'}}}):
            def fetch(path):
                if '/commits/' in path:
                    return response
                return self.fetcher(pushed_at=self.NOW.isoformat())(path)
            self.assertTrue(m.check(['github:a/b'], fetch, self.NOW))
        def fetch(path):
            if '/commits/' in path:
                raise TimeoutError()
            return self.fetcher()(path)
        self.assertTrue(m.check(['github:a/b'], fetch, self.NOW))
        self.assertTrue(m.check(['github:a/b'], self.fetcher(activity=91, pushed_at=self.NOW.isoformat()), self.NOW))

    def test_missing_metadata_fails_closed(self):
        for key in ('created_at', 'default_branch', 'archived'):
            self.assertTrue(m.check(['github:a/b'], self.fetcher(**{key: None}), self.NOW))

    def test_all_projects_and_fail_closed(self):
        calls = []
        def fetch(path):
            calls.append(path)
            if path.endswith('bad'):
                raise TimeoutError()
            return self.fetcher()(path)
        self.assertEqual(len(m.check(['github:a/bad', 'github:a/b', 'other:https://site.test'], fetch, self.NOW)), 2)
        self.assertEqual(calls, ['/repos/a/bad', '/repos/a/b', '/repos/a/b/commits/main'])

    def test_existing_sources_do_not_fetch_metadata(self):
        for name in m.STARTS:
            base = {p: heading + '\n' + row('https://github.com/a/b')
                    for p, heading in zip(m.FILES, m.STARTS[name])}
            head = {p: text.replace('Description.', 'Updated.') for p, text in base.items()}
            items = m.candidates(base, head, name)
            self.assertEqual(m.check(items, lambda _: self.fail('existing source queried')), [])

    def test_bad_api_metadata(self):
        for data in ({}, {'full_name': 'different/repo', 'private': False, 'stargazers_count': 500},
                     {'full_name': 'a/b', 'private': False, 'stargazers_count': '50'},
                     {'full_name': 'a/b', 'private': True, 'stargazers_count': 50}):
            self.assertTrue(m.check(['github:a/b'], lambda _: data))

    def test_bilingual_dedup_case_git_subpaths(self):
        head = docs(row('https://github.com/A/B.GIT/') + '\n' + row('https://github.com/a/b/tree/main/skill'))
        self.assertEqual(m.candidates(docs(), head, 'awesome-skills'), ['github:a/b'])

    def test_existing_translation_and_format_changes(self):
        base = docs(row('https://github.com/a/b'))
        head = docs('- [译名](https://github.com/A/B/) - Translated description.')
        self.assertEqual(m.candidates(base, head, 'awesome-skills'), [])

    def test_existing_website_and_internal_link(self):
        base = docs(row('https://site.test') + '\n' + row('skills/awesome-skills'))
        head = {p: text.replace('Description.', 'New description.') for p, text in base.items()}
        self.assertEqual(m.candidates(base, head, 'awesome-skills'), [])

    def test_new_unknown_source_fails(self):
        for url in ('https://site.test', 'skills/new', 'https://github.com.evil/a/b', 'https://github.com@evil/a/b'):
            items = m.candidates(docs(), docs(row(url)), 'awesome-skills')
            self.assertTrue(m.check(items, lambda _: self.fail('unexpected network request')))

    def test_replacement_and_deletion(self):
        base = docs(row('https://github.com/a/b'))
        self.assertEqual(m.candidates(base, docs(row('https://github.com/a/c')), 'awesome-skills'), ['github:a/c'])
        self.assertEqual(m.candidates(base, docs(), 'awesome-skills'), [])

    def test_malformed_reference_html_table_fail(self):
        for text in ('- [Project][ref]', '<a href="https://github.com/a/b">Project</a>',
                     '| Project | https://github.com/a/b |', '- Project without link'):
            with self.assertRaises(m.CheckError):
                m.candidates(docs(), docs(text), 'awesome-skills')

    def test_navigation_badges_description_links_ignored(self):
        text = '- [Nav](#nav)\n[![Badge](https://badge.test)](https://github.com/a/b)\n'
        head = {p: text + v + '\n' + row('https://github.com/a/c') + ' [Demo](https://github.com/a/d)' for p, v in docs().items()}
        self.assertEqual(m.candidates(docs(), head, 'awesome-skills'), ['github:a/c'])

    def test_entries_after_scope_still_checked(self):
        head = docs('## Scope\n' + row('https://github.com/a/new'))
        self.assertEqual(m.candidates(docs(), head, 'awesome-skills'), ['github:a/new'])

    def test_missing_heading_and_invalid_github(self):
        with self.assertRaises(m.CheckError):
            m.entries('no heading', '## Skill Ecosystem')
        for url in ('https://github.com/owner', 'https://github.com/a/../b', 'https://github.com/a/b/issues/1'):
            with self.assertRaises(m.CheckError):
                m.identity(url)

    def test_redirects_blocked(self):
        with self.assertRaises(m.CheckError):
            m.NoRedirect().redirect_request(None, None, 301, '', {}, 'https://evil.test')

    def test_readme_fetch_sha_and_type(self):
        import base64
        data = {'type': 'file', 'encoding': 'base64', 'content': base64.b64encode(b'hello').decode()}
        with patch.object(m, 'api', return_value=data) as api:
            self.assertEqual(m.read_readmes('a/b', 'a' * 40), dict.fromkeys(m.FILES, 'hello'))
            self.assertIn('?ref=' + 'a' * 40, api.call_args.args[0])
        with patch.object(m, 'api', return_value={'type': 'symlink'}):
            with self.assertRaises(m.CheckError):
                m.read_readmes('a/b', 'a' * 40)
        with self.assertRaises(m.CheckError):
            m.read_readmes('a/b', '$(touch /tmp/unsafe)')

    def test_new_unsupported_links_outside_catalogue_fail(self):
        for line in ('- [Project][ref]', '<a href="https://github.com/a/b">x</a>',
                     '| [Project](https://github.com/a/b) |', '1. [Project](https://github.com/a/b)'):
            head = docs('## Scope\n' + line)
            with self.assertRaises(m.CheckError):
                m.candidates(docs(), head, 'awesome-skills')

    def test_main_uses_exact_base_head_and_returns_failure(self):
        import json
        import os
        import tempfile
        event = {'repository': {'full_name': 'ningzimu/awesome-skills'}, 'pull_request': {
            'base': {'repo': {'full_name': 'ningzimu/awesome-skills'}, 'sha': 'a' * 40},
            'head': {'repo': {'full_name': 'fork/awesome-skills'}, 'sha': 'b' * 40}}}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as file:
            json.dump(event, file)
            file.flush()
            with patch.dict(os.environ, {'GITHUB_EVENT_PATH': file.name}), patch.object(
                    m, 'read_readmes', side_effect=[docs(), docs(row('https://github.com/a/b'))]) as read, patch.object(
                    m, 'check', return_value=['a/b: 24 < 25']) as check:
                self.assertTrue(m.main())
                self.assertEqual(read.call_args_list[0].args, ('ningzimu/awesome-skills', 'a' * 40))
                self.assertEqual(read.call_args_list[1].args, ('fork/awesome-skills', 'b' * 40))
                check.assert_called_once_with(['github:a/b'])

    def test_deleted_readme_and_bad_encoding_fail(self):
        from urllib.error import HTTPError
        for error in (HTTPError('https://api.github.com', 404, 'Not found', {}, None), TimeoutError()):
            with patch.object(m, 'api', side_effect=error):
                with self.assertRaises(type(error)):
                    m.read_readmes('a/b', 'a' * 40)
        with patch.object(m, 'api', return_value={'type': 'file', 'encoding': 'base64', 'content': 'aGVsbG8=!!!'}):
            with self.assertRaises(ValueError):
                m.read_readmes('a/b', 'a' * 40)

    def test_current_catalogue_no_changes(self):
        current = {p: (ROOT / p).read_text() for p in m.FILES}
        name = 'awesome-projects' if '# Awesome Projects' in current['README.md'] else 'awesome-skills'
        self.assertEqual(m.candidates(current, current, name), [])


if __name__ == '__main__':
    unittest.main()

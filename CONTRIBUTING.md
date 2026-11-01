# Contributing

English | [简体中文](CONTRIBUTING.zh-CN.md)

## Selection standards

- **Scope:** Useful AI Agent Skills, reusable agent workflows, and directly related companion tools.
- **Useful and authentic:** explain a concrete use case and distinctive value. Verify the original author's repository and documentation; do not substitute an unrelated popular repository, mirror, or marketing claim for the source.
- **At least 50 stars for new sources:** the original public GitHub repository must have `stargazers_count >= 50` when CI runs. Exactly 50 passes; 49 fails. A skill's tree/blob subdirectory uses its containing repository's count. A passing check is only an eligibility threshold, not approval or proof of quality or safety.
- **Accurate description:** use one short, factual sentence explaining what it does. Avoid unverified superlatives and copied promotional copy. Mention material paid dependencies, platform limits, sensitive permissions, or data handling where relevant.
- **Evidence:** verify purpose, working source links, maintenance context, and actual license terms. Public access does not establish an open-source license; describe missing or restrictive licensing accurately. Stars do not replace this review, and there is no additional numeric age or activity cutoff.
- **No duplicates:** search both language versions first, including renamed projects and aliases. Prefer the original source, not another copy of an existing entry. Different useful skills within one repository may have distinct entries, but CI queries the repository once.

## Entry and language format

Use a single-line bullet with the primary source link first, followed by a concise description:

```markdown
- **[Project name](https://github.com/owner/repository)** — One factual sentence.
```

Existing unbolded bullets with a hyphen separator are also recognized. New entries should use the format above. Use repository URLs, or `tree`/`blob` links for a specific skill. Do not use reference-style links, HTML, tables, redirects, or issue/profile URLs as project entries. Put entries in the catalogue, not the introduction or policy text. Keep the catalogue start heading intact; structural changes require checker review.

Update `README.md` and `README.zh-CN.md` together: same projects, source URLs, category structure, order, and language-switch links. Translate naturally rather than copying one language into the other. Choose the existing category that best matches the use case and preserve its ordering; explain a new category in the PR. Put secondary demos or documentation links in the description, not in place of the source.

## Star check behavior

The check compares primary source identities in both READMEs at the PR base and head commits. It checks new repositories once across both languages; case, `.git`, trailing slash, and repository subpaths are normalized. Existing entries are grandfathered: description, translation, formatting, reordering, and deletion do not trigger retrospective star checks. Adding another path from an already listed repository is not a new source identity. Replacing a source with a different repository is checked. This change does not remove old entries.

New website-only, non-GitHub, or relative source links cannot establish this threshold and fail. Supply the real original GitHub source if one exists; otherwise use an issue for discussion rather than merging an unverifiable entry. Existing website/internal entries remain unchanged; changing their source URL may require review. API timeouts, rate limits, inaccessible repositories, redirects, malformed responses, and unsupported catalogue syntax fail closed. Fix the source or syntax and rerun; if stars are below 50, wait until the source reaches 50. A claimed count or screenshot is not a bypass.

CI checks source stars and supported listing syntax. Reviewers still verify authenticity, relevance, duplicate entries, bilingual alignment, category placement, licenses, and risks. Markdown outside the catalogue is not a general-purpose content validator; reviewers must reject hidden or misplaced listings. A source can lose stars after a successful run; rerun before merging if the result is stale. Retargeting a PR runs the check again; base-branch updates alone do not guarantee a fresh run.

## PR checklist

- [ ] Explain the use case and why this belongs in this list.
- [ ] Link the original source and verify it has at least 50 stars now.
- [ ] Check for existing entries and aliases in both languages.
- [ ] Keep both READMEs aligned, with a concise description and suitable category.
- [ ] Verify documentation, license, dependencies, and relevant risks; do not run untrusted setup scripts just to review a submission.
- [ ] Run `git diff --check` and review the rendered Markdown and links.
- [ ] Wait for **Minimum source stars (50)** and human quality review. If changing the checker, also run `python3 -m unittest discover -s tests -v`.

## Maintainer deployment notes

The workflow deliberately uses `pull_request_target` with only `contents: read`, runs the checker from the pinned PR **base** commit, and fetches the PR's READMEs as data through the GitHub API. It never checks out or executes head code, installs head dependencies, or uses custom secrets. Keep this trust boundary intact. Changes to the workflow/checker require human review; do not run proposed checker code in this workflow. The workflow must first land on the default branch before it can protect later PRs; the bootstrap PR needs local test review.

A failing Action does **not** itself prevent merging. After deployment, an administrator must separately make **Minimum source stars (50)** required in branch protection/rulesets if enforced blocking is desired. This contribution change does not modify repository settings. Fork event behavior, check reporting, and the first hosted run still need verification after publication. No automatic approval or merge is performed.

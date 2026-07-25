---
name: awesome-skills
description: Discover relevant specialist skills from the live awesome-skills list and install them when appropriate. Use proactively for non-trivial tasks that may benefit from a reusable specialist capability not already available, or when the user asks what skills or tools to use. Check the live list before searching for generic alternatives or rebuilding a known capability. Skip simple conversational requests and tasks already covered by installed skills.
---

# Awesome Skills

Use the live `awesome-skills` list as a capability index. Do not assume a fixed set of categories or projects: always read the current list when this skill is needed.

## Workflow

1. Fetch the current English list before looking for candidates:

   ```bash
   curl -fsSL https://raw.githubusercontent.com/ningzimu/awesome-skills/main/README.md
   ```

   If `curl` is unavailable, use:

   ```bash
   wget -qO- https://raw.githubusercontent.com/ningzimu/awesome-skills/main/README.md
   ```

2. Search the fetched list for entries that match the user's goal, inputs, desired output, constraints, and current environment. Read only the relevant sections and shortlist a few candidates.
3. For each serious candidate, inspect its original repository and installation instructions. The list is an index, not a substitute for source documentation.
4. Reuse an installed capability when it already fits. Otherwise install the best matching skill through its documented method or the current environment's native skill installer.
5. Confirm that the new skill is discoverable, then state briefly what was installed and why.

## Boundaries

- Do not query the list for simple conversation, simple writing, translation, or a task already well covered by installed skills.
- Install automatically only when the path is documented, non-interactive, and does not need credentials, account authorization, elevated privileges, or system-level changes.
- Ask before installations with those requirements or an unclear installation path.
- If the list has no suitable candidate, continue with available tools rather than forcing an installation.

# install-skill-with-registration

**Version:** 2.0.0  
**Last Updated:** 2026-09-19  
**Author:** Charles Ho (commissioned)

## Description

Replaces the built-in `install_skill(name)` workflow. Whenever a skill is installed (whether new or revised), this skill:

1. **Installs the skill** (calls the underlying `install_skill(name)` tool)
2. **Retrieves the directory** from GitHub repo `viecharlie/Docs_for_AI/instructions/commissioned-skills-directory.md` using the `api-link-github_repo` skill
3. **Adds or updates the skill's entry** in the directory with description, source, revision date, and trigger phrases using `update_directory.py`
4. **Uploads the updated directory** back to the same GitHub path using the `api-link-github_repo` skill

This ensures every skill installation or revision is automatically recorded, regardless of which chat window or workspace the request originates from.

## Why This Works Across Workspaces

The directory file lives on GitHub (`viecharlie/Docs_for_AI/instructions/`), not in the local sandbox. Any agent in any workspace can pull the latest directory, update it, and push it back using the `api-link-github_repo` skill. This avoids the problem of stale local copies when switching between chat windows.

## Important: Skill Revision = Re-installation

When a skill definition is revised (SKILL.md edited, scripts updated), the skill file is edited and then **re-installed** via `install_skill(name)`. This means the `install-skill-with-registration` workflow handles BOTH:
- **New skill installations** → adds a new entry to the directory
- **Existing skill revisions** → updates the existing entry (bumps revision date, updates description)

There is NO need for a separate "revise" skill — the registration wrapper handles both cases automatically.

## Dependencies

- **api-link-github_repo** — handles all GitHub REST API operations (retrieve and upload)
- **skill-directory-auto-updater** — provides the `update_directory.py` script for modifying the directory

## Workflow

### Step 1: Receive Request
User says "install skill X" or the agent determines a skill needs installing or revising.

### Step 2: Install the Skill
Call `install_skill(name)` to persist the skill in the SP environment.

### Step 3: Retrieve Current Directory from GitHub
Use the `api-link-github_repo` skill to download the current directory:
- Repo: `viecharlie/Docs_for_AI`
- Path: `instructions/commissioned-skills-directory.md`
- Save to: `/workspace/commissioned-skills-directory.md`

### Step 4: Add or Update the Skill's Entry
Run the update script. For a **new skill**:
```bash
python3 /workspace/skills/skill-directory-auto-updater/update_directory.py \
    --action installed \
    --skill-name "skill-name" \
    --description "Short description" \
    --source "Charles Ho (custom)" \
    --latest-revision "YYYY-MM-DD" \
    --trigger-phrases "phrase 1","phrase 2"
```

For a **revised skill**:
```bash
python3 /workspace/skills/skill-directory-auto-updater/update_directory.py \
    --action revised \
    --skill-name "skill-name" \
    --description "Updated description (if changed)" \
    --latest-revision "YYYY-MM-DD"
```

### Step 5: Upload Updated Directory to GitHub
Use the `api-link-github_repo` skill to upload the updated file:
- Repo: `viecharlie/Docs_for_AI`
- Path: `instructions/commissioned-skills-directory.md`
- File: `/workspace/commissioned-skills-directory.md`
- Commit message: `"Register skill: skill-name"` or `"Update directory entry: skill-name (revised YYYY-MM-DD)"`

### Step 6: Confirm
Report to the user that the skill was installed/revised and the directory entry was updated.

## Input

| Field | Required | Description |
|-------|----------|-------------|
| `skill_name` | Yes | Name of the skill to install or revise |
| `description` | Yes | What the skill does |
| `source` | Yes | "Charles Ho (custom)" or GitHub repo link |
| `latest_revision` | Yes | Date (YYYY-MM-DD or YYYY-MM) |
| `trigger_phrases` | Yes | Comma-separated sample user phrases |

## Output

- Skill installed/revised in SP environment
- Directory updated on GitHub at `viecharlie/Docs_for_AI/instructions/commissioned-skills-directory.md`
- Confirmation message to user

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | 2026-09-19 | Added changelog; clarified that skill revision = re-installation (no separate revise skill needed); fixed repo reference to Docs_for_AI; added revised action support |
| 1.1.0 | 2026-09-19 | Refactored to use api-link-github_repo skill instead of raw API calls |
| 1.0.0 | 2026-09-18 | Initial creation — wrapper for install_skill() with directory registration |

## Notes

- This skill SUPERSEDES the bare `install_skill(name)` call — always use this workflow instead
- The `api-link-github_repo` skill handles authentication via the stored GitHub token
- If the directory doesn't exist on GitHub yet, create it first with the standard header
- The `update_directory.py` script is at `/workspace/skills/skill-directory-auto-updater/update_directory.py`
- **Skill revision = re-installation**: Editing a skill's files and calling `install_skill(name)` again triggers this same workflow, which updates the existing directory entry
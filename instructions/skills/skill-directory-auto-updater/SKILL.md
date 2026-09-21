# skill-directory-auto-updater

**Version:** 3.0.0  
**Last Updated:** 2026-09-18  
**Author:** Charles Ho (commissioned)

## Description

Maintains the `commissioned-skills-directory.md` file by detecting newly installed, revised, or removed skills and updating the directory accordingly. Two complementary mechanisms:

1. **On-demand trigger** — Run after every `install_skill()` / `uninstall_skill()` / skill revision
2. **Weekly audit** — Scheduled scan that cross-references the system prompt's available skills list against the directory to catch anything missed

## Companion Scripts

| Script | Purpose |
|--------|---------|
| `update_directory.py` | Add/update/remove a single skill entry. Run after every skill change. |
| `weekly_audit.py` | Full audit: compare available skills vs directory, report missing entries, optionally apply updates and push to GitHub. |

**Location:** `skills/skill-directory-auto-updater/`

## Mechanism 1: On-Demand Trigger (After Every Skill Change)

**After EVERY** `install_skill(name)`, `uninstall_skill(name)`, or skill revision, the agent **MUST** run:

```bash
python3 /workspace/skills/skill-directory-auto-updater/update_directory.py \
    --action installed \
    --skill-name "skill-name" \
    --description "Short description" \
    --source "Charles Ho (custom)" \
    --latest-revision "2026-09" \
    --trigger-phrases "phrase 1","phrase 2"
```

For removals:
```bash
python3 /workspace/skills/skill-directory-auto-updater/update_directory.py \
    --action removed \
    --skill-name "skill-name"
```

## Mechanism 2: Weekly Audit (Scheduled)

Run weekly to catch any skills that were missed by the on-demand trigger.

### How the Audit Works (Reliable, Not Chat-History-Dependent)

The audit uses a **deterministic comparison** that avoids unreliable chat history search:

1. **Read the system prompt** to get the authoritative list of all available/installed skills
2. **Parse the directory** to get the list of recorded skills
3. **Cross-reference** — find skills in the available list that are NOT in the directory AND are NOT built-in system skills
4. **Report or apply** findings

This is reliable because:
- The system prompt's available skills list is the **single source of truth**
- No fuzzy chat history search needed
- The comparison is complete and deterministic

### Running the Audit

```bash
# Audit only (report findings)
python3 /workspace/skills/skill-directory-auto-updater/weekly_audit.py \
    --available-skills "skill1,skill2,skill3,..."

# Audit and apply updates
python3 /workspace/skills/skill-directory-auto-updater/weekly_audit.py \
    --available-skills "skill1,skill2,skill3,..." \
    --apply

# Audit, apply, and push to GitHub
python3 /workspace/skills/skill-directory-auto-updater/weekly_audit.py \
    --available-skills "skill1,skill2,skill3,..." \
    --apply \
    --github-token "ghp_..."
```

### Getting the Available Skills List

The agent running the audit must extract the skill names from the system prompt's available skills section. This is done by reading the prompt and parsing skill names from the list. The format is:

```
- skill-name: "description"
```

Extract all `skill-name` values, join with commas, and pass to `--available-skills`.

## Workflow

### Step 1: On-Demand (After Each Skill Change)
Run `update_directory.py` with the appropriate arguments.

### Step 2: Weekly Audit
Run `weekly_audit.py` to catch any missed skills.

### Step 3: Verify
Read the updated `commissioned-skills-directory.md` and confirm changes.

### Step 4: Upload to GitHub
Push to `viecharlie/Docs_for_SciPal/instructions/commissioned-skills-directory.md`.

## Input

| Field | Description |
|-------|-------------|
| `skill_name` | Name of the skill |
| `action` | `installed`, `revised`, or `removed` |
| `description` | Short description of what the skill does |
| `source` | Attribution: "Charles Ho (custom)" or GitHub repo link |
| `latest_revision` | Date (YYYY-MM-DD or YYYY-MM) |
| `trigger_phrases` | Comma-separated sample user phrases |

## Directory Format

```markdown
| # | Skill Name | Description | Source | Latest Revision | Sample Trigger Phrases |
|---|-----------|-------------|--------|-----------------|----------------------|
| 1 | **skill-name** | Description text. | Source attribution | YYYY-MM-DD | "phrase 1", "phrase 2" |
```

## Source Column Rules

- **Custom skills**: `Charles Ho (custom)`
- **Adapted from open-source**: `[Owner/repo-name](https://github.com/...)` optionally with subpath
- **Unknown**: `TBD`

## Notes

- Do NOT delete removed entries — mark with "REMOVED" annotation
- The directory file is at `/workspace/commissioned-skills-directory.md`
- GitHub: `viecharlie/Docs_for_SciPal/instructions/commissioned-skills-directory.md`
- **Self-registration:** The script auto-checks if this skill is in the directory and adds itself if missing
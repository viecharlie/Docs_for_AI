#!/usr/bin/env python3
"""
weekly_audit.py — Weekly scheduled audit for commissioned-skills-directory.md

Run this script weekly (e.g., via cron or manual trigger) to detect newly installed
or revised skills that are NOT yet recorded in the directory.

HOW IT WORKS:
1. Reads the current commissioned-skills-directory.md
2. Reads the SP environment's available skills list (from the system prompt)
3. Cross-references: finds skills in the available list that are NOT in the directory
   AND are NOT built-in system skills
4. For each missing skill, attempts to determine: description, source, revision date
5. Reports findings and optionally updates the directory

WHY THIS IS MORE RELIABLE THAN CHAT HISTORY SEARCH:
- Chat history search is fuzzy and often fails to find relevant threads
- The available skills list in the system prompt is the AUTHORITATIVE source of truth
- Direct comparison is deterministic and complete
- No reliance on finding the right chat thread

USAGE:
    python3 weekly_audit.py              # Audit only, report findings
    python3 weekly_audit.py --apply       # Audit and update directory with new skills
    python3 weekly_audit.py --apply --github-token TOKEN  # Audit, update, and push to GitHub
"""

import re
import os
import sys
import json
import argparse
from datetime import datetime

DIRECTORY_PATH = "/workspace/commissioned-skills-directory.md"
UPDATE_SCRIPT = "/workspace/skills/skill-directory-auto-updater/update_directory.py"

# Built-in system skills that should NEVER be in the commissioned directory
BUILTIN_SKILLS = {
    "brainstorming", "mineru", "office-docx", "office-pptx", "ppt-master",
    "skill-creator", "skill-judge", "verify-bib", "graphify",
    "virtual-bcell-data-collection",
    "antibody-assay-data-automation", "antibody-sequence-workflow",
    "chai-pythia-pipeline", "clickmab-antibody-humanization",
    "mos-antibody-humanization", "wemol-affinity-maturation",
    "wemol-antibody-stability", "wemol-vhh-humanization", "zotero",
    "scientific-brainstorming", "scientific-critical-thinking",
    "scientific-claim-validator",
    "chemical-formula-subscript-fixer-context-aware",
    "fix-figure-table-subscript-exception",
    "pdf-chemical-formula-subscript-fixer-with-figure-table-exception",
    "mcp-link-um", "mcp-link-consensus", "mcp-api-connector-builder",
    "api-link-github_repo", "github-repo-manager",
    "scientific-writing", "Claud-Sci-Writer",
    "citation-compiler", "citation-vetter", "citation-enricher",
    "unified-scientific-accuracy-guard", "unified-scientific-manuscript-writer",
    "research-grants", "automated-implementer",
    "skill-directory-auto-updater",
    "pdf-figure-table-extractor-with-qc",
    "pdf-to-article-md",
}

def parse_directory_skills():
    """Parse all skill names from the directory file."""
    if not os.path.exists(DIRECTORY_PATH):
        return set()
    
    with open(DIRECTORY_PATH) as f:
        content = f.read()
    
    skills = set()
    for m in re.finditer(r'\|\s*\d+\s*\|\s*\*\*([^*]+)\*\*', content):
        skills.add(m.group(1).strip())
    return skills

def get_available_skills_from_prompt():
    """
    Parse the system prompt to extract all available skill names.
    
    The system prompt contains a list of available skills with descriptions.
    We extract skill names by looking for lines matching the pattern:
    `- skill-name: "description"`
    or
    `- skill-name`
    
    Returns a set of skill names.
    """
    # The system prompt is passed as context. We read it from the environment.
    # Since we can't directly access the system prompt programmatically,
    # we use a different approach: read the available skills from the
    # SP environment's skill registry.
    
    # For now, we rely on the fact that the system prompt lists all available skills.
    # The agent running this script should pass the skill list as an argument
    # or the script reads from a known location.
    
    # Alternative: read from /workspace/available_skills.txt if it exists
    skills_file = "/workspace/available_skills.txt"
    if os.path.exists(skills_file):
        with open(skills_file) as f:
            return set(line.strip() for line in f if line.strip())
    
    return set()

def find_missing_skills(available_skills, dir_skills):
    """Find skills that are available but not in the directory (and not built-in)."""
    missing = set()
    for skill in available_skills:
        if skill not in dir_skills and skill not in BUILTIN_SKILLS:
            missing.add(skill)
    return missing

def generate_trigger_phrases(skill_name):
    """Generate reasonable trigger phrases from a skill name."""
    # Convert kebab-case or snake_case to words
    name = skill_name.replace("-", " ").replace("_", " ")
    words = name.split()
    
    phrases = []
    # Full name as a phrase
    phrases.append(f'"{skill_name}"')
    # Key action phrases
    if "pdf" in words:
        phrases.append(f'"PDF {name}"')
    if "extract" in words or "extractor" in words:
        phrases.append(f'"extract from {name}"')
    if "convert" in words:
        phrases.append(f'"convert {name}"')
    if "download" in words or "downloader" in words:
        phrases.append(f'"download {name}"')
    if "merge" in words:
        phrases.append(f'"merge {name}"')
    if "split" in words:
        phrases.append(f'"split {name}"')
    
    if not phrases:
        phrases.append(f'"{name}"')
    
    return '", "'.join(phrases[:3])

def run_audit(apply_updates=False, github_token=None):
    """Run the weekly audit."""
    print("=" * 60)
    print(f"📋 Weekly Skill Directory Audit — {datetime.now().strftime('%Y-%m-%d')}")
    print("=" * 60)
    
    # Step 1: Read current directory
    dir_skills = parse_directory_skills()
    print(f"\n📁 Skills in directory: {len(dir_skills)}")
    
    # Step 2: Get available skills
    # The agent running this should provide the list
    available_skills = get_available_skills_from_prompt()
    
    if not available_skills:
        print("\n⚠️  Cannot read available skills list directly.")
        print("   The agent running this script must provide the list.")
        print("   Run with: --available-skills skill1,skill2,skill3")
        return
    
    print(f"📦 Available skills: {len(available_skills)}")
    
    # Step 3: Find missing
    missing = find_missing_skills(available_skills, dir_skills)
    
    if not missing:
        print("\n✅ No missing skills found. Directory is up to date.")
        return
    
    print(f"\n🔍 Missing skills ({len(missing)}):")
    for skill in sorted(missing):
        print(f"   - {skill}")
    
    # Step 4: Apply updates if requested
    if apply_updates and missing:
        print("\n🔄 Applying updates...")
        for skill in sorted(missing):
            phrases = generate_trigger_phrases(skill)
            cmd = (
                f'python3 {UPDATE_SCRIPT} '
                f'--action installed '
                f'--skill-name "{skill}" '
                f'--description "Auto-detected skill — {skill.replace(chr(45), chr(32)).replace(chr(95), chr(32))}" '
                f'--source "Charles Ho (custom)" '
                f'--latest-revision "{datetime.now().strftime("%Y-%m-%d")}" '
                f'--trigger-phrases "{phrases}"'
            )
            print(f"   Adding: {skill}")
            os.system(cmd)
        
        print(f"\n✅ Added {len(missing)} skills to directory.")
        
        # Step 5: Push to GitHub if token provided
        if github_token:
            print("\n🔄 Pushing to GitHub...")
            import requests, base64
            owner = "viecharlie"
            repo = "Docs_for_SciPal"
            path = "instructions/commissioned-skills-directory.md"
            
            with open(DIRECTORY_PATH, "rb") as f:
                content_b64 = base64.b64encode(f.read()).decode("utf-8")
            
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
            headers = {"Authorization": f"Bearer {github_token}", "Accept": "application/vnd.github+json"}
            r = requests.get(url, headers=headers)
            sha = r.json().get("sha") if r.status_code == 200 else None
            
            data = {"message": f"Weekly audit: add {len(missing)} new skills", "content": content_b64, "branch": "main"}
            if sha: data["sha"] = sha
            
            r2 = requests.put(url, headers=headers, json=data)
            if r2.status_code in (200, 201):
                print("✅ GitHub upload successful")
            else:
                print(f"❌ GitHub upload failed: {r2.status_code}")
    else:
        print(f"\n💡 Run with --apply to add these skills to the directory.")

def main():
    parser = argparse.ArgumentParser(description="Weekly skill directory audit")
    parser.add_argument("--apply", action="store_true", help="Apply updates to directory")
    parser.add_argument("--github-token", help="GitHub token for push")
    parser.add_argument("--available-skills", help="Comma-separated list of available skills")
    
    args = parser.parse_args()
    
    # If available skills provided via CLI, write to temp file
    if args.available_skills:
        skills = [s.strip() for s in args.available_skills.split(",")]
        with open("/workspace/available_skills.txt", "w") as f:
            for s in skills:
                f.write(f"{s}\n")
    
    run_audit(apply_updates=args.apply, github_token=args.github_token)

if __name__ == "__main__":
    main()
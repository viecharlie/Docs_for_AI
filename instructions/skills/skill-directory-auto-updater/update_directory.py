#!/usr/bin/env python3
"""
skill-directory-auto-updater — v2.0.0

Usage:
    python3 update_directory.py --action installed --skill-name "my-skill" \\
        --description "Does X" --source "Charles Ho (custom)" \\
        --latest-revision "2026-09" --trigger-phrases "do X","do Y"

    python3 update_directory.py --action removed --skill-name "my-skill"

    python3 update_directory.py --action revised --skill-name "my-skill" \\
        --description "Updated description" --latest-revision "2026-09-18"

Reads /workspace/commissioned-skills-directory.md, applies the change,
and writes the updated file back. Self-registers if not present.
"""

import argparse
import re
import os
import sys
from datetime import datetime

DIRECTORY_PATH = "/workspace/commissioned-skills-directory.md"

TABLE_HEADER = "| # | Skill Name | Description | Source | Latest Revision | Sample Trigger Phrases |"
TABLE_SEPARATOR = "|---|-----------|-------------|--------|-----------------|----------------------|"

def read_directory():
    if not os.path.exists(DIRECTORY_PATH):
        return None
    with open(DIRECTORY_PATH, "r") as f:
        return f.read()

def find_section_boundaries(content):
    """Find all section headers and their line ranges."""
    lines = content.split("\n")
    sections = []  # [(header_line_idx, header_name, start_idx, end_idx)]
    
    header_idxs = [i for i, l in enumerate(lines) if l.startswith("## ")]
    
    for i, h_idx in enumerate(header_idxs):
        header = lines[h_idx].replace("## ", "").strip()
        end_idx = header_idxs[i + 1] if i + 1 < len(header_idxs) else len(lines)
        sections.append((h_idx, header, h_idx, end_idx))
    
    return lines, sections

def find_table_in_section(lines, start, end):
    """Find the table boundaries within a section. Returns (header_idx, sep_idx, data_start, data_end) or None."""
    in_table = False
    header_idx = None
    sep_idx = None
    data_start = None
    data_end = None
    
    for i in range(start, end):
        line = lines[i]
        if line.startswith("| # |"):
            header_idx = i
            in_table = True
            continue
        if in_table and line.startswith("|---"):
            sep_idx = i
            data_start = i + 1
            continue
        if in_table and line.startswith("|"):
            data_end = i + 1
            continue
        if in_table and not line.startswith("|") and data_start is not None:
            data_end = i
            break
    
    if header_idx is not None and data_start is not None:
        return header_idx, sep_idx, data_start, data_end
    return None

def parse_skill_row(line):
    """Parse a table row into a dict. Returns None if not a valid data row."""
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    if stripped.startswith("| # |") or stripped.startswith("|---"):
        return None
    
    cells = [c.strip() for c in stripped.split("|")[1:-1]]
    if len(cells) < 6:
        return None
    
    return {
        "number": cells[0],
        "name": cells[1].strip("* "),
        "description": cells[2],
        "source": cells[3],
        "revision": cells[4],
        "phrases": cells[5],
    }

def build_table_row(num, name, desc, source, revision, phrases):
    return f"| {num} | **{name}** | {desc} | {source} | {revision} | {phrases} |"

def update_directory(action, skill_name, description=None, source=None,
                     latest_revision=None, trigger_phrases=None):
    content = read_directory()
    
    if content is None:
        today = datetime.now().strftime("%Y-%m-%d")
        content = f"""# Commissioned Skills Directory

## MCP Skills

{TABLE_HEADER}
{TABLE_SEPARATOR}

## Scientific Writing & Citation Skills

{TABLE_HEADER}
{TABLE_SEPARATOR}

## Infrastructure Skills

{TABLE_HEADER}
{TABLE_SEPARATOR}

*Last updated: {today}*
"""
    
    lines, sections = find_section_boundaries(content)
    
    # Find the Infrastructure Skills section (or first section with a table)
    target_section = None
    for h_idx, h_name, s, e in sections:
        if "Infrastructure" in h_name:
            target_section = (h_idx, h_name, s, e)
            break
    
    if target_section is None:
        # Fallback to first section with a table
        for h_idx, h_name, s, e in sections:
            table_info = find_table_in_section(lines, s, e)
            if table_info:
                target_section = (h_idx, h_name, s, e)
                break
    
    if target_section is None:
        print("ERROR: No section with a table found")
        return False
    
    h_idx, h_name, sec_start, sec_end = target_section
    table_info = find_table_in_section(lines, sec_start, sec_end)
    
    if table_info is None:
        print("ERROR: No table found in target section")
        return False
    
    header_idx, sep_idx, data_start, data_end = table_info
    
    # Parse existing rows
    existing_rows = []
    for i in range(data_start, data_end):
        if i < len(lines):
            row = parse_skill_row(lines[i])
            if row:
                existing_rows.append((i, row))
    
    # Find max number across all sections
    max_num = 0
    for h_idx2, h_name2, s2, e2 in sections:
        ti = find_table_in_section(lines, s2, e2)
        if ti:
            _, _, ds, de = ti
            for i in range(ds, de):
                if i < len(lines):
                    r = parse_skill_row(lines[i])
                    if r:
                        try:
                            n = int(r["number"])
                            if n > max_num:
                                max_num = n
                        except ValueError:
                            pass
    
    # Check if skill already exists
    found_idx = None
    for i, row in existing_rows:
        if row["name"] == skill_name:
            found_idx = i
            break
    
    if found_idx is not None:
        # Update existing row
        old_row = None
        for i, row in existing_rows:
            if i == found_idx:
                old_row = row
                break
        
        if action == "removed":
            lines[found_idx] = f"| ~~{lines[found_idx].strip('|').strip()}~~ | *REMOVED* |"
        elif action in ("revised", "installed"):
            desc = description or old_row["description"]
            src = source or old_row["source"]
            rev = latest_revision or (datetime.now().strftime("%Y-%m-%d") if action == "revised" else old_row["revision"])
            phr = trigger_phrases or old_row["phrases"]
            lines[found_idx] = build_table_row(old_row["number"], skill_name, desc, src, rev, phr)
        print(f"✅ Directory updated: {action} '{skill_name}' (existing entry updated)")
    elif action == "installed":
        # Add new row at the end of the table data
        new_num = max_num + 1
        rev = latest_revision or datetime.now().strftime("%Y-%m-%d")
        src = source or "TBD"
        desc = description or "TBD"
        phr = trigger_phrases or "TBD"
        new_row = build_table_row(str(new_num), skill_name, desc, src, rev, phr)
        
        # Insert after the last data row (before the blank line after table)
        insert_at = data_end if data_end < len(lines) else len(lines)
        lines.insert(insert_at, new_row)
        print(f"✅ Directory updated: {action} '{skill_name}' (new entry added)")
    else:
        print(f"⚠️ Skill '{skill_name}' not found for action '{action}'")
        return False
    
    # Update last updated timestamp
    today = datetime.now().strftime("%Y-%m-%d")
    for i, line in enumerate(lines):
        if line.strip().startswith("*Last updated"):
            lines[i] = f"\n*Last updated: {today}*"
            break
    
    # Write back
    result = "\n".join(lines)
    with open(DIRECTORY_PATH, "w") as f:
        f.write(result)
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Update commissioned skills directory")
    parser.add_argument("--action", required=True, choices=["installed", "revised", "removed"])
    parser.add_argument("--skill-name", required=True)
    parser.add_argument("--description", default=None)
    parser.add_argument("--source", default=None)
    parser.add_argument("--latest-revision", default=None)
    parser.add_argument("--trigger-phrases", default=None)
    
    args = parser.parse_args()
    
    success = update_directory(
        action=args.action,
        skill_name=args.skill_name,
        description=args.description,
        source=args.source,
        latest_revision=args.latest_revision,
        trigger_phrases=args.trigger_phrases,
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
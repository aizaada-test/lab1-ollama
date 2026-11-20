"""Lab 5: load SKILLs from the skills/ folder.

A skill is a folder with a SKILL.md file:

    skills/
      linux-commands/
        SKILL.md          <- required: name + description + instructions
      security-tutor/
        SKILL.md
        ports.md          <- optional extra files are loaded too (reference data)

SKILL.md starts with a small header between two '---' lines:

    ---
    name: linux-commands
    description: One sentence that says what the skill does.
    ---
    (instructions for the model)
"""
import os

SKILLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills")


def _parse_skill_md(text):
    """Split SKILL.md into (header dict, instructions)."""
    header, body = {}, text
    if text.startswith("---"):
        parts = text.split("---", 2)          # ['', header, body]
        if len(parts) == 3:
            for line in parts[1].strip().splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    header[key.strip()] = value.strip()
            body = parts[2]
    return header, body.strip()


def load_skills():
    """Read every skills/<folder>/SKILL.md. Returns {name: skill}."""
    skills = {}
    if not os.path.isdir(SKILLS_DIR):
        return skills
    for folder in sorted(os.listdir(SKILLS_DIR)):
        path = os.path.join(SKILLS_DIR, folder)
        skill_md = os.path.join(path, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue
        with open(skill_md, encoding="utf-8") as f:
            header, instructions = _parse_skill_md(f.read())
        # Extra .md files in the folder (for example ports.md) are reference data.
        extras = []
        for name in sorted(os.listdir(path)):
            if name.endswith(".md") and name != "SKILL.md":
                with open(os.path.join(path, name), encoding="utf-8") as f:
                    extras.append(f"[{name}]\n" + f.read().strip())
        skill_name = header.get("name", folder)
        text = instructions + ("\n\n" + "\n\n".join(extras) if extras else "")
        skills[skill_name] = {
            "name": skill_name,
            "description": header.get("description", ""),
            "files": ["SKILL.md"] + [e.split("]")[0][1:] for e in extras],
            "text": text,
            "size": len(text.encode("utf-8")),
        }
    return skills

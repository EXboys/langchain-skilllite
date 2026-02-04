"""
Direct skill execution without LLM.
"""
from pathlib import Path
from skilllite import SkillManager

skills_dir = Path(".skills")

# Create manager
manager = SkillManager(skills_dir=str(skills_dir))

# List skills
print("Available skills:")
for skill in manager.list_skills():
    print(f"  - {skill.name}: {skill.description[:50]}...")

# Execute directly
result = manager.execute("text-upper", {"text": "hello world"})
print(f"\nResult: {result.output}")


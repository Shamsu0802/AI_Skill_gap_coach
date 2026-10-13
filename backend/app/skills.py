
from pydantic import BaseModel, Field
from typing import List, Dict, Any


class SkillGapRequest(BaseModel):
    current_skills: List[str] = Field(
        ...,
        min_length=1,
        description="Skills the user currently possesses"
    )

    required_skills: List[Dict[str, Any]] = Field(
        ...,
        min_length=1,
        description="Skills extracted from a job description using AI"
    )


def analyze_skill_gaps(request: SkillGapRequest):
    # Normalize user skills for case-insensitive comparison
    current_skills = {
        skill.strip().casefold()
        for skill in request.current_skills
        if skill.strip()
    }

    matched_skills = []
    missing_skills = []

    # Compare current skills against AI-extracted requirements
    for item in request.required_skills:
        skill_name = str(item.get("skill", "")).strip()

        if not skill_name:
            continue

        skill_info = {
            "skill": skill_name,
            "importance": item.get("importance", "medium"),
            "reason": item.get("reason", "")
        }

        if skill_name.casefold() in current_skills:
            matched_skills.append(skill_info)
        else:
            missing_skills.append(skill_info)

    total_skills = len(matched_skills) + len(missing_skills)

    match_percentage = round(
        len(matched_skills) / total_skills * 100
    ) if total_skills else 0

    return {
        "current_skills": request.current_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "total_required_skills": total_skills,
        "matched_count": len(matched_skills),
        "missing_count": len(missing_skills),
        "skill_match_percentage": match_percentage
    }

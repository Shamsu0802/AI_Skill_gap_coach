
import os
import json

from dotenv import load_dotenv
from groq import Groq


# Load environment variables from backend/.env
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError(
        "GROQ_API_KEY not found. Check your backend/.env file."
    )


# Initialize Groq client
client = Groq(api_key=api_key)


# Test the Groq connection
def test_groq_connection():
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": (
                    "Reply with exactly: "
                    "Groq connection successful!"
                )
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content


# Extract required skills from a job description using AI
def extract_required_skills(job_description: str):
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": """
You are an AI career skill analysis assistant.

Analyze the supplied job description and identify
the skills required for the role.

Return a JSON object with this structure:
{
    "job_title": "Job title",
    "required_skills": [
        {
            "skill": "Skill name",
            "importance": "high",
            "reason": "Why the skill is required"
        }
    ]
}

Rules:
1. Extract skills supported by the description.
2. Do not invent requirements.
3. Include technical and relevant professional skills.
4. Importance must be high, medium, or low.
5. Avoid duplicate skills.
6. Return valid JSON only.
"""
            },
            {
                "role": "user",
                "content": job_description
            }
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError(
            "Groq returned an empty skill analysis response."
        )

    try:
        result = json.loads(content)
    except json.JSONDecodeError as exc:
        print("Invalid skill analysis JSON:", repr(content))
        raise ValueError(
            "Groq returned invalid JSON while extracting skills."
        ) from exc

    if not isinstance(result, dict):
        raise ValueError(
            "Groq returned an unexpected skill analysis format."
        )

    if not isinstance(result.get("required_skills"), list):
        raise ValueError(
            "The required_skills field is missing or invalid."
        )

    return result


# Generate a personalized learning roadmap using Groq
def generate_learning_roadmap(
    target_role: str,
    current_skills: list,
    missing_skills: list,
    hours_per_week: int
):
    prompt = {
        "target_role": target_role,
        "current_skills": current_skills,
        "missing_skills": missing_skills,
        "hours_per_week": hours_per_week
    }

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": """
You are an AI career learning coach.

Generate a realistic learning roadmap using the user's
target role, current skills, missing skills, and available
weekly study hours.

Return a JSON object with this structure:
{
    "target_role": "Target job role",
    "estimated_duration_weeks": 6,
    "roadmap": [
        {
            "week": 1,
            "skill": "Skill to learn",
            "learning_objectives": [
                "Objective 1",
                "Objective 2"
            ],
            "practice_task": "Practical exercise",
            "mini_project": "Small project",
            "estimated_hours": 5
        }
    ]
}

Rules:
1. Prioritize high-importance missing skills.
2. Build on skills the user already knows.
3. Respect the weekly study-hour limit.
4. Each week's estimated hours must not exceed
   the user's available weekly study hours.
5. Include practical exercises and mini-projects.
6. Use consecutive week numbers starting from 1.
7. Avoid unnecessary repetition of mastered skills.
8. Return valid JSON only, without Markdown fences.
"""
            },
            {
                "role": "user",
                "content": json.dumps(prompt)
            }
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError(
            "Groq returned an empty roadmap response."
        )

    try:
        result = json.loads(content)
    except json.JSONDecodeError as exc:
        print("Invalid roadmap JSON:", repr(content))
        raise ValueError(
            "Groq returned invalid JSON while generating "
            "the roadmap."
        ) from exc

    if not isinstance(result, dict):
        raise ValueError(
            "Groq returned an unexpected roadmap format."
        )

    if not isinstance(result.get("roadmap"), list):
        raise ValueError(
            "The roadmap field is missing or invalid."
        )

    return result

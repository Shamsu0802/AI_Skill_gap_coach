import json

from fastapi import FastAPI, HTTPException, Depends, Query
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pydantic import BaseModel, Field

from sqlalchemy.orm import Session

from app.database import engine, Base, get_db, get_background_db

from app import models
from zoneinfo import ZoneInfo


from app.models import (

    UserProfile,

    LearningRoadmap,

    LearningProgress,

    MarketSkillObservation,

)

from app.schemas import (

    UserProfileCreate,

    LearningProgressUpdate,

    MarketSkillObservationCreate,

)

from app.ai_service import (

    test_groq_connection,

    extract_required_skills,

    generate_learning_roadmap,

)

from app.skills import SkillGapRequest, analyze_skill_gaps


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the weekly market-demand scheduler
    if not scheduler.running:
        scheduler.start()
        print("Weekly market-demand scheduler started.")

    try:
        yield
    finally:
        # Stop the scheduler when FastAPI shuts down
        if scheduler.running:
            scheduler.shutdown(wait=False)
            print("Weekly market-demand scheduler stopped.")


app = FastAPI(
    title="AI Skill Gap Coach",
    description="A personalized career learning assistant",
    version="1.0.0",
    lifespan=lifespan,
)


# Create database tables, including the new market observations table.

Base.metadata.create_all(bind=engine)

class JobDescriptionRequest(BaseModel):

    job_description: str = Field(

        ...,

        min_length=50,

        description="Paste the complete job description",

    )

class RoadmapRequest(BaseModel):

    target_role: str = Field(..., min_length=2)

    current_skills: list[str] = Field(..., min_length=1)

    missing_skills: list[dict] = Field(..., min_length=1)

    hours_per_week: int = Field(..., ge=1, le=40)

class SavedRoadmapRequest(BaseModel):

    job_description: str = Field(..., min_length=50)

    hours_per_week: int = Field(..., ge=1, le=40)

@app.get("/")

def home():

    return {

        "message": "Welcome to AI Skill Gap Coach!",

        "status": "Backend is running successfully",

    }

@app.get("/test-groq")

def test_groq():

    try:

        return {"message": test_groq_connection()}

    except Exception as e:

        print(f"Groq error: {type(e).__name__}: {e}")

        raise HTTPException(

            status_code=502,

            detail="Groq connection test failed.",

        )

@app.post("/analyze-job-description")

def analyze_job_description(request: JobDescriptionRequest):

    try:

        return extract_required_skills(request.job_description)

    except Exception as e:

        print(f"Job analysis error: {type(e).__name__}: {e}")

        raise HTTPException(

            status_code=502,

            detail="Unable to analyze the job description.",

        )

@app.post("/skill-gap")

def skill_gap(request: SkillGapRequest):

    try:

        return analyze_skill_gaps(request)

    except Exception as e:

        print(f"Skill gap error: {type(e).__name__}: {e}")

        raise HTTPException(

            status_code=500,

            detail="Unable to calculate skill gaps.",

        )

@app.post("/generate-roadmap")

def generate_roadmap(request: RoadmapRequest):

    try:

        return generate_learning_roadmap(

            target_role=request.target_role,

            current_skills=request.current_skills,

            missing_skills=request.missing_skills,

            hours_per_week=request.hours_per_week,

        )

    except Exception as e:

        print(f"Roadmap error: {type(e).__name__}: {e}")

        raise HTTPException(

            status_code=502,

            detail="Unable to generate the learning roadmap.",

        )

# ---------------- USER PROFILES ----------------

@app.post("/profiles")

def create_profile(

    request: UserProfileCreate,

    db: Session = Depends(get_db),

):

    profile = UserProfile(

        name=request.name.strip(),

        target_role=request.target_role.strip(),

        current_skills=json.dumps(request.current_skills),

    )

    db.add(profile)

    db.commit()

    db.refresh(profile)

    return {

        "id": profile.id,

        "name": profile.name,

        "target_role": profile.target_role,

        "current_skills": json.loads(profile.current_skills),

    }

@app.get("/profiles/{profile_id}")

def get_profile(

    profile_id: int,

    db: Session = Depends(get_db),

):

    profile = db.query(UserProfile).filter(

        UserProfile.id == profile_id

    ).first()

    if profile is None:

        raise HTTPException(

            status_code=404,

            detail="User profile not found",

        )

    return {

        "id": profile.id,

        "name": profile.name,

        "target_role": profile.target_role,

        "current_skills": json.loads(profile.current_skills),

    }

@app.post("/profiles/{profile_id}/analyze-job")

def analyze_profile_against_job(

    profile_id: int,

    request: JobDescriptionRequest,

    db: Session = Depends(get_db),

):

    profile = db.query(UserProfile).filter(

        UserProfile.id == profile_id

    ).first()

    if profile is None:

        raise HTTPException(

            status_code=404,

            detail="User profile not found",

        )

    try:

        job_analysis = extract_required_skills(

            request.job_description

        )

        gap_request = SkillGapRequest(

            current_skills=json.loads(profile.current_skills),

            required_skills=job_analysis["required_skills"],

        )

        gap_result = analyze_skill_gaps(gap_request)

        return {

            "profile_id": profile.id,

            "target_role": profile.target_role,

            "job_title": job_analysis.get(

                "job_title", profile.target_role

            ),

            "skill_analysis": gap_result,

        }

    except Exception as e:

        print(

            f"Profile job analysis error: {type(e).__name__}: {e}"

        )

        raise HTTPException(

            status_code=502,

            detail="Unable to analyze this job description.",

        )

# ---------------- GENERATE AND SAVE ROADMAP ----------------

@app.post("/profiles/{profile_id}/generate-and-save-roadmap")

def generate_and_save_roadmap(

    profile_id: int,

    request: SavedRoadmapRequest,

    db: Session = Depends(get_db),

):

    profile = db.query(UserProfile).filter(

        UserProfile.id == profile_id

    ).first()

    if profile is None:

        raise HTTPException(

            status_code=404,

            detail="User profile not found",

        )

    try:

        current_skills = json.loads(profile.current_skills)

        job_analysis = extract_required_skills(

            request.job_description

        )

        gap_request = SkillGapRequest(

            current_skills=current_skills,

            required_skills=job_analysis["required_skills"],

        )

        gap_result = analyze_skill_gaps(gap_request)

        if not gap_result["missing_skills"]:

            raise HTTPException(

                status_code=400,

                detail=(

                    "No missing skills found. A new learning "

                    "roadmap is not needed."

                ),

            )

        roadmap = generate_learning_roadmap(

            target_role=profile.target_role,

            current_skills=current_skills,

            missing_skills=gap_result["missing_skills"],

            hours_per_week=request.hours_per_week,

        )

        saved_roadmap = LearningRoadmap(

            user_id=profile.id,

            title=f"{profile.target_role} Learning Roadmap",

            roadmap_data=json.dumps(roadmap),

        )

        db.add(saved_roadmap)

        db.commit()

        db.refresh(saved_roadmap)

        return {

            "roadmap_id": saved_roadmap.id,

            "profile_id": profile.id,

            "title": saved_roadmap.title,

            "skill_match_percentage": gap_result[

                "skill_match_percentage"

            ],

            "roadmap": roadmap,

            "saved": True,

        }

    except HTTPException:

        raise

    except Exception as e:

        db.rollback()

        print(f"Roadmap save error: {type(e).__name__}: {e}")

        raise HTTPException(

            status_code=502,

            detail="Unable to generate and save the roadmap.",

        )

# ---------------- RETRIEVE SAVED ROADMAP ----------------

@app.get("/roadmaps/{roadmap_id}")

def get_saved_roadmap(

    roadmap_id: int,

    db: Session = Depends(get_db),

):

    roadmap = db.query(LearningRoadmap).filter(

        LearningRoadmap.id == roadmap_id

    ).first()

    if roadmap is None:

        raise HTTPException(

            status_code=404,

            detail="Roadmap not found",

        )

    return {

        "roadmap_id": roadmap.id,

        "profile_id": roadmap.user_id,

        "title": roadmap.title,

        "roadmap": json.loads(roadmap.roadmap_data),

        "created_at": roadmap.created_at,

    }

# ---------------- UPDATE LEARNING PROGRESS ----------------

@app.put("/roadmaps/{roadmap_id}/progress/{week}")

def update_learning_progress(

    roadmap_id: int,

    week: int,

    request: LearningProgressUpdate,

    db: Session = Depends(get_db),

):

    roadmap = db.query(LearningRoadmap).filter(

        LearningRoadmap.id == roadmap_id

    ).first()

    if roadmap is None:

        raise HTTPException(

            status_code=404,

            detail="Roadmap not found",

        )

    roadmap_data = json.loads(roadmap.roadmap_data)

    weekly_items = roadmap_data.get("roadmap", [])

    week_item = next(

        (

            item for item in weekly_items

            if item.get("week") == week

        ),

        None,

    )

    if week_item is None:

        raise HTTPException(

            status_code=404,

            detail="Week not found in this roadmap",

        )

    progress = db.query(LearningProgress).filter(

        LearningProgress.roadmap_id == roadmap_id,

        LearningProgress.week == week,

    ).first()

    if progress is None:

        progress = LearningProgress(

            roadmap_id=roadmap_id,

            week=week,

            skill=week_item.get("skill", "Unknown skill"),

        )

        db.add(progress)

    progress.status = request.status

    progress.notes = request.notes

    db.commit()

    db.refresh(progress)

    return {

        "message": "Learning progress updated successfully",

        "roadmap_id": roadmap_id,

        "week": progress.week,

        "skill": progress.skill,

        "status": progress.status,

        "notes": progress.notes,

    }

# ---------------- VIEW LEARNING PROGRESS ----------------

@app.get("/roadmaps/{roadmap_id}/progress")

def get_learning_progress(

    roadmap_id: int,

    db: Session = Depends(get_db),

):

    roadmap = db.query(LearningRoadmap).filter(

        LearningRoadmap.id == roadmap_id

    ).first()

    if roadmap is None:

        raise HTTPException(

            status_code=404,

            detail="Roadmap not found",

        )

    progress_items = db.query(LearningProgress).filter(

        LearningProgress.roadmap_id == roadmap_id

    ).order_by(LearningProgress.week).all()

    return {

        "roadmap_id": roadmap_id,

        "total_progress_records": len(progress_items),

        "progress": [

            {

                "week": item.week,

                "skill": item.skill,

                "status": item.status,

                "notes": item.notes,

                "updated_at": item.updated_at,

            }

            for item in progress_items

        ],

    }

# ---------------- PROGRESS SUMMARY ----------------

@app.get("/roadmaps/{roadmap_id}/progress-summary")

def get_progress_summary(

    roadmap_id: int,

    db: Session = Depends(get_db),

):

    roadmap = db.query(LearningRoadmap).filter(

        LearningRoadmap.id == roadmap_id

    ).first()

    if roadmap is None:

        raise HTTPException(

            status_code=404,

            detail="Roadmap not found",

        )

    roadmap_data = json.loads(roadmap.roadmap_data)

    weekly_items = roadmap_data.get("roadmap", [])

    total_weeks = len(weekly_items)

    progress_items = db.query(LearningProgress).filter(

        LearningProgress.roadmap_id == roadmap_id

    ).all()

    completed_weeks = sum(

        1 for item in progress_items

        if item.status == "completed"

    )

    in_progress_weeks = sum(

        1 for item in progress_items

        if item.status == "in_progress"

    )

    not_started_weeks = max(

        0, total_weeks - completed_weeks - in_progress_weeks

    )

    completion_percentage = (

        round(completed_weeks / total_weeks * 100, 2)

        if total_weeks else 0

    )

    return {

        "roadmap_id": roadmap_id,

        "total_weeks": total_weeks,

        "completed_weeks": completed_weeks,

        "in_progress_weeks": in_progress_weeks,

        "not_started_weeks": not_started_weeks,

        "completion_percentage": completion_percentage,

    }

# ---------------- USER DASHBOARD ----------------

@app.get("/profiles/{profile_id}/dashboard")

def get_user_dashboard(

    profile_id: int,

    db: Session = Depends(get_db),

):

    profile = db.query(UserProfile).filter(

        UserProfile.id == profile_id

    ).first()

    if profile is None:

        raise HTTPException(

            status_code=404,

            detail="User profile not found",

        )

    roadmaps = db.query(LearningRoadmap).filter(

        LearningRoadmap.user_id == profile_id

    ).order_by(LearningRoadmap.id.desc()).all()

    roadmap_summaries = []

    for roadmap in roadmaps:

        roadmap_data = json.loads(roadmap.roadmap_data)

        weekly_items = roadmap_data.get("roadmap", [])

        total_weeks = len(weekly_items)

        progress_items = db.query(LearningProgress).filter(

            LearningProgress.roadmap_id == roadmap.id

        ).all()

        completed_weeks = sum(

            1 for item in progress_items

            if item.status == "completed"

        )

        in_progress_weeks = sum(

            1 for item in progress_items

            if item.status == "in_progress"

        )

        not_started_weeks = max(

            0, total_weeks - completed_weeks - in_progress_weeks

        )

        completion_percentage = (

            round(completed_weeks / total_weeks * 100, 2)

            if total_weeks else 0

        )

        roadmap_summaries.append({

            "roadmap_id": roadmap.id,

            "title": roadmap.title,

            "total_weeks": total_weeks,

            "completed_weeks": completed_weeks,

            "in_progress_weeks": in_progress_weeks,

            "not_started_weeks": not_started_weeks,

            "completion_percentage": completion_percentage,

        })

    return {

        "profile": {

            "id": profile.id,

            "name": profile.name,

            "target_role": profile.target_role,

            "current_skills": json.loads(profile.current_skills),

        },

        "total_roadmaps": len(roadmaps),

        "roadmaps": roadmap_summaries,

    }

# ---------------- RECORD MARKET SKILL OBSERVATIONS ----------------

@app.post("/market-observations")

def create_market_observation(

    request: MarketSkillObservationCreate,

    db: Session = Depends(get_db),

):

    demand_percentage = round(

        request.posting_count / request.total_postings * 100,

        2,

    )

    observation = MarketSkillObservation(

        target_role=request.target_role.strip(),

        skill=request.skill.strip(),

        posting_count=request.posting_count,

        total_postings=request.total_postings,

        demand_percentage=demand_percentage,

        source=request.source.strip(),

    )

    try:

        db.add(observation)

        db.commit()

        db.refresh(observation)

        return {

            "message": "Market skill observation saved successfully",

            "id": observation.id,

            "target_role": observation.target_role,

            "skill": observation.skill,

            "posting_count": observation.posting_count,

            "total_postings": observation.total_postings,

            "demand_percentage": observation.demand_percentage,

            "source": observation.source,

            "observed_at": observation.observed_at,

        }

    except Exception as e:

        db.rollback()

        print(

            f"Market observation error: {type(e).__name__}: {e}"

        )

        raise HTTPException(

            status_code=500,

            detail="Unable to save the market skill observation.",

        )

# ---------------- COMPARE MARKET SKILL OBSERVATIONS ----------------

@app.get("/market-demand/trends")

def get_market_demand_trends(

    target_role: str = Query(..., min_length=2, max_length=150),

    db: Session = Depends(get_db),

):

    observations = db.query(MarketSkillObservation).filter(

        MarketSkillObservation.target_role.ilike(

            target_role.strip()

        )

    ).order_by(

        MarketSkillObservation.observed_at.asc(),

        MarketSkillObservation.id.asc(),

    ).all()

    if not observations:

        return {

            "target_role": target_role,

            "message": "No market observations have been recorded for this role.",

            "skills": [],

        }

    # Group observations by skill.

    grouped = {}

    for item in observations:

        skill_key = item.skill.strip().casefold()

        if skill_key not in grouped:

            grouped[skill_key] = {

                "skill": item.skill,

                "observations": [],

            }

        grouped[skill_key]["observations"].append({

            "posting_count": item.posting_count,

            "total_postings": item.total_postings,

            "demand_percentage": item.demand_percentage,

            "source": item.source,

            "observed_at": item.observed_at,

        })

    trends = []

    for data in grouped.values():

        history = data["observations"]

        first = history[0]

        latest = history[-1]

        change = round(

            latest["demand_percentage"]

            - first["demand_percentage"],

            2,

        )

        if len(history) < 2:

            trend = "insufficient_data"

        elif change > 0:

            trend = "increasing"

        elif change < 0:

            trend = "decreasing"

        else:

            trend = "unchanged"

        trends.append({

            "skill": data["skill"],

            "observation_count": len(history),

            "earliest_demand_percentage": first[

                "demand_percentage"

            ],

            "latest_demand_percentage": latest[

                "demand_percentage"

            ],

            "change_percentage_points": change,

            "trend": trend,

            "history": history,

        })

    trends.sort(

        key=lambda item: item["latest_demand_percentage"],

        reverse=True,

    )

    return {

        "target_role": target_role,

        "total_observations": len(observations),

        "skills": trends,

    }





# ---------------- UPDATE ROADMAP USING MARKET DEMAND ----------------

@app.post("/roadmaps/{roadmap_id}/update-market-priorities")
def update_roadmap_market_priorities(
    roadmap_id: int,
    db: Session = Depends(get_db),
):
    """
    Update a saved roadmap using market-demand observations.

    Completed and in-progress weeks remain unchanged.
    Not-started weeks are reprioritized using relevant market skills.
    The roadmap keeps its original number of weeks.
    """

    saved_roadmap = (
        db.query(LearningRoadmap)
        .filter(LearningRoadmap.id == roadmap_id)
        .first()
    )

    if saved_roadmap is None:
        raise HTTPException(status_code=404, detail="Roadmap not found")

    profile = (
        db.query(UserProfile)
        .filter(UserProfile.id == saved_roadmap.user_id)
        .first()
    )

    if profile is None:
        raise HTTPException(status_code=404, detail="User profile not found")

    target_role = profile.target_role.strip()

    observations = (
        db.query(MarketSkillObservation)
        .filter(
            MarketSkillObservation.target_role.ilike(target_role)
        )
        .order_by(
            MarketSkillObservation.observed_at.asc(),
            MarketSkillObservation.id.asc(),
        )
        .all()
    )

    if not observations:
        raise HTTPException(
            status_code=404,
            detail=f"No market observations found for '{target_role}'.",
        )

    def normalize_skill(value):
        return " ".join(str(value or "").casefold().split())

    # Build demand history for each skill.
    grouped = {}

    for observation in observations:
        key = normalize_skill(observation.skill)
        grouped.setdefault(key, []).append(observation)

    market_by_skill = {}

    for key, history in grouped.items():
        first = history[0]
        latest = history[-1]

        change = round(
            latest.demand_percentage - first.demand_percentage, 2
        )

        if len(history) < 2:
            trend = "insufficient_data"
        elif change > 0:
            trend = "increasing"
        elif change < 0:
            trend = "decreasing"
        else:
            trend = "unchanged"

        market_by_skill[key] = {
            "skill": latest.skill,
            "latest_demand_percentage": latest.demand_percentage,
            "change_percentage_points": change,
            "trend": trend,
            "source": latest.source,
            "observed_at": (
                latest.observed_at.isoformat()
                if latest.observed_at else None
            ),
        }

    try:
        roadmap_data = json.loads(saved_roadmap.roadmap_data)
    except (TypeError, json.JSONDecodeError):
        raise HTTPException(
            status_code=500,
            detail="The saved roadmap contains invalid JSON.",
        )

    weekly_items = roadmap_data.get("roadmap", [])

    if not isinstance(weekly_items, list) or not weekly_items:
        raise HTTPException(
            status_code=400,
            detail="The saved roadmap has no weekly learning items.",
        )

    # Find progress records so protected weeks are not modified.
    progress_records = (
        db.query(LearningProgress)
        .filter(LearningProgress.roadmap_id == roadmap_id)
        .all()
    )

    progress_by_week = {
        record.week: record.status for record in progress_records
    }

    fixed_items = []
    pending_items = []

    for item in weekly_items:
        week_number = item.get("week")
        status = progress_by_week.get(week_number, "not_started")

        if status in {"completed", "in_progress"}:
            fixed_items.append(item)
        else:
            pending_items.append(item)

    fixed_week_numbers = {
        item.get("week") for item in fixed_items
    }

    pending_week_numbers = [
        item.get("week") for item in pending_items
    ]

    existing_skills = {
        normalize_skill(item.get("skill"))
        for item in weekly_items
        if item.get("skill")
    }

    # Select high-demand skills that are not already in the roadmap.
    # The current profile skills are also excluded.
    current_skills = json.loads(profile.current_skills or "[]")
    current_skill_names = {
        normalize_skill(skill) for skill in current_skills
    }

    candidates = []

    for key, market in market_by_skill.items():
        if key in existing_skills or key in current_skill_names:
            continue

        candidates.append(market)

    candidates.sort(
        key=lambda market: (
            market["latest_demand_percentage"],
            market["change_percentage_points"],
        ),
        reverse=True,
    )

    # Generate complete learning content for selected additional skills.
    # Existing AI service is used so objectives/tasks/projects are generated
    # rather than fabricated by this endpoint.
    generated_items = []

    if candidates and pending_items:
        selected_skills = candidates[:len(pending_items)]

        missing_skills = [
            {
                "skill": market["skill"],
                "importance": "high",
                "reason": (
                    f"Market demand is {market['latest_demand_percentage']}%; "
                    f"trend is {market['trend']} "
                    f"({market['change_percentage_points']:+.2f} percentage points)."
                ),
            }
            for market in selected_skills
        ]

        try:
            generated_roadmap = generate_learning_roadmap(
                target_role=target_role,
                current_skills=current_skills,
                missing_skills=missing_skills,
                hours_per_week=max(
                    1,
                    min(
                        40,
                        int(
                            sum(
                                item.get("estimated_hours", 5)
                                for item in pending_items
                            ) / max(len(pending_items), 1)
                        ),
                    ),
                ),
            )

            generated_items = generated_roadmap.get("roadmap", [])

            if not isinstance(generated_items, list):
                generated_items = []

        except Exception as error:
            print(
                "Unable to generate market-based learning content: "
                f"{type(error).__name__}: {error}"
            )
            raise HTTPException(
                status_code=502,
                detail=(
                    "Could not generate learning tasks for the new "
                    "market-priority skills. The saved roadmap was not updated."
                ),
            )

    # Only use generated items that contain a skill name.
    generated_by_skill = {}

    for item in generated_items:
        skill_key = normalize_skill(item.get("skill"))
        if skill_key:
            generated_by_skill[skill_key] = item

    replacements = []

    for market in candidates:
        key = normalize_skill(market["skill"])
        generated = generated_by_skill.get(key)

        if not generated:
            continue

        replacement = dict(generated)
        replacement["skill"] = market["skill"]
        replacement["market_demand"] = {
            "latest_demand_percentage":
                market["latest_demand_percentage"],
            "change_percentage_points":
                market["change_percentage_points"],
            "trend": market["trend"],
            "source": market["source"],
            "observed_at": market["observed_at"],
        }

        replacements.append(replacement)

        if len(replacements) >= len(pending_items):
            break

    # Existing pending items are retained if the AI service does not
    # generate enough valid replacement skills.
    for item in pending_items:
        key = normalize_skill(item.get("skill"))
        market = market_by_skill.get(key)

        if market:
            item["market_demand"] = {
                "latest_demand_percentage":
                    market["latest_demand_percentage"],
                "change_percentage_points":
                    market["change_percentage_points"],
                "trend": market["trend"],
                "source": market["source"],
                "observed_at": market["observed_at"],
            }
        else:
            item["market_demand"] = {
                "message": "No exact market observation available."
            }

    # Prefer generated market-priority items, then retain remaining
    # original pending items.
    replacement_count = min(len(replacements), len(pending_items))
    updated_pending = (
        replacements[:replacement_count]
        + pending_items[replacement_count:]
    )

    # Keep original week numbers and preserve protected weeks.
    pending_by_week = {}

    for week_number, item in zip(
        pending_week_numbers, updated_pending
    ):
        updated_item = dict(item)
        updated_item["week"] = week_number
        pending_by_week[week_number] = updated_item

    fixed_by_week = {
        item.get("week"): item for item in fixed_items
    }

    updated_weeks = []

    for original_item in weekly_items:
        week_number = original_item.get("week")

        if week_number in fixed_week_numbers:
            updated_weeks.append(fixed_by_week[week_number])
        else:
            updated_weeks.append(
                pending_by_week.get(week_number, original_item)
            )

    # Record recommendations that were not placed into the schedule.
    scheduled_skills = {
        normalize_skill(item.get("skill"))
        for item in updated_weeks
        if item.get("skill")
    }

    additional_skills = [
        {
            "skill": market["skill"],
            "latest_demand_percentage":
                market["latest_demand_percentage"],
            "change_percentage_points":
                market["change_percentage_points"],
            "trend": market["trend"],
            "source": market["source"],
        }
        for key, market in market_by_skill.items()
        if key not in scheduled_skills
        and key not in current_skill_names
    ]

    additional_skills.sort(
        key=lambda item: (
            item["latest_demand_percentage"],
            item["change_percentage_points"],
        ),
        reverse=True,
    )

    roadmap_data["roadmap"] = updated_weeks
    roadmap_data["market_skill_recommendations"] = additional_skills
    roadmap_data["market_demand_update"] = {
        "updated": True,
        "target_role": target_role,
        "observations_used": len(observations),
        "protected_weeks": sorted(
            week for week in fixed_week_numbers if week is not None
        ),
        "note": (
            "Pending weeks were updated using generated learning content "
            "for skills with high recorded market demand. Completed and "
            "in-progress weeks were preserved. Synthetic sample data is "
            "illustrative and is not verified real-world job-market data."
        ),
    }

    try:
        saved_roadmap.roadmap_data = json.dumps(roadmap_data)
        db.commit()
        db.refresh(saved_roadmap)

    except Exception as error:
        db.rollback()
        print(
            f"Market-based roadmap update error: "
            f"{type(error).__name__}: {error}"
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to save the market-based roadmap update.",
        )

    return {
        "message": "Roadmap updated using market-demand observations.",
        "roadmap_id": saved_roadmap.id,
        "profile_id": profile.id,
        "target_role": target_role,
        "preserved_completed_and_in_progress_weeks": True,
        "scheduled_market_skills": [
            item.get("skill")
            for item in updated_weeks
            if item.get("market_demand", {}).get(
                "latest_demand_percentage"
            ) is not None
        ],
        "additional_market_skills": additional_skills,
        "roadmap": roadmap_data,
    }


# ---------------- AUTOMATIC WEEKLY MARKET UPDATES ----------------

# ---------------- AUTOMATIC WEEKLY MARKET UPDATES ----------------

def run_weekly_market_updates():
    """Update saved roadmaps using stored market observations."""
    db = get_background_db()

    try:
        roadmap_ids = [
            roadmap_id
            for (roadmap_id,) in db.query(LearningRoadmap.id).all()
        ]

        for roadmap_id in roadmap_ids:
            try:
                update_roadmap_market_priorities(
                    roadmap_id=roadmap_id,
                    db=db,
                )
                print(
                    f"Weekly market update completed for roadmap {roadmap_id}"
                )

            except Exception as error:
                db.rollback()
                print(
                    f"Weekly market update failed for roadmap "
                    f"{roadmap_id}: {error}"
                )

    finally:
        db.close()

# ---------------- SCHEDULER CONFIGURATION ----------------

scheduler = BackgroundScheduler(
    timezone=ZoneInfo("Asia/Kolkata")
)

scheduler.add_job(
    run_weekly_market_updates,
    trigger=CronTrigger(
        day_of_week="mon",
        hour=9,
        minute=0,
        timezone=ZoneInfo("Asia/Kolkata"),
    ),
    id="weekly_market_updates",
    replace_existing=True,
    max_instances=1,
    coalesce=True,
)

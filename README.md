#  AI Skill Gap Coach

A personalized career learning assistant. Paste a job description, see your skill gaps, get an AI-generated weekly learning roadmap, and track your progress.

Built with **FastAPI**, **Streamlit**, **SQLite**, and the **Groq API**.

##  Features

- Create a profile with your target role and current skills
- AI extracts required skills from any job description
- Skill gap analysis with match percentage
- Personalized weekly learning roadmap (objectives, practice task, mini project)
- Progress tracking per week with a completion summary
- Market demand trends and market-based roadmap updates
- Weekly automatic roadmap refresh (Mondays, 09:00 IST)

##  Tech Stack

FastAPI · Streamlit · SQLAlchemy (SQLite) · Groq API (`openai/gpt-oss-20b`) · APScheduler

##  Project Structure

```
ai-skill-gap-coach/
├── backend/
│   ├── app/
│   │   ├── main.py          # API endpoints + scheduler
│   │   ├── ai_service.py    # Groq integration
│   │   ├── skills.py        # Skill gap logic
│   │   ├── models.py        # Database models
│   │   ├── schemas.py       # Request schemas
│   │   └── database.py      # DB connection
│   ├── seed_market_data.py
│   ├── job_market_sample_dataset.csv
│   ├── requirements.txt
│   └── .env                 # not committed
└── frontend/
    └── app.py               # Streamlit UI
```

## 🚀 Setup

**Requirements:** Python 3.10+ and a free [Groq API key](https://console.groq.com).

```bash
# 1. Clone
git clone https://github.com/<your-username>/ai-skill-gap-coach.git
cd ai-skill-gap-coach

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install fastapi "uvicorn[standard]" sqlalchemy pydantic python-dotenv groq apscheduler requests streamlit python-multipart
```

Create `backend/.env`:

```env
GROQ_API_KEY=your_groq_api_key_here
```

##  Run

Use two terminals (virtual environment activated in both).

**Backend:**
```bash
cd backend
uvicorn app.main:app --reload
```
API docs: http://127.0.0.1:8000/docs

**Load sample market data (optional, once):**
```bash
cd backend
python seed_market_data.py
```

**Frontend:**
```bash
cd frontend
streamlit run app.py
```
Open http://localhost:8501

## 📖 How to Use

1. **Create a profile**: name, target role, comma-separated skills. Note the Profile ID.
2. **Analyze a job description**: see your match %, matched skills, and missing skills.
3. **Generate a roadmap**: choose weekly study hours. Note the Roadmap ID.
4. **Track progress**: mark each week as not started, in progress, or completed.
5. **Market demand**: view skill trends for a role and update pending weeks.

## 📡 Main API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/profiles` | Create profile |
| POST | `/profiles/{id}/analyze-job` | Skill gap analysis |
| POST | `/profiles/{id}/generate-and-save-roadmap` | Generate and save roadmap |
| GET | `/roadmaps/{id}` | Get saved roadmap |
| PUT | `/roadmaps/{id}/progress/{week}` | Update week progress |
| GET | `/roadmaps/{id}/progress-summary` | Completion summary |
| GET | `/profiles/{id}/dashboard` | All roadmaps for a profile |
| GET | `/market-demand/trends?target_role=...` | Skill demand trends |
| POST | `/roadmaps/{id}/update-market-priorities` | Reprioritize pending weeks |

##  Notes

- The sample market dataset is **synthetic** and not real job-market data.
- Skill matching is exact (case-insensitive), so "JS" and "JavaScript" are treated as different skills.
- There is no authentication; this project is intended for local use and demos.



import requests

import streamlit as st



API_URL = "http://127.0.0.1:8000"



st.set_page_config(

          page_title="AI Skill Gap Coach",

          page_icon="🎯",

          layout="wide"

)



st.title("🎯 AI Skill Gap Coach")

st.subheader("Your Personalized Career Learning Assistant")



st.write(

          "Analyze job descriptions, identify skill gaps, "

          "generate personalized learning roadmaps, and track your progress."

)



st.divider()



# ---------------- PROFILE CREATION ----------------



st.header("👤 Create Your Profile")



with st.form("profile_form"):

          name = st.text_input("Your Name")

          target_role = st.text_input(

                    "Target Job Role",

                    placeholder="e.g., Python Developer"

          )

          skills_input = st.text_area(

                    "Your Current Skills",

                    placeholder="Python, SQL, Git"

          )



          profile_submitted = st.form_submit_button("Create Profile")



if profile_submitted:

          current_skills = [

                    skill.strip()

                    for skill in skills_input.split(",")

                    if skill.strip()

          ]



          if not name.strip() or not target_role.strip() or not current_skills:

                    st.error("Please fill in all the fields.")

          else:

                    profile_data = {

                              "name": name.strip(),

                              "target_role": target_role.strip(),

                              "current_skills": current_skills

                    }



                    try:

                              with st.spinner("Saving your profile..."):

                                        response = requests.post(

                                                  f"{API_URL}/profiles",

                                                  json=profile_data,

                                                  timeout=15

                                        )



                              if response.status_code == 200:

                                        profile = response.json()

                                        st.session_state["profile"] = profile



                                        st.success("Your profile has been saved successfully!")

                                        st.write("**Profile ID:**", profile["id"])

                                        st.write("**Name:**", profile["name"])

                                        st.write("**Target Role:**", profile["target_role"])

                                        st.write(

                                                  "**Current Skills:**",

                                                  ", ".join(profile["current_skills"])

                                        )

                              else:

                                        st.error(

                                                  f"Unable to save profile: "

                                                  f"{response.status_code} - {response.text}"

                                        )



                    except requests.exceptions.RequestException as error:

                              st.error(f"Could not connect to the backend: {error}")





# ---------------- LOAD EXISTING PROFILE ----------------



st.divider()

st.header("📄 Analyze a Job Description")



profile_id_input = st.number_input(

          "Profile ID",

          min_value=1,

          step=1,

          value=int(st.session_state.get("profile", {}).get("id", 1))

)



job_description = st.text_area(

          "Paste the Job Description",

          height=220,

          placeholder=(

                    "We are looking for a Data Scientist proficient in Python, "

                    "SQL, Pandas, NumPy, machine learning, statistics, and "

                    "data visualization..."

          )

)



if st.button("Analyze Job Description"):

          if len(job_description.strip()) < 50:

                    st.warning("Please enter a job description of at least 50 characters.")

          else:

                    try:

                              with st.spinner("Analyzing the job description with AI..."):

                                        response = requests.post(

                                                  f"{API_URL}/profiles/{int(profile_id_input)}/analyze-job",

                                                  json={"job_description": job_description.strip()},

                                                  timeout=90

                                        )



                              if response.status_code == 200:

                                        result = response.json()

                                        skill_analysis = result["skill_analysis"]



                                        st.success("Job description analyzed successfully!")



                                        st.subheader("🎯 Job Analysis")

                                        st.write("**Target Role:**", result["target_role"])

                                        st.write("**Job Title:**", result["job_title"])



                                        st.subheader("📊 Skill Match")

                                        match_percentage = skill_analysis["skill_match_percentage"]

                                        st.metric("Skill Match", f"{match_percentage}%")

                                        st.progress(match_percentage / 100)



                                        col1, col2 = st.columns(2)



                                        with col1:

                                                  st.markdown("### ✅ Matched Skills")

                                                  matched = skill_analysis["matched_skills"]



                                                  if matched:

                                                            for item in matched:

                                                                      st.write(f"**{item['skill']}**")

                                                                      if item.get("reason"):

                                                                                st.caption(item["reason"])

                                                  else:

                                                            st.info("No matching skills found.")



                                        with col2:

                                                  st.markdown("### 📚 Missing Skills")

                                                  missing = skill_analysis["missing_skills"]



                                                  if missing:

                                                            for item in missing:

                                                                      st.write(

                                                                                f"**{item['skill']}** "

                                                                                f"— Importance: {item['importance']}"

                                                                      )

                                                                      if item.get("reason"):

                                                                                st.caption(item["reason"])

                                                  else:

                                                            st.success("No missing skills identified!")



                                        st.session_state["last_skill_analysis"] = result



                              else:

                                        st.error(

                                                  f"Analysis failed: HTTP {response.status_code}. "

                                                  "Check the profile ID and backend logs."

                                        )



                    except requests.exceptions.Timeout:

                              st.error("The AI request took too long. Please try again.")

                    except requests.exceptions.RequestException as error:

                              st.error(f"Could not connect to the backend: {error}")

                    except (KeyError, ValueError, TypeError):

                              st.error("The backend returned an unexpected response.")



# ---------------- LEARNING ROADMAP GENERATION ----------------



st.divider()

st.header("🗺️ Generate Your Learning Roadmap")



st.write(

          "Create a personalized learning plan based on your "

          "missing skills and available study time."

)



roadmap_profile_id = st.number_input(

          "Profile ID for Roadmap",

          min_value=1,

          step=1,

          value=int(st.session_state.get("profile", {}).get("id", 1)),

          key="roadmap_profile_id"

)



hours_per_week = st.slider(

          "Available study hours per week",

          min_value=1,

          max_value=40,

          value=6

)



if st.button("Generate Learning Roadmap"):

          if "last_skill_analysis" not in st.session_state:

                    st.warning(

                              "Please analyze a job description first before generating a roadmap."

                    )

          else:

                    try:

                              with st.spinner("Generating your personalized roadmap..."):

                                        response = requests.post(

                                                  f"{API_URL}/profiles/"

                                                  f"{int(roadmap_profile_id)}/generate-and-save-roadmap",

                                                  json={

                                                            "job_description": job_description.strip(),

                                                            "hours_per_week": hours_per_week

                                                  },

                                                  timeout=120

                                        )



                              if response.status_code == 200:

                                        roadmap_result = response.json()

                                        st.session_state["saved_roadmap"] = roadmap_result



                                        st.success("Your learning roadmap has been generated and saved!")



                                        st.metric(

                                                  "Skill Match",

                                                  f"{roadmap_result['skill_match_percentage']}%"

                                        )



                                        roadmap = roadmap_result["roadmap"]



                                        st.subheader(

                                                  f"🗓️ {roadmap.get('estimated_duration_weeks', 0)}-Week Plan"

                                        )



                                        for week_item in roadmap.get("roadmap", []):

                                                  with st.expander(

                                                            f"Week {week_item['week']}: {week_item['skill']}"

                                                  ):

                                                            st.markdown("**Learning Objectives**")

                                                            for objective in week_item.get(

                                                                      "learning_objectives", []

                                                            ):

                                                                      st.write(f"- {objective}")



                                                            st.write(

                                                                      "**Practice Task:**",

                                                                      week_item.get("practice_task", "Not specified")

                                                            )



                                                            st.write(

                                                                      "**Mini Project:**",

                                                                      week_item.get("mini_project", "Not specified")

                                                            )



                                                            st.write(

                                                                      "**Estimated Hours:**",

                                                                      week_item.get("estimated_hours", 0)

                                                            )



                                        st.info(

                                                  f"Roadmap ID: {roadmap_result['roadmap_id']} "

                                                  "— saved in your database."

                                        )



                              elif response.status_code == 400:

                                        st.warning(

                                                  "No missing skills were found. "

                                                  "Your current skills may already match the job requirements."

                                        )

                              else:

                                        st.error(

                                                  f"Roadmap generation failed: "

                                                  f"HTTP {response.status_code}."

                                        )



                    except requests.exceptions.Timeout:

                              st.error("Roadmap generation took too long. Please try again.")

                    except requests.exceptions.RequestException as error:

                              st.error(f"Could not connect to the backend: {error}")



# ---------------- LEARNING PROGRESS TRACKING ----------------



st.divider()

st.header("📈 Track Your Learning Progress")



progress_roadmap_id = st.number_input(

          "Roadmap ID for Progress",

          min_value=1,

          step=1,

          value=int(st.session_state.get("saved_roadmap", {}).get("roadmap_id", 1)),

          key="progress_roadmap_id"

)



progress_week = st.number_input(

          "Week Number",

          min_value=1,

          max_value=52,

          value=1,

          step=1

)



progress_status = st.selectbox(

          "Learning Status",

          options=["not_started", "in_progress", "completed"],

          format_func=lambda value: {

                    "not_started": "Not Started",

                    "in_progress": "In Progress",

                    "completed": "Completed"

          }[value]

)



progress_notes = st.text_area(

          "Progress Notes",

          placeholder="Describe what you learned or completed this week..."

)



if st.button("Update Learning Progress"):

          try:

                    with st.spinner("Saving your progress..."):

                              response = requests.put(

                                        f"{API_URL}/roadmaps/{int(progress_roadmap_id)}"

                                        f"/progress/{int(progress_week)}",

                                        json={

                                                  "status": progress_status,

                                                  "notes": progress_notes

                                        },

                                        timeout=30

                              )



                    if response.status_code == 200:

                              st.success("Learning progress updated successfully!")

                              st.json(response.json())

                    else:

                              st.error(

                                        f"Could not update progress: "

                                        f"HTTP {response.status_code} - {response.text}"

                              )



          except requests.exceptions.RequestException as error:

                    st.error(f"Could not connect to the backend: {error}")





# ---------------- VIEW LEARNING PROGRESS ----------------



if st.button("View Learning Progress"):

          try:

                    response = requests.get(

                              f"{API_URL}/roadmaps/{int(progress_roadmap_id)}/progress",

                              timeout=30

                    )



                    if response.status_code == 200:

                              progress_data = response.json()



                              st.subheader("Saved Progress")

                              st.write(

                                        "Total progress records:",

                                        progress_data["total_progress_records"]

                              )



                              if progress_data["progress"]:

                                        st.dataframe(

                                                  progress_data["progress"],

                                                  use_container_width=True

                                        )

                              else:

                                        st.info("No progress has been recorded yet.")

                    else:

                              st.error(

                                        f"Could not retrieve progress: "

                                        f"HTTP {response.status_code}"

                              )



          except requests.exceptions.RequestException as error:

                    st.error(f"Could not connect to the backend: {error}")





# ---------------- PROGRESS SUMMARY ----------------



if st.button("View Overall Progress"):

          try:

                    response = requests.get(

                              f"{API_URL}/roadmaps/{int(progress_roadmap_id)}"

                              "/progress-summary",

                              timeout=30

                    )



                    if response.status_code == 200:

                              summary = response.json()



                              st.subheader("Overall Learning Progress")



                              col1, col2, col3, col4 = st.columns(4)



                              col1.metric("Total Weeks", summary["total_weeks"])

                              col2.metric("Completed", summary["completed_weeks"])

                              col3.metric("In Progress", summary["in_progress_weeks"])

                              col4.metric("Completion", f"{summary['completion_percentage']}%")



                              st.progress(

                                        summary["completion_percentage"] / 100

                              )

                    else:

                              st.error(

                                        f"Could not retrieve summary: "

                                        f"HTTP {response.status_code}"

                              )



          except requests.exceptions.RequestException as error:

                    st.error(f"Could not connect to the backend: {error}")



# ---------------- MARKET DEMAND & SKILL UPDATES ----------------



st.divider()

st.header("📈 Market Demand & Skill Updates")



st.write(

          "Analyze a new job description to identify missing skills "

          "for your target role."

)



market_profile_id = st.number_input(

          "Profile ID for Market Comparison",

          min_value=1,

          step=1,

          value=int(st.session_state.get("profile", {}).get("id", 1)),

          key="market_profile_id"

)



market_job_description = st.text_area(

          "Paste a New Job Description",

          height=180,

          placeholder="Paste a recent job description here...",

          key="market_job_description"

)



if st.button("Analyze New Skill Requirements"):

          if len(market_job_description.strip()) < 50:

                    st.warning("Please enter at least 50 characters.")

          else:

                    try:

                              with st.spinner("Analyzing job requirements..."):

                                        response = requests.post(

                                                  f"{API_URL}/profiles/"

                                                  f"{int(market_profile_id)}/analyze-job",

                                                  json={

                                                            "job_description": market_job_description.strip()

                                                  },

                                                  timeout=90

                                        )



                              if response.status_code == 200:

                                        result = response.json()

                                        analysis = result["skill_analysis"]



                                        st.success("Job requirements analyzed successfully!")



                                        st.metric(

                                                  "Skill Match",

                                                  f"{analysis['skill_match_percentage']}%"

                                        )



                                        st.subheader("Skills to Consider Learning")



                                        missing_skills = analysis["missing_skills"]



                                        if missing_skills:

                                                  for item in missing_skills:

                                                            st.write(

                                                                      f"**{item['skill']}** "

                                                                      f"— Importance: {item['importance']}"

                                                            )

                                                            if item.get("reason"):

                                                                      st.caption(item["reason"])

                                        else:

                                                  st.success("No missing skills identified.")



                                        st.info(

                                                  "This version analyzes a supplied job description. "

                                                  "It does not yet measure actual market trends or "

                                                  "automatically update your roadmap."

                                        )



                              else:

                                        st.error(

                                                  f"Analysis failed: HTTP {response.status_code}"

                                        )



                    except requests.exceptions.RequestException as error:

                              st.error(f"Backend connection failed: {error}")





# ---------------- MARKET DEMAND TRENDS ----------------

st.divider()
st.header("📈 Market Demand Trends")
st.write(
    "Explore how the demand for skills changes for your target role."
)

default_role = st.session_state.get("profile", {}).get("target_role", "")
target_role = st.text_input(
    "Target Job Role",
    value=default_role,
    key="market_trends_target_role",
)

if st.button("View Market Demand Trends"):
    if not target_role.strip():
        st.warning("Please enter your target job role.")
    else:
        try:
            response = requests.get(
                f"{API_URL}/market-demand/trends",
                params={"target_role": target_role.strip()},
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                st.subheader(f"Target Role: {target_role.strip()}")

                skills = data.get("skills", [])
                if not skills:
                    st.info(
                        "No market observations found for this role yet. "
                        "Add observations through the backend API first."
                    )
                else:
                    st.metric(
                        "Total Observations",
                        data.get("total_observations", 0),
                    )

                    for item in skills:
                        with st.expander(item.get("skill", "Unknown skill")):
                            st.write(
                                "Latest demand: "
                                f'{item.get("latest_demand_percentage", 0)}%'
                            )
                            st.write(
                                "Earliest demand: "
                                f'{item.get("earliest_demand_percentage", 0)}%'
                            )
                            st.write(
                                "Change: "
                                f'{item.get("change_percentage_points", 0)} '
                                "percentage points"
                            )

                            trend = item.get("trend", "insufficient_data")
                            if trend == "increasing":
                                st.success("📈 Demand is increasing")
                            elif trend == "decreasing":
                                st.warning("📉 Demand is decreasing")
                            elif trend == "unchanged":
                                st.info("➡️ Demand is unchanged")
                            else:
                                st.info(
                                    "Not enough observations to identify a trend."
                                )

                            history = item.get("history", [])
                            if history:
                                st.markdown("**Observation history**")
                                st.dataframe(history, use_container_width=True)
            else:
                st.error(
                    f"API error ({response.status_code}): {response.text}"
                )

        except requests.exceptions.RequestException as error:
            st.error(f"Could not connect to the backend: {error}")

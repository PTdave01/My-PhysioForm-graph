import streamlit as st
import pandas as pd
from db import get_db
from queries import patients_with_issue, patient_similarity

st.set_page_config(page_title="PhysioGraph", layout="wide")

# Sidebar navigation
st.sidebar.title("PhysioGraph")
page = st.sidebar.radio(
    "Navigate",
    ["Dashboard", "Patients", "Patient Detail", "Clinicians", "Exercises", "Graph Queries"]
)

# Helper to get DB connection and handle errors
def get_db_safe():
    try:
        return get_db()
    except Exception as e:
        st.error(f"⚠️ Database unreachable: {str(e)}")
        return None

# Dashboard page
if page == "Dashboard":
    st.title("Dashboard")
    db = get_db_safe()
    if db:
        try:
            stats = {}
            for label in ["Patient", "Clinician", "Session", "Exercise", "Rep", "Feedback", "FormIssue"]:
                result = db.query(f"MATCH (n:{label}) RETURN count(n) AS count")
                stats[label] = result[0]["count"]
            cols = st.columns(4)
            for i, (label, count) in enumerate(stats.items()):
                with cols[i % 4]:
                    st.metric(label=label, value=count)
            st.info("Use the sidebar to explore patients, clinicians, exercises, and run graph queries.")
        except Exception as e:
            st.error(f"Query failed: {str(e)}")
        finally:
            db.close()

# Patients list
elif page == "Patients":
    st.title("Patients")
    db = get_db_safe()
    if db:
        try:
            query = """
                MATCH (p:Patient)
                OPTIONAL MATCH (p)-[:ASSIGNED_TO]->(c:Clinician)
                RETURN p.id AS id, p.name AS name, p.age AS age, p.condition AS condition, c.name AS clinician
                ORDER BY p.name
            """
            patients = db.query(query)
            if patients:
                df = pd.DataFrame(patients)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No patients found. Seed the database first.")
        except Exception as e:
            st.error(f"Query failed: {str(e)}")
        finally:
            db.close()

# Patient Detail (select patient)
elif page == "Patient Detail":
    st.title("Patient Detail")
    db = get_db_safe()
    if db:
        try:
            # Get list of patient IDs and names for selectbox
            patients = db.query("MATCH (p:Patient) RETURN p.id AS id, p.name AS name ORDER BY p.name")
            if not patients:
                st.info("No patients found.")
            else:
                patient_options = {f"{p['name']} ({p['id']})": p['id'] for p in patients}
                selected = st.selectbox("Select a patient", list(patient_options.keys()))
                patient_id = patient_options[selected]
                query = """
                    MATCH (p:Patient {id: $patient_id})
                    OPTIONAL MATCH (p)-[:ASSIGNED_TO]->(c:Clinician)
                    OPTIONAL MATCH (p)-[:PERFORMED]->(s:Session)
                    OPTIONAL MATCH (s)-[:CONTAINS]->(r:Rep)-[:OF_EXERCISE]->(e:Exercise)
                    OPTIONAL MATCH (r)-[:HAS_FEEDBACK]->(fb:Feedback)-[:RELATES_TO]->(fi:FormIssue)
                    RETURN p, c, s, r, e, fb, fi
                    ORDER BY s.date, r.rep_number
                """
                records = db.query(query, {"patient_id": patient_id})
                if records:
                    patient = records[0]["p"]
                    clinician = records[0]["c"]
                    st.subheader(patient["name"])
                    st.write(f"**Condition:** {patient['condition']}")
                    st.write(f"**Clinician:** {clinician['name'] if clinician else 'None'}")
                    # Group sessions
                    sessions = {}
                    for rec in records:
                        s = rec["s"]
                        if s and s["id"] not in sessions:
                            sessions[s["id"]] = {"session": s, "reps": []}
                        if s and rec["r"]:
                            sessions[s["id"]]["reps"].append({
                                "rep": rec["r"],
                                "exercise": rec["e"],
                                "feedback": rec["fb"],
                                "issue": rec["fi"]
                            })
                    for s_data in sessions.values():
                        s = s_data["session"]
                        with st.expander(f"Session {s['id']} - {s['date']} ({s['duration_minutes']} min)"):
                            if s_data["reps"]:
                                rep_df = pd.DataFrame([{
                                    "Rep #": r["rep"]["rep_number"],
                                    "Exercise": r["exercise"]["name"] if r["exercise"] else "",
                                    "Form Score": r["rep"]["form_score"],
                                    "Feedback": r["feedback"]["comment"] if r["feedback"] else "",
                                    "Issue": r["issue"]["name"] if r["issue"] else ""
                                } for r in s_data["reps"]])
                                st.table(rep_df)
                            else:
                                st.write("No reps recorded for this session.")
                else:
                    st.warning("No data found for this patient.")
        except Exception as e:
            st.error(f"Query failed: {str(e)}")
        finally:
            db.close()

# Clinicians
elif page == "Clinicians":
    st.title("Clinicians")
    db = get_db_safe()
    if db:
        try:
            query = """
                MATCH (c:Clinician)
                OPTIONAL MATCH (c)<-[:ASSIGNED_TO]-(p:Patient)
                RETURN c.id AS id, c.name AS name, c.specialty AS specialty, collect(p.name) AS patients
                ORDER BY c.name
            """
            clinicians = db.query(query)
            if clinicians:
                df = pd.DataFrame(clinicians)
                df["patients"] = df["patients"].apply(lambda x: ", ".join(x))
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No clinicians found.")
        except Exception as e:
            st.error(f"Query failed: {str(e)}")
        finally:
            db.close()

# Exercises
elif page == "Exercises":
    st.title("Exercises")
    db = get_db_safe()
    if db:
        try:
            query = """
                MATCH (e:Exercise)
                OPTIONAL MATCH (e)-[:TARGETS]->(m:MuscleGroup)
                OPTIONAL MATCH (e)-[:REQUIRES]->(eq:Equipment)
                RETURN e.id AS id, e.name AS name, e.description AS description,
                       collect(DISTINCT m.name) AS muscles,
                       collect(DISTINCT eq.name) AS equipment
                ORDER BY e.name
            """
            exercises = db.query(query)
            if exercises:
                df = pd.DataFrame(exercises)
                df["muscles"] = df["muscles"].apply(lambda x: ", ".join(x))
                df["equipment"] = df["equipment"].apply(lambda x: ", ".join(x))
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No exercises found.")
        except Exception as e:
            st.error(f"Query failed: {str(e)}")
        finally:
            db.close()

# Graph Queries
elif page == "Graph Queries":
    st.title("Graph Queries")
    query_type = st.selectbox(
        "Select a query",
        ["Patients with Form Issue", "Patient Similarity"]
    )
    db = get_db_safe()
    if db:
        try:
            if query_type == "Patients with Form Issue":
                issue_name = st.text_input("Form issue name", value="Knee Valgus")
                if st.button("Run Query"):
                    with st.spinner("Running graph query..."):
                        results = db.query(patients_with_issue(issue_name), {"issue_name": issue_name})
                    if results:
                        df = pd.DataFrame(results)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No patients found with that issue.")
            else:  # Patient Similarity
                if st.button("Run Query"):
                    with st.spinner("Running graph query..."):
                        results = db.query(patient_similarity())
                    if results:
                        df = pd.DataFrame(results)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No similarities found.")
        except Exception as e:
            st.error(f"Query failed: {str(e)}")
        finally:
            db.close()

import os
from db import get_db

clinicians = [
    {"id": "c1", "name": "Dr. Sarah Johnson", "specialty": "Orthopedics"},
    {"id": "c2", "name": "Dr. Mark Lee", "specialty": "Sports Medicine"},
]

patients = [
    {"id": "p1", "name": "Alice Smith", "age": 34, "condition": "ACL recovery"},
    {"id": "p2", "name": "Bob Brown", "age": 45, "condition": "Lower back pain"},
    {"id": "p3", "name": "Carol White", "age": 28, "condition": "Shoulder impingement"},
]

exercises = [
    {"id": "e1", "name": "Biceps Curl", "description": "Elbow flexion with dumbbell"},
    {"id": "e2", "name": "Squat", "description": "Knee and hip flexion"},
    {"id": "e3", "name": "Shoulder Press", "description": "Overhead press"},
]

form_issues = [
    {"id": "f1", "name": "Knee Valgus"},
    {"id": "f2", "name": "Shoulder Shrug"},
    {"id": "f3", "name": "Back Arch"},
]

muscle_groups = [
    {"id": "m1", "name": "Biceps"},
    {"id": "m2", "name": "Quadriceps"},
    {"id": "m3", "name": "Deltoids"},
]

equipment = [
    {"id": "eq1", "name": "Dumbbell"},
    {"id": "eq2", "name": "Barbell"},
    {"id": "eq3", "name": "Bodyweight"},
]

sessions = [
    {"id": "s1", "patient_id": "p1", "date": "2024-05-01", "duration": 30},
    {"id": "s2", "patient_id": "p1", "date": "2024-05-03", "duration": 25},
    {"id": "s3", "patient_id": "p2", "date": "2024-05-02", "duration": 40},
    {"id": "s4", "patient_id": "p3", "date": "2024-05-04", "duration": 35},
]

reps = [
    {"id": "r1", "session_id": "s1", "exercise_id": "e1", "rep_number": 1, "form_score": 85},
    {"id": "r2", "session_id": "s1", "exercise_id": "e1", "rep_number": 2, "form_score": 78},
    {"id": "r3", "session_id": "s1", "exercise_id": "e2", "rep_number": 1, "form_score": 70},
    {"id": "r4", "session_id": "s2", "exercise_id": "e1", "rep_number": 1, "form_score": 90},
    {"id": "r5", "session_id": "s3", "exercise_id": "e2", "rep_number": 1, "form_score": 65},
    {"id": "r6", "session_id": "s4", "exercise_id": "e3", "rep_number": 1, "form_score": 80},
]

feedback = [
    {"id": "fb1", "rep_id": "r3", "issue_id": "f1", "comment": "Knee caving inward", "severity": "High"},
    {"id": "fb2", "rep_id": "r5", "issue_id": "f1", "comment": "Knee valgus observed", "severity": "Medium"},
    {"id": "fb3", "rep_id": "r6", "issue_id": "f2", "comment": "Shoulders raised", "severity": "Low"},
]

def seed_database():
    db = get_db()
    driver = db.driver

    with driver.session() as session:
        # Clear existing data (optional)
        session.run("MATCH (n) DETACH DELETE n")

        # Insert clinicians
        session.run("""
            UNWIND $clinicians AS row
            CREATE (c:Clinician {id: row.id, name: row.name, specialty: row.specialty})
        """, clinicians=clinicians)

        # Insert patients
        session.run("""
            UNWIND $patients AS row
            CREATE (p:Patient {id: row.id, name: row.name, age: row.age, condition: row.condition})
        """, patients=patients)

        # Insert exercises
        session.run("""
            UNWIND $exercises AS row
            CREATE (e:Exercise {id: row.id, name: row.name, description: row.description})
        """, exercises=exercises)

        # Insert form issues
        session.run("""
            UNWIND $issues AS row
            CREATE (f:FormIssue {id: row.id, name: row.name})
        """, issues=form_issues)

        # Insert muscle groups
        session.run("""
            UNWIND $muscles AS row
            CREATE (m:MuscleGroup {id: row.id, name: row.name})
        """, muscles=muscle_groups)

        # Insert equipment
        session.run("""
            UNWIND $equipment AS row
            CREATE (eq:Equipment {id: row.id, name: row.name})
        """, equipment=equipment)

        # Insert sessions
        session.run("""
            UNWIND $sessions AS row
            CREATE (s:Session {id: row.id, date: row.date, duration_minutes: row.duration})
        """, sessions=sessions)

        # Insert reps
        session.run("""
            UNWIND $reps AS row
            CREATE (r:Rep {id: row.id, rep_number: row.rep_number, form_score: row.form_score})
        """, reps=reps)

        # Insert feedback
        session.run("""
            UNWIND $feedback AS row
            CREATE (fb:Feedback {id: row.id, comment: row.comment, severity: row.severity})
        """, feedback=feedback)

        # Create relationships
        # ASSIGNED_TO
        session.run("""
            MATCH (p:Patient {id: 'p1'}), (c:Clinician {id: 'c1'})
            CREATE (p)-[:ASSIGNED_TO]->(c)
        """)
        session.run("""
            MATCH (p:Patient {id: 'p2'}), (c:Clinician {id: 'c1'})
            CREATE (p)-[:ASSIGNED_TO]->(c)
        """)
        session.run("""
            MATCH (p:Patient {id: 'p3'}), (c:Clinician {id: 'c2'})
            CREATE (p)-[:ASSIGNED_TO]->(c)
        """)

        # PERFORMED
        for s in sessions:
            session.run("""
                MATCH (p:Patient {id: $patient_id}), (s:Session {id: $session_id})
                CREATE (p)-[:PERFORMED]->(s)
            """, patient_id=s["patient_id"], session_id=s["id"])

        # CONTAINS
        for r in reps:
            session.run("""
                MATCH (s:Session {id: $session_id}), (r:Rep {id: $rep_id})
                CREATE (s)-[:CONTAINS]->(r)
            """, session_id=r["session_id"], rep_id=r["id"])

        # OF_EXERCISE
        for r in reps:
            session.run("""
                MATCH (r:Rep {id: $rep_id}), (e:Exercise {id: $exercise_id})
                CREATE (r)-[:OF_EXERCISE]->(e)
            """, rep_id=r["id"], exercise_id=r["exercise_id"])

        # HAS_FEEDBACK
        for fb in feedback:
            session.run("""
                MATCH (r:Rep {id: $rep_id}), (fb:Feedback {id: $fb_id})
                CREATE (r)-[:HAS_FEEDBACK]->(fb)
            """, rep_id=fb["rep_id"], fb_id=fb["id"])

        # RELATES_TO
        for fb in feedback:
            session.run("""
                MATCH (fb:Feedback {id: $fb_id}), (f:FormIssue {id: $issue_id})
                CREATE (fb)-[:RELATES_TO]->(f)
            """, fb_id=fb["id"], issue_id=fb["issue_id"])

        # TARGETS
        session.run("""
            MATCH (e:Exercise {id: 'e1'}), (m:MuscleGroup {id: 'm1'})
            CREATE (e)-[:TARGETS]->(m)
        """)
        session.run("""
            MATCH (e:Exercise {id: 'e2'}), (m:MuscleGroup {id: 'm2'})
            CREATE (e)-[:TARGETS]->(m)
        """)
        session.run("""
            MATCH (e:Exercise {id: 'e3'}), (m:MuscleGroup {id: 'm3'})
            CREATE (e)-[:TARGETS]->(m)
        """)

        # REQUIRES
        session.run("""
            MATCH (e:Exercise {id: 'e1'}), (eq:Equipment {id: 'eq1'})
            CREATE (e)-[:REQUIRES]->(eq)
        """)
        session.run("""
            MATCH (e:Exercise {id: 'e2'}), (eq:Equipment {id: 'eq3'})
            CREATE (e)-[:REQUIRES]->(eq)
        """)
        session.run("""
            MATCH (e:Exercise {id: 'e3'}), (eq:Equipment {id: 'eq1'})
            CREATE (e)-[:REQUIRES]->(eq)
        """)

        # SIMILAR_TO (example)
        session.run("""
            MATCH (e1:Exercise {id: 'e1'}), (e2:Exercise {id: 'e3'})
            CREATE (e1)-[:SIMILAR_TO]->(e2)
        """)

    db.close()
    print("Database seeded successfully.")

if __name__ == "__main__":
    seed_database()

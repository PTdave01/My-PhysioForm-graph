def patients_with_issue(issue_name):
    return """
        MATCH (p:Patient)-[:PERFORMED]->(s:Session)-[:CONTAINS]->(r:Rep)-[:HAS_FEEDBACK]->(fb:Feedback)-[:RELATES_TO]->(fi:FormIssue {name: $issue_name})
        OPTIONAL MATCH (r)-[:OF_EXERCISE]->(e:Exercise)
        OPTIONAL MATCH (p)-[:ASSIGNED_TO]->(c:Clinician)
        RETURN p.name AS patient, e.name AS exercise, c.name AS clinician, fb.severity AS severity
    """

def patient_similarity():
    return """
        MATCH (p1:Patient)-[:PERFORMED]->(:Session)-[:CONTAINS]->(:Rep)-[:OF_EXERCISE]->(e:Exercise),
              (p1)-[:PERFORMED]->(:Session)-[:CONTAINS]->(:Rep)-[:HAS_FEEDBACK]->(:Feedback)-[:RELATES_TO]->(fi:FormIssue),
              (p2:Patient)-[:PERFORMED]->(:Session)-[:CONTAINS]->(:Rep)-[:OF_EXERCISE]->(e),
              (p2)-[:PERFORMED]->(:Session)-[:CONTAINS]->(:Rep)-[:HAS_FEEDBACK]->(:Feedback)-[:RELATES_TO]->(fi)
        WHERE p1 <> p2
        RETURN p1.name AS patient1, p2.name AS patient2, e.name AS exercise, fi.name AS issue, count(*) AS common_issues
        ORDER BY common_issues DESC
    """

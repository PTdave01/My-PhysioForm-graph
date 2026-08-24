import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

URI = os.getenv("COGNO_URI")
USER = os.getenv("COGNO_USER")
PASSWORD = os.getenv("COGNO_PASSWORD")

class Neo4jConnection:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def query(self, cypher, parameters=None):
        with self.driver.session() as session:
            result = session.run(cypher, parameters or {})
            return [record.data() for record in result]

    def execute_write(self, cypher, parameters=None):
        with self.driver.session() as session:
            session.execute_write(lambda tx: tx.run(cypher, parameters or {}))

def get_db():
    return Neo4jConnection(URI, USER, PASSWORD)

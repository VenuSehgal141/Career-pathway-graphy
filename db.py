"""
db.py
-----
Thin wrapper around the official Neo4j Python driver, pointed at CognoDB.

Why this file exists as its own module:
- Keeps connection/config concerns out of the UI and query code.
- Gives us a single place to handle "database unreachable" gracefully,
  instead of scattering try/except blocks across the app.
- Makes the driver a singleton so Streamlit doesn't reopen a new
  connection pool on every rerun (Streamlit reruns the whole script
  on every UI interaction).
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError, Neo4jError

load_dotenv()

URI = os.getenv("COGNODB_URI")
USER = os.getenv("COGNODB_USER")
PASSWORD = os.getenv("COGNODB_PASSWORD")

# On Render, environment variables are injected at runtime, but the app should
# still be safe to import locally without a .env file present.
if not URI:
    URI = ""
if not USER:
    USER = ""
if not PASSWORD:
    PASSWORD = ""


class DatabaseUnavailableError(Exception):
    """Raised when CognoDB can't be reached or credentials are wrong.
    The UI layer catches this and shows a friendly message instead of
    a stack trace."""
    pass


_driver = None


def get_driver():
    """Return a cached driver instance, creating it on first call.

    Using a module-level singleton avoids re-establishing a fresh
    connection pool on every Streamlit rerun, which would otherwise
    happen because Streamlit re-executes the script top-to-bottom on
    every user interaction.
    """
    global _driver
    if _driver is None:
        if not URI or not USER or not PASSWORD:
            raise DatabaseUnavailableError(
                "Missing CognoDB credentials. Check your .env file against .env.example."
            )
        try:
            _driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
            _driver.verify_connectivity()
        except (ServiceUnavailable, AuthError, Neo4jError, ValueError) as e:
            _driver = None
            raise DatabaseUnavailableError(
                f"Could not connect to CognoDB: {e}"
            ) from e
    return _driver


def run_query(cypher: str, parameters: dict | None = None):
    """Run a single parameterised Cypher query and return a list of
    plain dicts (one per record). Every query in this project goes
    through this function so parameterisation is enforced in one
    place -- no query in the codebase ever string-concatenates
    user input into Cypher.
    """
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run(cypher, parameters or {})
            return [record.data() for record in result]
    except ServiceUnavailable as e:
        raise DatabaseUnavailableError(f"CognoDB became unreachable mid-query: {e}") from e


def close_driver():
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None

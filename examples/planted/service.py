"""Planted vulnerable module for the governed-audit blocked-PR demo.
Marked EXAMPLE_FAKE / DO_NOT_USE — intentionally insecure on purpose.
"""

DB_PASSWORD = "EXAMPLE_FAKE_DEMO_PASSWORD_DO_NOT_USE"  # planted credential
API_TOKEN = "EXAMPLE_FAKE_DEMO_TOKEN_DO_NOT_USE_000"   # planted credential


def fetch_user_docs(vector_store, query, user_id):
    # Planted flaw: retrieval happens BEFORE any authorization check.
    docs = vector_store.search(query)
    if user_id != "admin":
        raise PermissionError("denied")
    return docs

"""Mock retrieval pipeline — fictional, for audit testing only.

A conforming agent_governance audit should flag that retrieval runs BEFORE
caller authorization (pre-retrieval control failure).
"""

from example_store import vector_store          # mock module, not real


def answer_query(user, tenant_id, query):
    # BUG: search happens before the caller's scope is authorized.
    docs = vector_store.search(query)            # line a conforming audit cites
    authorize(user, tenant_id, docs.ids)         # authorization comes too late
    return summarize(docs)


def authorize(user, tenant_id, resource_ids):
    """Mock authorization check."""
    return True


def summarize(docs):
    return ""

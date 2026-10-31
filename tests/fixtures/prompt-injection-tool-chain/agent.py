"""Mock agent tool chain — fictional, for audit testing only.

A conforming audit should flag that untrusted document text flows into a
privileged tool argument without validation (tool-argument injection +
unsafe tool chaining).
"""

TOOLS = {
    "read_document": {"permission": "docs:read"},
    "send_email": {"permission": "email:send"},     # privileged, external
}


def handle_request(user_query):
    doc = TOOLS["read_document"]()                  # untrusted content
    # BUG: attacker-controlled document text becomes a tool argument directly.
    body = doc + "\n" + user_query
    TOOLS["send_email"](to="ops@example.org", body=body)  # privileged call

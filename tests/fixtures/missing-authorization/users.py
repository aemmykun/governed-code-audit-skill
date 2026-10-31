"""Mock service code — fictional, for audit testing only."""


def disable_user(request, user_id):
    """Privileged action WITHOUT an authorization check.

    A conforming audit should flag: this handler performs an administrative
    action without verifying the caller's role, and emits no audit event.
    """
    db = request.app.db
    db.execute("UPDATE users SET disabled = TRUE WHERE id = ?", [user_id])
    return {"ok": True}

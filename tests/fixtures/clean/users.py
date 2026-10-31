"""Mock well-formed service code — fictional, for audit testing only.

A conforming audit should produce no critical/high findings on this file.
"""

import logging

logger = logging.getLogger(__name__)

ADMIN_ROLE = "admin"


def disable_user(request, user_id):
    """Privileged action WITH authorization check and audit event."""
    if request.user.role != ADMIN_ROLE:
        return {"error": "forbidden"}, 403
    db = request.app.db
    db.execute("UPDATE users SET disabled = TRUE WHERE id = ?", [user_id])
    logger.info("user.disabled", extra={"actor": request.user.id, "target": user_id})
    return {"ok": True}

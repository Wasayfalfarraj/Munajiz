import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.db import get_connection  # noqa: E402


def get_codes():
    conn = get_connection()
    cur = conn.cursor()
    rows = cur.execute(
        """SELECT fc.code, fc.name_ar, fc.meaning_ar, fc.root_cause_ar, fc.resolution_type,
                  fc.automatic_resolution_allowed, fc.employee_intervention_required,
                  fc.recommended_action_ar,
                  (SELECT COUNT(*) FROM cases c WHERE c.code = fc.code) AS total_count,
                  (SELECT COUNT(*) FROM cases c WHERE c.code = fc.code AND c.status = 'open') AS open_count
           FROM failure_codes fc ORDER BY fc.code"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

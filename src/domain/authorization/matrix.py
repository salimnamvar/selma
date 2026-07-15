"""Normative capability matrix projection (SPECIFICATION.md §3.2).

Do not invent rows. Operation→capability bindings that are not rows:
  - directive.split → directive.fork (Q-01 / SPEC-01)
  - finding.reopen → finding.reject_remediation (S-14c / Q-02)
"""

from __future__ import annotations

from domain.authorization.enums import Role

# Full Official matrix from §3.2
_OFFICIAL: frozenset[str] = frozenset(
    {
        "directive.create",
        "directive.modify",
        "directive.retire",
        "directive.fork",
        "directive.merge",
        "directive.restore",
        "finding.view",
        "finding.dismiss",
        "finding.waive",
        "finding.approve_remediation",
        "finding.reject_remediation",
        "finding.supersede",
        "analytics.view",
        "conflict.resolve",
    }
)

_COMPLIANCE: frozenset[str] = frozenset(
    {
        "inspection.submit",
        "inspection.reinspect",
        "finding.view",
        "finding.acknowledge",
        "evidence.submit",
        "analytics.view",
    }
)

_SYSTEM: frozenset[str] = frozenset(
    {
        "inspection.submit",
        "finding.view",
        "analytics.view",
    }
)

ROLE_CAPABILITIES: dict[Role, frozenset[str]] = {
    Role.REGULATORY_OFFICIAL: _OFFICIAL,
    Role.COMPLIANCE_REPRESENTATIVE: _COMPLIANCE,
    Role.SYSTEM: _SYSTEM,
}

# Command → gating capability (including non-1:1 bindings)
COMMAND_CAPABILITY: dict[str, str] = {
    "directive.create": "directive.create",
    "directive.modify": "directive.modify",
    "directive.retire": "directive.retire",
    "directive.fork": "directive.fork",
    "directive.merge": "directive.merge",
    "directive.restore": "directive.restore",
    "directive.split": "directive.fork",  # Q-01
    "inspection.submit": "inspection.submit",
    "inspection.reinspect": "inspection.reinspect",
    "finding.acknowledge": "finding.acknowledge",
    "finding.dismiss": "finding.dismiss",
    "finding.waive": "finding.waive",
    "finding.approve_remediation": "finding.approve_remediation",
    "finding.reject_remediation": "finding.reject_remediation",
    "finding.reopen": "finding.reject_remediation",  # S-14c / Q-02
    "evidence.submit": "evidence.submit",
    "finding.supersede": "finding.supersede",
    "finding.view": "finding.view",
    "analytics.view": "analytics.view",
    "conflict.resolve": "conflict.resolve",
}

SOD_ACTIONS = frozenset({"finding.waive", "finding.approve_remediation"})

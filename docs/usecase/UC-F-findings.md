# UC-F — Finding Lifecycle

| ID | Use case | Actor | Capability | Transition | Stories |
| :--- | :--- | :--- | :--- | :--- | :--- |
| UC-F-01 | View findings | either | `finding.view` | — | US-FC-001 |
| UC-F-02 | Acknowledge | Compliance | `finding.acknowledge` | Open → Acknowledged | US-FL-010 |
| UC-F-03 | Submit evidence | Compliance | `evidence.submit` | Acknowledged → Evidence Submitted | US-FL-010 |
| UC-F-04 | Approve remediation | Official | `finding.approve_remediation` | Pending → Verified | US-SD-002 |
| UC-F-05 | Reject remediation | Official | `finding.reject_remediation` | Pending → Rejected | US-FL-010 |
| UC-F-06 | Reopen | Official | `finding.reject_remediation` | Rejected → Open | US-FL-010 |
| UC-F-07 | Dismiss | Official | `finding.dismiss` | Open → Dismissed | US-FL-001 |
| UC-F-08 | Waive | Official | `finding.waive` | Open → Waived | US-SD-001 |

**System-only:** Created→Open; Evidence→Pending Verification; Verified→Closed; Waived→Closed.

**Refs:** `contracts/finding_lifecycle/*`, `selma_finding_lifecycle.puml`.

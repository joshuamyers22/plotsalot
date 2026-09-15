# Security Policy

## Supported versions

Security fixes are provided for the latest published minor release line. Older
minor lines are not supported. Because plotsalot is pre-1.0, a minor release may
contain compatibility changes; upgrade guidance will be included when a fix
requires one.

## Reporting a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/joshuamyers22/plotsalot/security/advisories/new)
to report a suspected vulnerability to the repository owner. Do not open a
public issue before a fix and disclosure plan are agreed. Include the affected
version, impact, reproduction steps, and any suggested mitigation, but do not
include real credentials or production data.

The repository owner is responsible for coordinating the response. Reports are
targeted for acknowledgement within three business days and an initial impact
assessment within seven business days. These are response targets rather than a
guaranteed service-level agreement. Remediation and coordinated-disclosure
timing depend on severity, exploitability, and release complexity.

## Statistical and model risk

Treat statistical model risk as a correctness and governance concern: preserve
the approved sample and specification, restrict sensitive outputs, test leakage
and unstable assumptions, and require review before a result affects capital,
risk limits, client reporting, or automated decisions.

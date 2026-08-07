# Enterprise Forecast Decision Intelligence Platform
## Version 1 — Engineering Master Plan (Enterprise-Hardened Revision)

*Revision note.* This supersedes the first blueprint. On re-review, the original was a sound, lean V1 plan but read closer to a **production-capable MVP than an enterprise-grade product**. This revision keeps the lean modular-monolith discipline (still no microservices, no Kubernetes, small-team-friendly) and adds the dimensions that genuinely make a product *enterprise-grade and production-oriented*: **multi-tenancy and isolation, run reproducibility/lineage, compliance and data governance, availability and disaster recovery with SLOs, deep observability and incident response, accessibility, load/security testing, and flexible deployment models.** Each is separated into **day-one V1** versus **architected-for-but-phased** so we do not over-build.

---

## 0. What "Enterprise-Grade" Actually Means Here

A frequent mistake is to equate "enterprise" with "microservices, Kubernetes, and maximal architecture." That is wrong and would sink a V1. For this product, enterprise-grade means eight concrete properties, all achievable inside a modular monolith:

1. **Tenant isolation** — customers' data is provably separated.
2. **Reproducibility & auditability** — every decision can be reproduced and explained from stored provenance. *(This is also the product's core value proposition, so it is non-negotiable.)*
3. **Compliance posture** — SOC 2 readiness, data retention/deletion, residency options.
4. **Availability & recoverability** — defined SLOs, multi-AZ, tested backups and recovery.
5. **Observability & operability** — logs, metrics, traces, SLO alerting, incident response.
6. **Security by default** — least privilege, encryption with managed keys, dependency and image scanning.
7. **Accessibility** — WCAG-conformant UI (a real procurement gate).
8. **Predictable delivery** — versioned APIs/contracts, progressive rollout, rollback.

The rest of this document delivers these without abandoning simplicity. Where a property is a *journey* (e.g. SOC 2 Type II certification), V1 delivers the **architecture and controls** that make it attainable, and the roadmap phases the certification work.

---

## 1. Executive Summary

The prototype proved the analytical pipeline. V1 productizes it as a **multi-tenant, auditable, production-operated application**: a dataset is uploaded, the proven pipeline runs as a **governed, reproducible job**, a versioned **decision object** is persisted with full provenance, and it is rendered as an interactive dashboard and downloadable reports.

The architecture remains a **modular monolith** — one codebase, one Postgres, one Redis, one object store, three artifacts (API, worker, static SPA) — because the subsystems change together and a small team builds them. Every boundary is drawn to split cleanly later without a rewrite. **The decision object is the central contract**; the dashboard and report renderer consume it and never recompute.

What makes this revision *enterprise-grade*: strong **tenant isolation** (row-level scoping enforced in the app *and* Postgres RLS as defense in depth); **run reproducibility** (input hash + code version + config version stored with every run, so any decision is reproducible and defensible — the auditability the product sells); a **compliance and governance** posture (SOC 2 controls, retention/deletion, residency, KMS-managed encryption); **availability/DR** with explicit SLOs and tested recovery; **full observability** (logs/metrics/traces + SLO alerting + incident response); **accessibility** to WCAG 2.1 AA; and **flexible deployment** (managed SaaS by default, single-tenant VPC option for security-sensitive customers).

---

## 2. Product Architecture

### 2.1 Subsystems (unchanged core, enterprise concerns made explicit)

The functional subsystems are as before — Ingestion, Semantic/Schema Mapping, Validation, Analytics Engine, Evidence Generation, Decision Engine, Business-Context Assembly, Report Generation, Dashboard, API, Job/Queue, Storage, Configuration — now joined by first-class **cross-cutting** subsystems that the original treated as afterthoughts: **Tenancy & Access**, **Provenance & Audit**, **Observability**, and **Governance/Retention**.

### 2.2 Shape

Three deployable artifacts (**API**, **worker**, **static SPA**) over **PostgreSQL + Redis + S3-compatible storage**, deployed **multi-AZ**. This is the entire production footprint. The worker is separate only because analytics jobs are long-running; everything else stays in one well-factored codebase.

**Why still a monolith:** enterprise-grade is about *isolation, auditability, availability, and operability* — none of which require service decomposition at V1. Microservices would add distributed-systems failure modes and data-consistency burden with no product benefit yet. The module boundaries (especially the analytics library, the decision object, and the tenancy layer) are the seams that make later extraction cheap.

---

## 3. Multi-Tenancy & Data Isolation *(new — foundational)*

The tenancy model is the first enterprise decision and must be made deliberately.

- **Model chosen for V1: shared database, shared schema, row-level tenancy** — every tenant-owned row carries a `tenant_id`, and *every* query is scoped by it.
- **Defense in depth: PostgreSQL Row-Level Security (RLS)** — even if an application query forgets to scope, the database refuses cross-tenant rows. Application-level scoping is the primary control; RLS is the backstop. Isolation is covered by **automated tests that attempt cross-tenant access and must fail**.
- **Object storage isolation** — tenant-prefixed keys and per-tenant access policies; no shared, guessable paths.
- **Why this model over alternatives:** *schema-per-tenant* and *database-per-tenant* give stronger isolation but multiply migration and operational cost and cap tenant count — premature for V1. Shared-schema + RLS is the standard pragmatic enterprise SaaS starting point and upgrades cleanly.
- **Phased/architected-for:** for security-sensitive customers who require hard isolation, the same image deploys as a **single-tenant instance** (see §15). Because tenancy is a clean layer, this is a deployment choice, not a rewrite.

---

## 4. Reproducibility, Lineage & Auditability *(new — core product requirement)*

The product's promise is *defensible, auditable decisions*. That is impossible unless every run is reproducible. V1 therefore treats provenance as a first-class output, not a log line.

For **every run**, the system persists:
- a **content hash of the input dataset** (and a pointer to the immutable stored file),
- the **analytics library version** and **decision-policy version** used,
- the **resolved configuration snapshot** (metrics, thresholds, mappings) as applied,
- the **environment/runtime version**,
- timestamps, actor, and tenant.

Consequences, all enterprise-critical:
- **Reproducibility:** re-running the same input + versions yields the same decision object — verifiable in CI via golden tests and in production via a "re-run" action.
- **Explainability:** every evidence item already links to its computation; provenance links the whole run to exact code/config/data.
- **Audit trail:** an append-only, tamper-evident **decision log** records who saw what, who accepted/overrode which recommendation, and on what evidence — satisfying governance and, later, regulatory review.
- **Change safety:** because analytics/policy/config are versioned, a decision made last quarter can be reproduced even after the methodology evolves.

This section is the difference between "a dashboard" and "a system of record for decisions."

---

## 5. Technology Stack

Unchanged core recommendations from the prior blueprint, with enterprise additions noted:

- **Backend:** Python 3.12 + FastAPI + Pydantic v2 (one language across API and analytics; typed contracts; auto OpenAPI). *Alternative:* Django if you want built-in admin/SSO sooner.
- **Analytics:** pandas/numpy/scipy/statsmodels as a versioned internal library with a module registry. *Future:* Polars/DuckDB behind the same interface for larger-than-memory data.
- **Async jobs:** Redis + RQ (start simple) → Celery if scheduling/retries/routing grow. **Jobs must be idempotent** (keyed by run id) so retries are safe.
- **Relational DB:** PostgreSQL 16 (JSONB decision objects; **RLS** for tenancy), SQLAlchemy 2.x + Alembic.
- **Object storage:** S3-compatible (MinIO locally), **versioning + SSE-KMS enabled**.
- **Cache/broker:** Redis (queue, cache, rate-limit counters).
- **Frontend:** React 18 + TypeScript + Vite; TanStack Query + Zustand; **Chart.js preserved**; a11y-tested components.
- **Reports:** Jinja2 + Playwright (PDF); openpyxl/python-docx for Excel/Word.
- **AuthN:** managed **OIDC** (Auth0/Cognito) with a path to **enterprise SSO (SAML/OIDC) and SCIM provisioning**; app **RBAC**. *Alternative:* self-hosted Keycloak for data-residency mandates.
- **Secrets & keys:** cloud **Secrets Manager** + **KMS**-managed encryption keys with rotation; **BYOK** as a phased option for regulated customers.
- **CI/CD & runtime:** GitHub Actions + Docker; **AWS ECS Fargate** multi-AZ (managed **RDS**, **ElastiCache**, **S3**, **CloudFront**, **ALB**). *Leanest V1 alternative:* a PaaS (Render/Fly). **No Kubernetes in V1.**
- **Observability:** OpenTelemetry (traces/metrics) + Sentry (errors) + structured JSON logs + a metrics/alerting backend (managed, e.g. Grafana Cloud/Datadog, or Prometheus/Grafana self-hosted).

---

## 6. Frontend Architecture

As previously specified — feature-oriented React SPA, client-rendered, data-driven from the decision object, Chart.js/SVG components preserved, TanStack Query for server state — plus two enterprise additions the original omitted:

- **Accessibility (day-one):** target **WCAG 2.1 AA** — semantic markup, keyboard operability, focus management, sufficient contrast, and **no color-only encoding** (add labels/patterns to the divergent charts and legends we already flagged). Automated a11y checks (axe) run in CI; a **VPAT** is producible for procurement. This is frequently a hard gate in enterprise buying.
- **Performance budgets (day-one):** defined budgets (bundle size, time-to-interactive, chart render time for the largest supported dataset); enforced in CI; code-splitting per workspace; virtualized tables/heatmaps for large scopes.

Rendering strategy remains SPA (authenticated internal tool; SSR unnecessary). Deep-linkable scope/filter state in the URL enables shareable views.

---

## 7. Backend Architecture

As previously specified — pipeline stages as typed, testable functions; the `analytics` and `decision` libraries; REST API with OpenAPI; decision object persisted as JSONB — hardened with:

- **Provenance capture** at each run (§4).
- **Idempotent, resumable jobs** keyed by run id, with per-stage status, timeouts, and safe retries.
- **Backpressure & quotas:** per-tenant concurrency limits and queue depth limits so one tenant's large run cannot starve others.
- **API versioning:** the REST API is versioned (`/v1`) with an explicit deprecation policy; the decision-object schema is independently versioned in `contracts`. Both use additive/expand-contract changes so clients never break.
- **Graceful degradation:** if a non-critical stage (e.g. a specific analytics module) fails, the run completes with that section marked unavailable rather than failing wholesale.

---

## 8. Data Flow

Upload → (store raw file + tenant-scoped dataset record) → mapping/validation confirmed → **run created with provenance** (input hash, code/config versions) → enqueued → worker executes pipeline (idempotent, per-stage status) → **decision object persisted (JSONB, versioned) + artifacts to object storage + audit entry** → frontend fetches the tenant-scoped decision object and renders → report renderer produces HTML/PDF from the same object → user decisions appended to the immutable decision log.

The decision object remains the contract; provenance and tenancy travel with it end-to-end.

---

## 9. Repository Structure

Monorepo, as before:

```
repo/
  apps/{api, worker, web}
  packages/{analytics, decision, contracts}
  config/            # metrics, thresholds, policies, themes (declarative, versioned)
  infra/             # Docker, compose, IaC, CI, RLS policies, migrations
  tests/             # golden datasets, isolation tests, load, e2e
  docs/              # architecture, runbooks, incident response, onboarding, compliance
```

Additions vs. the original: explicit homes for **RLS policies/migrations**, **isolation and load tests**, and **compliance/runbook docs** — signaling these are first-class, not afterthoughts.

---

## 10. Development Environment

Unchanged and strong: Python 3.12 + uv, Node 20 + pnpm, Docker Compose (Postgres, Redis, MinIO), pre-commit hooks, VS Code + devcontainer, Playwright browsers. Onboarding target: running full stack with seeded multi-tenant sample data in under an hour. Add **seeded tenants** to the local fixtures so isolation is exercised in development, not just production.

---

## 11. Dependency Management

Unchanged: uv (Python) and pnpm (JS) with committed lockfiles; pinned direct deps; internal semantic versioning of `analytics`/`decision`/`contracts`; Renovate/Dependabot with CI-gated updates and fast-tracked security advisories. Enterprise addition: **SBOM generation** (software bill of materials) per build, and license scanning, both increasingly required in enterprise procurement and supply-chain reviews.

---

## 12. Configuration Strategy

As before — 12-factor env config; metrics/thresholds and decision policies as **declarative, versioned** definitions; secrets in a manager, never in the repo; **startup config validation** (fail fast). Enterprise additions:

- **Config is versioned and snapshotted per run** (feeds §4 reproducibility).
- **Feature flags** support **progressive delivery** (enable per-tenant/per-environment; dark launch) rather than a global on/off — the basis for safe canary rollouts.
- **Per-tenant configuration** (branding, thresholds, policies) is first-class, isolated, and auditable.

---

## 13. Testing Strategy

The original's analytics-first testing (golden/snapshot + property-based) is correct and retained as the top priority. Enterprise/production additions the original lacked:

- **Tenant-isolation tests (day-one):** automated attempts at cross-tenant reads/writes that **must fail** — the single most important safety test for a multi-tenant product.
- **Load & performance testing:** against defined budgets and the largest supported dataset; validates worker scaling and per-tenant limits; run before each release.
- **Security testing:** dependency + image scanning (Trivy), SAST, and periodic DAST/pen-test; secrets scanning in CI.
- **Accessibility testing:** automated axe checks in CI + manual keyboard/screen-reader passes on key flows.
- **Resilience testing:** fault injection on the queue/DB (retry, timeout, restart) to prove idempotency and graceful degradation.
- Retained: unit, integration (API+DB+queue), component, visual-regression, and E2E (upload→run→dashboard→report) on a compose stack.

---

## 14. Deployment Strategy

Three environments (local/staging/production), one image promoted (no rebuild), CI/CD via GitHub Actions with a **manual production approval**. Enterprise additions:

- **Multi-AZ production** (API, worker, RDS, Redis all AZ-redundant) — availability is not optional at enterprise grade.
- **Progressive delivery:** canary/gradual rollout via feature flags and (where supported) weighted traffic; automated rollback on health/error-budget breach.
- **Deployment models (important for enterprise sales):**
  - **Managed multi-tenant SaaS** — the default, lowest-cost path.
  - **Single-tenant VPC/dedicated deployment** — the same containers deployed in an isolated tenant environment for security/compliance-sensitive customers. Enabled by the clean tenancy layer; offered as a phased option, not day-one.
- **Migrations:** Alembic, expand/contract, gated pre-deploy; **backward-compatible** so rollback is always safe.

---

## 15. Availability, Resilience & Disaster Recovery *(new)*

Enterprise production requires stated targets, not just "backups exist."

- **SLOs (initial, tunable):** e.g. **99.9%** API availability; dashboard read latency P95 within a defined budget; job success rate and time-to-complete targets by dataset size. Error budgets govern release pace.
- **Redundancy:** multi-AZ for compute and data stores; the stateless API/worker scale horizontally; the worker scales first under analytics load.
- **Backups & DR:** automated RDS snapshots **+ point-in-time recovery**; object-storage versioning; **defined RTO/RPO** (e.g. RPO ≤ 15 min via PITR, RTO ≤ a few hours) with a **restore rehearsed on a schedule** — an untested backup is not a backup.
- **Resilience patterns:** timeouts, bounded retries with backoff, idempotent jobs, circuit-breaking on external dependencies, and graceful degradation of non-critical analytics.
- **Capacity:** per-tenant quotas and queue limits prevent noisy-neighbor starvation.

---

## 16. Observability & Production Operations *(new / corrects "keep it light")*

Enterprise operations need all three pillars plus a human process:

- **Logs:** structured JSON, correlation/trace IDs, **no PII/secrets**, tenant-tagged.
- **Metrics:** system (latency, error rate, saturation) and **product/pipeline** metrics (runs, durations, failures by stage, dataset sizes).
- **Traces:** OpenTelemetry across API → queue → worker → DB, so a slow or failed run is diagnosable end to end.
- **Error tracking:** Sentry with release/tenant context.
- **SLO-based alerting:** alert on burn rate against SLOs (not on every blip), routed to on-call.
- **Incident response:** a defined on-call rotation, severity levels, runbooks per common failure, and blameless postmortems with error-budget accounting.
- **Health/readiness:** `/health` and `/ready` endpoints driving load-balancer and deploy gates.
- **Audit:** the append-only decision/audit log (§4) is queryable for governance.

Right-sizing note: for a small team, use **managed** observability (e.g. Grafana Cloud/Datadog + Sentry) rather than self-hosting a stack — enterprise-grade *signal*, minimal operational burden.

---

## 17. Security

The original's fundamentals stand (managed OIDC, RBAC, TLS, input validation, rate limiting, dependency scanning, structured logs). Hardened and completed:

- **Encryption:** in transit (TLS) and at rest via **KMS-managed keys** with rotation; **BYOK** as a phased option.
- **Tenant scoping** enforced in-app **and** via Postgres **RLS**, with isolation tests (§13).
- **Least privilege** across services and cloud IAM; scoped, short-lived credentials.
- **Per-tenant rate limits and quotas** (not just global).
- **Supply chain:** SBOM, image and dependency scanning, pinned/locked builds, signed images (phased).
- **API security:** versioned endpoints, strict CORS, security headers, upload validation/scanning, abuse protection.
- **Enterprise identity:** SAML/OIDC SSO and **SCIM** user provisioning on the roadmap; RBAC designed to accommodate them.

---

## 18. Compliance & Data Governance *(new — enterprise procurement gate)*

Enterprises will not buy without a credible governance posture. V1 builds the controls; certification is phased.

- **SOC 2 readiness (day-one controls, Type II over time):** access control, change management, encryption, logging/audit, backup/DR, vendor management — implemented as engineering practice from the start so certification is a documentation/audit exercise, not a re-architecture.
- **Data lifecycle:** explicit **retention and deletion** policies per tenant; **right-to-erasure** support (GDPR/CCPA) — enabled by tenant-scoped storage and the ability to purge a tenant's datasets/artifacts/decision objects on request.
- **Data residency:** region-pinned deployments for customers who require EU/US/other residency — enabled by the single-region, portable footprint.
- **Contracts & classification:** DPA support, data classification, and clear data-handling documentation.
- **Auditability:** the reproducibility/lineage system (§4) is the technical backbone of governance — every decision is explainable and reproducible on demand.

These are what let sales answer a security questionnaire without stalling.

---

## 19. Development Roadmap

Milestone-based, now interleaving enterprise hardening. **Day-one items are in-phase; certification-style items are explicitly phased.**

| Phase | Objective | Enterprise additions vs. prior plan | Acceptance criteria |
|---|---|---|---|
| **0 — Foundation** | Repo, envs, CI | Tenancy layer + RLS scaffolding; seeded multi-tenant fixtures; SBOM in CI | Compose runs; isolation test harness exists |
| **1 — Analytics + provenance** | Extract pipeline as tested library | **Run provenance** (input hash, code/config versions); golden + reproducibility tests | Same input+versions → identical decision object |
| **2 — Backend/API** | Governed jobs | Tenant scoping everywhere + RLS; idempotent jobs; per-tenant quotas; API versioning; audit log | Cross-tenant access tests fail; runs reproducible; audit entries written |
| **3 — Frontend** | Dashboard on the API | **WCAG 2.1 AA** + performance budgets in CI | axe checks pass; budgets enforced; visual parity |
| **4 — Reports** | HTML/PDF from decision object | Report provenance footer (versions/hash) | PDF matches dashboard; reproducible |
| **5 — Integration & hardening** | Wire together | **OTel traces + metrics + SLO alerting**; config snapshotting; feature flags | Full flow in staging observable end to end |
| **6 — Testing** | Confidence | **Isolation, load, security, resilience, a11y** suites | All suites green; budgets/SLOs baselined |
| **7 — Deployment** | Production infra | **Multi-AZ**, PITR + **rehearsed restore**, progressive delivery + rollback | DR restore demonstrated; canary + auto-rollback proven |
| **8 — Production & compliance readiness** | Operate safely | On-call + incident response + runbooks; SOC 2 control implementation; retention/deletion; residency option | Operational + security review passed; questionnaire-ready |
| **P+ (phased)** | Enterprise scale | SSO/SAML + SCIM; single-tenant VPC option; BYOK; SOC 2 Type II; Polars/DuckDB for large data | Delivered as demand/compliance require |

Sequencing rationale unchanged: **the analytics library + decision-object schema + provenance come first** because they are the contract and the audit backbone everything depends on.

---

## 20. Risk Assessment

| Risk | Type | Mitigation |
|---|---|---|
| Cross-tenant data leakage | Security (severe) | App scoping **+ RLS backstop + isolation tests that must fail on breach** |
| Unreproducible/undefensible decisions | Product/trust | Provenance per run (§4); reproducibility tests |
| Analytics correctness regressions | Technical | Golden + property-based tests gate every change |
| Availability/DR gaps | Operational | Multi-AZ, PITR, **rehearsed restore**, SLOs + error budgets |
| Compliance blocks sales | Business | SOC 2 controls day-one; retention/deletion; residency; DPA |
| Accessibility procurement gate | Business | WCAG 2.1 AA + automated checks + VPAT |
| Large-dataset performance | Technical | Budgets + load tests; worker scaling; Polars/DuckDB path reserved |
| Noisy-neighbor starvation | Operational | Per-tenant quotas + queue limits |
| Over-engineering (K8s/microservices) | Architectural | Explicit "modular monolith, no distributed systems in V1" principle |
| Vendor lock-in | Architectural | Containers, S3-compatible, OIDC/OTel standards; portable footprint |
| Schema/API churn breaking clients | Architectural | Versioned API + contracts; expand/contract only |

---

## 21. Future Evolution (without a rewrite)

All prior evolution paths hold (Polars/DuckDB behind the analytics interface; plugin analytics/policies/components on the stable decision object; continuous monitoring via scheduled runs; connectors and write-back as new adapters/renderers; a grounded AI copilot that *reads* the decision object and never authors conclusions). The enterprise layers added here are the ones that most expand the addressable market:

- **Single-tenant VPC / on-prem** offerings from the same image (tenancy is a clean layer).
- **Enterprise identity** (SSO/SCIM) and **BYOK** slot into the existing auth/KMS layers.
- **SOC 2 Type II / ISO 27001** become audit exercises because the controls exist from day one.
- **Regional expansion** via the portable single-region footprint.

Because tenancy, provenance, governance, and observability are layers rather than rewrites, the monolith scales into an enterprise platform by extension.

---

## 22. Verification Summary — Is This Now Enterprise-Grade & Production-Oriented?

**Yes, with the additions above; the prior version was not, on its own.** The re-review found the original strong on developer experience, analytics correctness, and lean architecture, but **silent or thin on the eight properties that define enterprise-grade** (Section 0). This revision closes each gap:

- Tenancy & isolation → **§3** (added)
- Reproducibility/lineage/audit → **§4** (added; also the product's core promise)
- Availability & DR with SLOs → **§15** (added)
- Observability & incident response → **§16** (corrected from "keep it light")
- Compliance & data governance → **§18** (added)
- Accessibility & performance budgets → **§6/§13** (added)
- Load/security/resilience/isolation testing → **§13** (added)
- Flexible deployment (SaaS + single-tenant VPC), progressive delivery, API versioning, KMS/BYOK, SSO/SCIM → **§14/§7/§17**

Crucially, none of this required abandoning the lean modular-monolith. Enterprise-grade here is a matter of **isolation, auditability, availability, governance, observability, accessibility, and operational discipline** — layered onto a simple architecture — not of structural complexity. The one discipline to hold throughout: resist microservices/Kubernetes until real scale or compliance signals demand them, and keep the **decision object + provenance** as the contract the whole system is organized around.

*Recommended pre-build spike (unchanged and reaffirmed): validate the decision-object schema, the analytics module interface, **and the provenance model** against three or four genuinely different compatible datasets before frontend work begins — that contract plus its audit backbone is what makes this an enterprise decision platform rather than a dashboard generator.*

# Phase-8 follow-up: biphenyl gameplay exclusion (quick-001, 2026-10-01)

quick-001 removed set_a biphenyl from REAL gameplay (pickup spawn pool +
head selection) via `spawn.GAMEPLAY_EXCLUDED_MOLS`. The dataset/manifest
entry is INTENTIONALLY KEPT (TDD + smoke fixtures + viewer display;
tests/test_demo_data.py contract unchanged; DATA_SOURCES sign-off flow
unaffected).

Per owner directive, NO phase-8 file was touched in quick-001. Phase 8
(08-01..08-10, Demo Data / Docs / Release Audit) MUST follow up:

- Update any 08-* docs / release-audit language that presents biphenyl
  as a playable or stackable species (demo docs, controls recap,
  requirements recap). Biphenyl remains: loadable + viewable from the
  manifest, ABSENT from the gameplay pickup pool and head combo.
- Re-scope STACK-05 "refuse demonstrator" wording if it implies
  gameplay reachability: the REFUSE_ATOM path is now TEST-only
  (direct-seeded fixtures in tests/test_placement.py +
  tests/test_phase5_integration.py). Suggest phrasing: "permanent
  refuse-path demonstrator in the test suite; excluded from live
  gameplay pools since 2026-10-01 (probe-proven always-clash geometry)".
- Optionally note in player-facing docs that the demo set offers 4
  stackable species (+ uploads).

Post-execution optional (NOT run in quick-001): the full --smoke battery
— smoke/04 exercises only the data path (manifest -> setloader ->
materialize -> head switch -> cleanup_srp), never the gameplay spawn
pool, and is unaffected by design.

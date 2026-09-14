# M1 Improvement Plan

## Target outcome

Provide reusable result, data, analysis, and rendering seams without weakening
the M0 statistical, license, or sample-reconciliation gates.

| Priority | Finding/risk | Smallest safe slice | Acceptance evidence | Owner | Status |
|---:|---|---|---|---|---|
| 1 | Analysis/render coupling | Split domain result/data/analysis from Matplotlib adapter | Import-boundary and behavior tests | Technical lead | Complete |
| 2 | Reversible array write flag | Use immutable backing bytes for retained sample | Mutation and write-flag tests | Technical lead | Complete |
| 3 | No coverage gate | Pin coverage tool and enforce measured branch baseline | `make check` reports at least 75% | Technical lead | Complete |

## Deferred item

Raise repository coverage above the initial baseline by testing the inherited
CLI entry points. Reconsider before the first supported release; this is not a
reason to omit tests for new domain paths, which should remain near complete.

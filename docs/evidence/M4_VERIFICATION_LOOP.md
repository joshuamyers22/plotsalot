# M4 Verification Loop

- Date: 2026-09-14
- Scope: approved C1–C5/G5 implementation and `0.2` categorical candidate
- Pass budget: three evidence-changing passes after method approval
- Result: complete; technical gates, independent review, and final acceptance pass

## Pass 1: shared boundary and complete method paths

Implemented the owned raw/count-weighted table, schema-v1 categorical result,
one-way Pearson goodness-of-fit, independent Pearson association, exact binary
paired inference, noncentral effect intervals, complete pairwise/stratum
families, semantic bar/pie renderers, and atomic grouped variants.

Focused tests exposed and corrected runtime shadowing of Python's `type`, strict
typing gaps at SciPy/Statsmodels/Matplotlib boundaries, and missing resource
fields in pre-existing result schemas. The pass ended with all existing M0–M3
tests passing and the M4 happy paths operational.

## Pass 2: contract reconciliation and reference evidence

Contract review found that follow-up results needed their exact observed
subtables and that confidence level needed a direct result field rather than
being recoverable only through intervals. Both were added with contradiction
checks and schema coverage. Paired empty margins and grouped color domains were
made explicit failures. Raw aggregation was vectorized without count expansion.

Pinned R 4.5.1 regenerated one-way, independent, paired, raw-row, aggregate,
bar, pie, and grouped objects. Base R independently verifies the approved
Pearson, exact-binomial, effect, and Holm fields. The verifier also asserts the
upstream Fisher, McNemar, and Pearson's-C adaptations rather than treating them
as parity.

## Pass 3: adversarial, performance, and production gates

Failure tests expanded every new domain module to at least 93% branch coverage.
Pairwise annotation text was made deterministic, wrapped, and figure-bounded;
no hypothesis is silently dropped. The retained five-sample benchmark covers
one million raw rows, 20 levels/190 pairwise tests, 20x20/400-cell tables,
weighted total 1,000,000,000, 20 groups, and 20 pie facets.

Same-host M0/M2/M3 reruns found no sustained regression over 20%. One M3 run
showed three sub-1.5 ms absolute timing increases over the investigation
threshold; three additional five-sample medians for each affected workload
returned below the threshold. There were no memory regressions over 20%.

The final technical pass includes Ruff, strict Pyright, 145 tests, 91% project
branch coverage, oracle/benchmark verification, OSV and license audit, source
and wheel builds, and an isolated-wheel categorical render/serialization smoke.

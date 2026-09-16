# M7C API and Schema Hardening Verification

- Date: 2026-09-15
- Track: M7C adversarial stability
- Status: implementation complete; M7D release-candidate review remains
- Governing decision: M7-D3 in `docs/MILESTONE_7.md`
- Retained corpus: `docs/m7/golden-results.json`
- Machine inventory: `docs/m7/public-contract.json`

## Accepted boundary

M7C preserves all 144 root exports shipped in `0.1.1`. The accepted M7B
classification remains unchanged: 137 exports are stable candidates and seven
dedicated fixed-Student-t4 robust-meta exports are experimental. M7C changes no
estimator, analysis population, selector behavior, error code, or runtime
fallback rule.

The retained corpus contains 51 examples covering all 25 public serialized
result types and all 49 distinct `(schema path, schema_version, analysis)`
triples. Fifty examples exercise stable variants; the sole experimental entry
is `RobustMetaResult` schema v2. Duplicate discriminator triples are retained
where distinct public result types share them, including labeled-dot outer and
nested one-sample records.

## Adversarial findings and dispositions

| Finding | Evidence | Disposition |
|---|---|---|
| Six emitted grouped robust analysis identities and their `resampling` record were absent from `grouped-result.schema.json` | Runtime `GroupedResult` identities and retained robust grouped examples | Closed by adding the emitted identities, robust-result reference, and bounded resampling object; serialized output is unchanged |
| `composition-result.schema.json` required `maximum_cells` and `maximum_total_count`, but `CompositionResult.to_dict()` never emits them | Retained composition example versus schema validation | Closed by removing the two non-emitted requirements; serialized output is unchanged |
| Bayesian schemas accepted unknown top-level properties | Unknown-property mutation replay | Closed with an exhaustive top-level property set and `additionalProperties: false`; all emitted Bayesian variants still validate |
| Bayesian computation schema omitted its emitted tolerance/error fields | All eight Bayesian discriminator examples | Closed by declaring the existing nullable computation fields; serialized output is unchanged |

These are pre-1.0 schema-document corrections, not runtime-result migrations.
The schema identifiers and serialized discriminator/version pairs remain
unchanged. The exact corrected schema bytes become the 1.0 baseline if M7D is
accepted.

## Retained checks

`tests/test_m7c_stability.py` enforces:

- Draft 2020-12 metaschema validity for all 12 checked-in schemas;
- exact golden coverage of all public serialized result types and all manifest
  discriminator triples;
- strict JSON round trips and schema validation for all 51 examples;
- rejection of missing fields, wrong JSON types, wrong schema versions, wrong
  analysis discriminators, and unknown top-level properties for every example;
- replay of representative `0.1.1` classical, robust, Bayesian, coefficient,
  grouped, and meta-analysis call shapes against retained schemas;
- exact reconciliation of the sole stable coded exception and its 16 literal
  `M6CMetaError.code` values;
- invalid, degenerate, resource-ceiling, and atomic grouped refusal behavior;
  and
- runtime reconciliation of `main`, `facet_*`, `panel_*`, and grouped member
  semantic-axis contracts.

`jsonschema==4.25.1` is locked as a development-only dependency. It is not a
package runtime dependency and does not alter the no-network/no-R installed
artifact boundary.

## Exit

The exact M7C candidate passed `make check`: Ruff, formatting, strict Pyright,
294 tests, 92% branch coverage, 127-document link validation, and public-
contract drift validation. `make audit build` found no known runtime dependency
vulnerabilities or adverse project statuses, passed the dependency-license
policy, and built both the `0.1.1` source distribution and wheel.

M7-F003 is closed: the manifest, retained corpus, schemas, mutation checks,
refusal inventory, migration replay, and semantic axes now form an enforceable
M7C boundary. M7D is the next and final M7 track. It must repeat the clean
package/platform, oracle, benchmark, documentation, security, and independent
review gates on the exact candidate; this record does not approve plotsalot
1.0.

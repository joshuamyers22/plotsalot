.PHONY: setup format lint typecheck test docs public-contract update-public-contract update-m7c-golden check audit build verify-artifacts oracle verify-oracle benchmark verify-benchmark m7b-smoke
setup:
	uv sync --frozen --dev
format:
	uv run ruff format .
lint:
	uv run ruff check .
	uv run ruff format --check .
typecheck:
	uv run pyright
test:
	uv run coverage run -m unittest discover -s tests
	uv run coverage report
docs:
	uv run python tools/check_docs.py
public-contract:
	uv run python tools/public_contract.py --check
update-public-contract:
	uv run python tools/public_contract.py --write
update-m7c-golden:
	uv run python tools/m7c_golden.py --write
check: lint typecheck test docs public-contract
audit:
	uv audit --preview-features audit-command --locked --no-dev
	uv run python tools/check_licenses.py
build:
	uv build --clear --no-sources
	$(MAKE) verify-artifacts
verify-artifacts:
	uv run python tools/verify_artifacts.py
oracle:
	docker build --platform linux/arm64 --build-arg GGSTATSPLOT_REVISION=7a724cd0ab55668b9d0b2e84b12c711c5be68ac8 -t plotsalot-r-oracle:m0 -f oracle/Dockerfile .
	docker run --rm --platform linux/arm64 -v "$(CURDIR):/work" plotsalot-r-oracle:m0
	uv run python tools/verify_oracle.py --write-manifest
	uv run python tools/verify_oracle.py
verify-oracle:
	uv run python tools/verify_oracle.py
benchmark:
	uv run python benchmarks/benchmark_m0.py
	uv run python benchmarks/benchmark_m2.py
	uv run python benchmarks/benchmark_m3.py
	uv run python benchmarks/benchmark_m4.py
	uv run python benchmarks/benchmark_m5a.py
	uv run python benchmarks/benchmark_m5b.py
	uv run python benchmarks/benchmark_m6a.py
	uv run python benchmarks/benchmark_m6b.py
	uv run python benchmarks/benchmark_m6c.py
	uv run python tools/verify_benchmark.py
verify-benchmark:
	uv run python tools/verify_benchmark.py
m7b-smoke:
	uv run python tools/calibrate_m7b.py --run smoke --workers 8

"""Guards for keeping the GitHub Actions test matrix focused and fast."""

from pathlib import Path

import tomllib

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (REPO_ROOT / relative).read_text(encoding="utf-8")


def _job_block(text: str, job_name: str, next_job_name: str) -> str:
    start = text.index(f"  {job_name}:\n")
    end = text.index(f"  {next_job_name}:\n", start)
    return text[start:end]


def test_static_analysis_runs_once_outside_python_test_matrix() -> None:
    text = _read(".github/workflows/tests.yml")
    test_job = _job_block(text, "test", "docs")

    assert "  lint-type:\n" in text
    assert "name: Static analysis" in text
    assert text.count("name: Ruff lint") == 1
    assert text.count("name: Mypy") == 1
    assert "name: Ruff lint" not in test_job
    assert "name: Mypy" not in test_job


def test_coverage_is_collected_once_on_canonical_python() -> None:
    text = _read(".github/workflows/tests.yml")

    assert "if: matrix.python-version == '3.12'" in text
    assert "if: matrix.python-version != '3.12'" in text
    assert "name: coverage-3.12" in text
    assert "coverage-${{ matrix.python-version }}" not in text


def test_test_matrix_runs_pytest_with_xdist_workers() -> None:
    workflow = _read(".github/workflows/tests.yml")
    pyproject = tomllib.loads(_read("pyproject.toml"))
    dev_dependencies = pyproject["dependency-groups"]["dev"]

    assert any(dependency.startswith("pytest-xdist") for dependency in dev_dependencies)
    assert workflow.count("uv run pytest -q -n auto") == 2
    assert "uv run pytest -q -n auto \\\n            --cov=tmhp" in workflow

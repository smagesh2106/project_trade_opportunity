from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "run_incremental_ingestion.sh"
)


def test_incremental_runner_script_exists():
    assert SCRIPT_PATH.exists(), (
        f"Missing incremental runner: {SCRIPT_PATH}"
    )


def test_incremental_runner_script_contains_required_contract():
    text = SCRIPT_PATH.read_text(encoding="utf-8")

    required_fragments = [
        "set -euo pipefail",
        ".venv/bin/python",
        "-m app.ingestion.run_comtrade",
        "--reporter-code",
        "--incremental",
        "--flow",
        "--hs-code",
        "--max-records",
        "incremental_ingestion.log",
    ]

    for fragment in required_fragments:
        assert fragment in text, (
            f"Expected runner script to contain: {fragment}"
        )


def test_incremental_runner_has_safe_project_directory_resolution():
    text = SCRIPT_PATH.read_text(encoding="utf-8")

    assert 'SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"' in text
    assert 'cd "$SCRIPT_DIR"' in text


if __name__ == "__main__":
    test_incremental_runner_script_exists()
    print("PASS incremental runner exists")

    test_incremental_runner_script_contains_required_contract()
    print("PASS incremental runner command contract")

    test_incremental_runner_has_safe_project_directory_resolution()
    print("PASS incremental runner working-directory handling")

    print("Incremental runner tests passed.")

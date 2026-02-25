#!/usr/bin/env python3
"""Run comprehensive benchmarks for all frameworks."""
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent
SAMPLES_DIR = BASE_DIR / "samples"

BENCHMARKS = [
    ("autogen", "single-agent"),
    ("autogen", "multi-agent-servicebus"),
    ("langgraph", "single-agent"),
    ("langgraph", "multi-agent-servicebus"),
    ("semantic-kernel", "single-agent"),
    ("semantic-kernel", "multi-agent-servicebus"),
]

def run_benchmark(framework: str, pattern: str) -> tuple[str, float]:
    """Run a single benchmark and return status and elapsed time."""
    sample_dir = SAMPLES_DIR / framework / pattern
    if not sample_dir.exists():
        return "SKIP", 0.0
    
    start = time.time()
    try:
        result = subprocess.run(
            ["uv", "run", "python", "src/main.py"],
            cwd=sample_dir,
            capture_output=True,
            timeout=180,
        )
        status = "OK" if result.returncode == 0 else "FAIL"
    except subprocess.TimeoutExpired:
        status = "TIMEOUT"
    except Exception as e:
        status = f"ERROR: {e}"
    
    elapsed = time.time() - start
    return status, elapsed


def main():
    print("=" * 60)
    print("Comprehensive Benchmark Results")
    print("=" * 60)
    
    results = []
    for framework, pattern in BENCHMARKS:
        print(f"\n[{framework}/{pattern}] Running...", end=" ", flush=True)
        status, elapsed = run_benchmark(framework, pattern)
        print(f"{status} ({elapsed:.1f}s)")
        results.append((framework, pattern, status, elapsed))
    
    print("\n" + "=" * 60)
    print("Summary Table")
    print("=" * 60)
    print(f"{'Framework':<20} {'Pattern':<25} {'Status':<8} {'Time':<8}")
    print("-" * 60)
    
    for framework, pattern, status, elapsed in results:
        print(f"{framework:<20} {pattern:<25} {status:<8} {elapsed:.1f}s")
    
    print("=" * 60)


if __name__ == "__main__":
    main()

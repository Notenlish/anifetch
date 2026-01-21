# tests/benchmark.py

"""
Benchmarking script for comparing the performance of Anifetch with Neofetch and Fastfetch.
Only works with 'pip' installation.
"""

import subprocess
import time
import shlex
import platform

OS = platform.system()
py_name = ""
if OS == "Linux" or OS == "Darwin":
    py_name = "python3"
elif OS == "Windows":
    py_name = "py"


def time_check(
    command: str, count: int, preheat: bool = False
) -> tuple[str, float, float]:
    args = shlex.split(command)
    if preheat:  # Preheat the cache by running the command once before timing
        subprocess.call(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    total = 0
    for _ in range(count):
        if command.startswith("neofetch") or command.startswith("fastfetch"):
            st = time.time()
            subprocess.call(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            total += time.time() - st
        else:
            output = subprocess.check_output(args, stderr=subprocess.DEVNULL)
            total += float(output)

    average = total / count
    return command, total, average


def run_all():
    count = 10
    video = "example.mp4"
    common_args = f"{video} -W 60 -r 10 --benchmark"

    tests = [
        ("Neofetch", "neofetch", True),
        ("Fastfetch", "fastfetch", True),
        (
            "Anifetch (no cache, Neofetch)",
            f"{py_name} -m anifetch {common_args} --force-render",
            False,
        ),
        ("Anifetch (cached, Neofetch)", f"{py_name} -m anifetch {common_args}", True),
        (
            "Anifetch (no cache, Fastfetch)",
            f"{py_name} -m anifetch {common_args} -ff --force-render",
            False,
        ),
        (
            "Anifetch (cached, Fastfetch)",
            f"{py_name} -m anifetch {common_args} -ff",
            True,
        ),
    ]

    results = []
    print("Running benchmarks...\n(This may take a moment)\n")

    for name, cmd, preheat in tests:
        print(f"Running: {name}...", end="", flush=True)
        try:
            _, total, avg = time_check(cmd, count, preheat)
            results.append((name, total, avg))
            print(" done.")
        except Exception as e:
            results.append((name, None, None))
            print(f" failed: {e}")

    print("\n=== BENCHMARK RESULTS ===\n")
    print(f"Common args: {common_args}")
    for name, total, avg in results:
        if total is None:
            print(f"{name}: failed")
        else:
            print(
                f"{name}:\n  Total time: {total:.2f} sec\n  Avg per run: {avg:.2f} sec\n"
            )


if __name__ == "__main__":
    run_all()

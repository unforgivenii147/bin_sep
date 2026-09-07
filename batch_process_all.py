import os
import subprocess
import concurrent.futures
from pathlib import Path

FILES_TO_EXCLUDE = {
    "afk_autoflake.py",
    "annotate_types.py",
    "type_hinter.py",
    "annotate.py",
    "add_typing.py",
    "batch_process_all.py",
}

BIN_DIR = "/home/adnanonagh/bin/"
ENV = os.environ.copy()
ENV["PATH"] = f"/home/adnanonagh/.local/bin:{ENV.get('PATH', '')}"


def process_file(file_path):
    file_name = os.path.basename(file_path)
    if file_name in FILES_TO_EXCLUDE:
        return None, "Excluded"

    # Step 1: Syntax Check
    res = subprocess.run(
        ["python3", "-m", "py_compile", file_path], capture_output=True, text=True
    )
    if res.returncode != 0:
        return file_path, f"Initial Syntax Check Failed: {res.stderr.strip()}"

    # Step 2: Clean Imports
    # Using the requested helper script
    res = subprocess.run(
        ["python3", "/home/adnanonagh/bin/afk_autoflake.py", "-a", file_path],
        env=ENV,
        capture_output=True,
        text=True,
    )

    # Step 3: Add Type Hints
    # Using the requested helper script
    res = subprocess.run(
        ["python3", "/home/adnanonagh/bin/annotate_types.py", file_path],
        env=ENV,
        capture_output=True,
        text=True,
    )

    # Step 4: Format
    res = subprocess.run(
        ["autopep8", "--in-place", file_path], env=ENV, capture_output=True, text=True
    )

    # Step 5: Final Check
    res = subprocess.run(
        ["python3", "-m", "py_compile", file_path], capture_output=True, text=True
    )
    if res.returncode != 0:
        return file_path, f"Final Syntax Check Failed: {res.stderr.strip()}"

    return file_path, "Success"


def main():
    py_files = sorted(
        [str(p) for p in Path(BIN_DIR).glob("*.py") if p.name not in FILES_TO_EXCLUDE]
    )

    print(f"Found {len(py_files)} files to process.")

    results = []
    # Use ProcessPoolExecutor for CPU-bound tasks and subprocess management
    # Using a reasonable number of workers to avoid resource exhaustion
    with concurrent.futures.ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        future_to_file = {executor.submit(process_file, f): f for f in py_files}
        for future in concurrent.futures.as_completed(future_to_file):
            try:
                res = future.result()
                if res[0] is not None:
                    results.append(res)
            except Exception as e:
                # Catch unexpected errors in the process pool
                results.append(("Unknown", str(e)))

    successes = [f for f, m in results if m == "Success"]
    failures = [(f, m) for f, m in results if m != "Success"]

    print(f"\nProcessing Complete.")
    print(f"Total processed: {len(results)}")
    print(f"Successes: {len(successes)}")
    print(f"Failures: {len(failures)}")

    if failures:
        print("\nFailures:")
        for f, m in failures:
            print(f"{f}: {m}")


if __name__ == "__main__":
    main()

import subprocess
import sys
from pathlib import Path

TARGET_SCRIPT = r"Y:\Claude Stuff\Checklist\run_daily_update.py"
TARGET_DIR = str(Path(TARGET_SCRIPT).parent)


def main():
    result = subprocess.run([sys.executable, TARGET_SCRIPT], cwd=TARGET_DIR)
    if result.returncode != 0:
        print(f"\nrun_daily_update.py exited with an error (code {result.returncode}).")
    try:
        input("\nPress Enter to close...")
    except EOFError:
        pass


if __name__ == "__main__":
    main()

import os
import sys
from pathlib import Path

TARGET_DIR = Path(r"Y:\Claude Stuff\Checklist")


def main():
    os.chdir(TARGET_DIR)
    sys.path.insert(0, str(TARGET_DIR))
    import run_daily_update
    try:
        run_daily_update.main()
    except SystemExit as e:
        print(f"\nrun_daily_update failed: {e}")
    try:
        input("\nPress Enter to close...")
    except EOFError:
        pass


if __name__ == "__main__":
    main()

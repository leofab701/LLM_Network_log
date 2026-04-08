import csv
from pathlib import Path

LOG_PATH = Path("/var/log/mikrotik/sample_logs.txt")
OUT_CSV  = Path("dataset_1000_windows.csv")

WINDOW_LINES = 10
NUM_WINDOWS = 1000

def main():
    lines = LOG_PATH.read_text(errors="replace").splitlines()
    # keep only non-empty lines
    lines = [ln for ln in lines if ln.strip()]

    total_needed = WINDOW_LINES * NUM_WINDOWS
    if len(lines) < total_needed:
        raise SystemExit(f"Not enough lines. Have {len(lines)}, need {total_needed}.")

    with OUT_CSV.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "window_text", "label"])  # label you will fill: NORMAL/ANOMALOUS
        for i in range(NUM_WINDOWS):
            chunk = lines[i * WINDOW_LINES:(i + 1) * WINDOW_LINES]
            window_text = "\n".join(chunk)
            w.writerow([f"w{i:03d}", window_text, ""])  # leave label empty for now

    print(f"Wrote {NUM_WINDOWS} windows to {OUT_CSV}")

if __name__ == "__main__":
    main()

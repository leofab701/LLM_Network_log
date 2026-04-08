import os
import csv
import json
import time
from typing import Dict, Any

from openai import OpenAI

INPUT_CSV = "dataset_1000_windows_labeled.csv"
OUTPUT_CSV = "gpt_results.csv"

MODEL = "gpt-4.1-mini"   # good cost/quality for milestone
SLEEP_SEC = 0.2          # polite pacing

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

SYSTEM_MSG = "You are a network security analyst for a Wireless ISP (WISP)."

def build_prompt(window_text: str) -> str:
    return f"""
Classify the following MikroTik router log window as NORMAL or ANOMALOUS.

Return ONLY valid JSON with keys:
- label: "NORMAL" or "ANOMALOUS"
- type: one of ["auth","routing","interface","scan","resource","config","other"]
- reason: 1-2 sentences (concise)

Log window:
{window_text}
""".strip()

def parse_json_loose(s: str) -> Dict[str, Any]:
    """
    Tries to parse JSON even if the model wraps it with extra text.
    """
    s = s.strip()
    # Try direct parse
    try:
        return json.loads(s)
    except Exception:
        pass

    # Try to extract first {...} block
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(s[start:end+1])

    raise ValueError("Could not parse JSON from model output.")

def main():
    with open(INPUT_CSV, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    out_fields = [
        "id",
        "true_label",
        "gpt_label",
        "gpt_type",
        "gpt_reason",
        "raw_response"
    ]

    with open(OUTPUT_CSV, "w", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=out_fields)
        writer.writeheader()

        for i, row in enumerate(rows):
            sample_id = row["id"]
            window_text = row["window_text"]
            true_label = row.get("label", "").strip()

            prompt = build_prompt(window_text)

            try:
                resp = client.responses.create(
                    model=MODEL,
                    input=[
                        {"role": "system", "content": SYSTEM_MSG},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0
                )

                text = resp.output_text
                data = parse_json_loose(text)

                gpt_label = str(data.get("label", "")).strip().upper()
                gpt_type = str(data.get("type", "")).strip().lower()
                gpt_reason = str(data.get("reason", "")).strip()

                writer.writerow({
                    "id": sample_id,
                    "true_label": true_label,
                    "gpt_label": gpt_label,
                    "gpt_type": gpt_type,
                    "gpt_reason": gpt_reason,
                    "raw_response": text
                })

                print(f"[{i+1:03d}/{len(rows)}] {sample_id}: {true_label} -> {gpt_label} ({gpt_type})")

            except Exception as e:
                # Write row with error info
                writer.writerow({
                    "id": sample_id,
                    "true_label": true_label,
                    "gpt_label": "ERROR",
                    "gpt_type": "",
                    "gpt_reason": f"Exception: {e}",
                    "raw_response": ""
                })
                print(f"[{i+1:03d}/{len(rows)}] {sample_id}: ERROR {e}")

            time.sleep(SLEEP_SEC)

    print(f"\nSaved results to: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()

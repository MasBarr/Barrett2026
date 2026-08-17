"""
build_activity.py  —  tidy Lab A (Cynthia) circadian data for the standardized set.
Reads the ClockLab exports in ../Cynthia and writes two long-format tables:
  activity_counts_long.csv   — per-10-min actogram (counts + light level), for the 2-D actogram
  activity_metrics_long.csv  — per-mouse circadian summary (RA, IV, IS, total counts, ...)
Lab A only (single-housed circadian study); Lab B has no ClockLab recordings.
"""
import os, glob, re
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CYN = os.path.join(HERE, "..", "Cynthia")
TRF_START = pd.Timestamp("2026-06-25")            # Lab A day_index = 0 (matches the other tables)


# ---------- actogram counts ----------
def parse_counts(path, phase, mouse):
    with open(path) as f:
        head = [next(f) for _ in range(3)]
    start = pd.to_datetime(head[2].split(",")[0].strip(), format="%d-%b-%Y")  # e.g. 17-Jun-2026
    d = pd.read_csv(path, skiprows=3).dropna(subset=["Day"])
    d["Day"] = d["Day"].astype(int)
    date = start + pd.to_timedelta(d["Day"] - d["Day"].min(), unit="D")
    return pd.DataFrame({
        "dataset": "Lab A", "subject_id": str(mouse), "phase": phase,
        "date": date.dt.date,
        "day_index": (date - TRF_START).dt.days,
        "time_of_day_h": (d["Hr"].astype(float) + d["Min"].astype(float) / 60).round(3),
        "counts_per_min": pd.to_numeric(d["Cnts/min"], errors="coerce"),
        "light_level": pd.to_numeric(d["Lights"], errors="coerce"),
    })


counts = []
for path in sorted(glob.glob(os.path.join(CYN, "*_Counts.csv"))):
    m = re.match(r"(ADL|TRF)_(\d+)_Counts\.csv", os.path.basename(path))
    if m:
        counts.append(parse_counts(path, m.group(1), m.group(2)))
counts = pd.concat(counts, ignore_index=True)
counts.to_csv(os.path.join(HERE, "activity_counts_long.csv"), index=False)


# ---------- circadian metrics ----------
METRICS = {"Total counts": "total_counts", "RA": "RA", "IV": "IV", "IS": "IS",
           "Alpha counts": "alpha_counts", "Rho counts": "rho_counts",
           "Amplitude": "amplitude", "MESOR": "mesor",
           "L Avg": "light_phase_activity", "M Avg": "dark_phase_activity"}
rows = []
for phase in ("ADL", "TRF"):
    a = pd.read_csv(os.path.join(CYN, f"E4_single-housed_clocklab__{phase}_Activity.csv"))
    a = a[pd.to_numeric(a["File"], errors="coerce").notna()]
    for _, r in a.iterrows():
        for col, name in METRICS.items():
            rows.append({"dataset": "Lab A", "subject_id": str(int(float(r["File"]))),
                         "phase": phase, "metric": name, "value": float(r[col])})
metrics = pd.concat([pd.DataFrame(rows)], ignore_index=True)
metrics.to_csv(os.path.join(HERE, "activity_metrics_long.csv"), index=False)

print(f"activity_counts_long.csv   rows={len(counts):,}  mice={counts.subject_id.nunique()}  "
      f"phases={sorted(counts.phase.unique())}  day_index {counts.day_index.min()}..{counts.day_index.max()}")
print(f"activity_metrics_long.csv  rows={len(metrics)}  metrics={sorted(metrics.metric.unique())}")

"""
set_labA_day0.py  —  set Lab A day_index so day 0 = first study/ADL day (2026-06-17).

Study-day numbering for Lab A (single-housed, ADL -> TRF):
    day 0..6  = ADL       (6/17 .. 6/23)
    day 7     = transition (6/24, ADL end / TRF start; some units still open all day 6/23)
    day 8..14 = TRF        (6/25 .. 7/1)
This gives a clean 0..14 axis that the figure plots as-is (no code shift).
Lab B is untouched (its own timeline).

Recomputes day_index from the `date` column for Lab A only; tables without a date column
are offset by the equivalent constant. Reads current tables from GitHub, writes next to this
script. Re-run + re-push after any upstream change.
"""
import os
import pandas as pd

BASE = "https://raw.githubusercontent.com/MasBarr/Barrett2026/main/Data/standardized"
HERE = os.path.dirname(os.path.abspath(__file__))
REF = pd.Timestamp("2026-06-17")                 # Lab A day 0
GITHUB_REF = pd.Timestamp("2026-06-25")          # current GitHub Lab A day 0
OFFSET = (GITHUB_REF - REF).days                 # = 8 (for tables lacking a date column)
TABLES = ["body_weight_long.csv", "food_intake_long.csv", "device_events_long.csv.gz",
          "door_transitions_long.csv", "device_summary_long.csv", "activity_counts_long.csv"]

for t in TABLES:
    d = pd.read_csv(f"{BASE}/{t}")
    la = d.dataset == "Lab A"
    if "date" in d.columns:
        d.loc[la, "day_index"] = (pd.to_datetime(d.loc[la, "date"]) - REF).dt.days
    else:
        d.loc[la, "day_index"] = d.loc[la, "day_index"] + OFFSET
    out = os.path.join(HERE, t)
    d.to_csv(out, index=False, compression="gzip" if t.endswith(".gz") else "infer")
    day0 = sorted(d[(d.dataset == "Lab A") & (d.day_index == 0)].get("date", pd.Series()).dropna().unique())[:1]
    print(f"wrote {t:30} Lab A day0 -> {day0}")

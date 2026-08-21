"""
shift_day0_to_transition.py  —  set Lab A day_index = 0 to the ADL->TRF transition day (6/24).

The Tumbly units were switched to TimedDoor mode on 6/23 (~1 PM), but some units stayed
open all day that day, so 6/23 is not a clean TRF day. The first synchronized restriction
(4 AM door close) was 6/24 — that is the ADL->TRF transition, and we define it as day 0.

Original standardized tables referenced day 0 = 6/25 (first full TRF day). This shifts
Lab A day_index by +1 so day 0 = 6/24 (transition). Lab B is untouched (its own timeline).
Phase labels are unchanged: ADL (day -7..-1), transition (day 0), TRF (day 1..7).

Reads the current standardized tables from GitHub and rewrites them next to this script.
Re-run + re-push after any upstream data change. (activity_metrics_long / subjects have no
day_index and are left as-is.)
"""
import os
import pandas as pd

BASE = "https://raw.githubusercontent.com/MasBarr/Barrett2026/main/Data/standardized"
HERE = os.path.dirname(os.path.abspath(__file__))
TABLES = ["body_weight_long.csv", "food_intake_long.csv", "device_events_long.csv.gz",
          "door_transitions_long.csv", "device_summary_long.csv", "activity_counts_long.csv"]

for t in TABLES:
    d = pd.read_csv(f"{BASE}/{t}")
    d.loc[d.dataset == "Lab A", "day_index"] = d.loc[d.dataset == "Lab A", "day_index"] + 1
    out = os.path.join(HERE, t)
    d.to_csv(out, index=False, compression="gzip" if t.endswith(".gz") else "infer")
    day0 = sorted(d[(d.dataset == "Lab A") & (d.day_index == 0)].get("date", pd.Series()).unique())[:1]
    print(f"wrote {t:30} Lab A day0 -> {day0}")

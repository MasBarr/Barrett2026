"""
build_device_events.py
Concatenate every raw Tumbly device log into ONE tidy long-form table so the
per-sample signals (door open/close, errors, battery, servo) can be plotted over
time at full resolution. Reads the header-cleaned per-file logs in ../Cynthia and
../Winston (verified faithful to the originals) and writes:

    standardized/device_events_long.csv.gz    (gzip; pandas & raw-GitHub read it directly)

Columns:
  dataset, unit, datetime, date, day_index, time_of_day_h,
  task, battery_v, light_sensor, door_open, servo_feedback, error, is_error
"""
import glob, os, re
import numpy as np
import pandas as pd
from datetime import date

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.dirname(BASE)
CYN, WIN = os.path.join(DATA, "Cynthia"), os.path.join(DATA, "Winston")
TRF_START = {"Cynthia": date(2026, 6, 25), "Winston": date(2026, 6, 20)}
NEEDED = ["Datetime", "Device_Number", "Task", "Battery_Voltage",
          "Light Sensor", "DoorOpen", "Servo_Feedback", "Error"]


def read_logs(folder, pattern, unit_fn):
    frames = []
    for f in sorted(glob.glob(os.path.join(folder, pattern))):
        try:
            d = pd.read_csv(f, dtype=str)
        except Exception:
            continue
        if "Datetime" not in d.columns or len(d) == 0:
            continue
        if not set(["DoorOpen", "Error"]).issubset(d.columns):
            continue  # FEED files (6-col) have no door/error signal
        d = d[[c for c in NEEDED if c in d.columns]].copy()
        d["unit"] = unit_fn(os.path.basename(f), d)
        frames.append(d)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def cyn_unit(fn, d):
    return "TUMBLY" + str(d["Device_Number"].dropna().iloc[0]).zfill(3)


def win_unit(fn, d):
    m = re.match(r"(Unit\d+)_", fn)
    return m.group(1) if m else "NA"


def tidy(raw, dataset):
    if raw.empty:
        return pd.DataFrame()
    dt = pd.to_datetime(raw["Datetime"], format="%m/%d/%Y %H:%M:%S", errors="coerce")
    df = pd.DataFrame({
        "dataset": dataset,
        "unit": raw["unit"],
        "datetime": dt,
        "task": raw["Task"],
        "battery_v": pd.to_numeric(raw["Battery_Voltage"], errors="coerce"),
        "light_sensor": raw["Light Sensor"],
        "door_open": pd.to_numeric(raw["DoorOpen"], errors="coerce").astype("Int64"),
        "servo_feedback": pd.to_numeric(raw["Servo_Feedback"], errors="coerce").astype("Int64"),
        "error": raw["Error"].astype(str).str.strip(),
    })
    df = df.dropna(subset=["datetime"]).reset_index(drop=True)
    df["date"] = df["datetime"].dt.date
    df["day_index"] = (pd.to_datetime(df["date"]) - pd.Timestamp(TRF_START[dataset])).dt.days
    df["time_of_day_h"] = (df["datetime"].dt.hour
                           + df["datetime"].dt.minute / 60
                           + df["datetime"].dt.second / 3600).round(4)
    df["is_error"] = (df["error"] != "OK")
    return df[["dataset", "unit", "datetime", "date", "day_index", "time_of_day_h",
               "task", "battery_v", "light_sensor", "door_open", "servo_feedback",
               "error", "is_error"]]


def door_transitions(events):
    """Extract every door open (0->1) and close (1->0) event per unit."""
    ev = events.sort_values(["dataset", "unit", "datetime"]).copy()
    ev["prev"] = ev.groupby(["dataset", "unit"])["door_open"].shift()
    ch = ev[(ev["door_open"].notna()) & (ev["prev"].notna())
            & (ev["door_open"] != ev["prev"])].copy()
    ch["transition"] = np.where(ch["door_open"] == 1, "open", "close")
    return ch[["dataset", "unit", "datetime", "date", "day_index",
               "time_of_day_h", "transition", "task"]].reset_index(drop=True)


def main():
    cyn = tidy(read_logs(CYN, "TUMBLY*.csv", cyn_unit), "Cynthia")
    win = tidy(read_logs(WIN, "Unit*.csv", win_unit), "Winston")
    events = pd.concat([cyn, win], ignore_index=True).sort_values(
        ["dataset", "unit", "datetime"]).reset_index(drop=True)
    events["dataset"] = events["dataset"].replace({"Cynthia": "Lab A", "Winston": "Lab B"})

    out = os.path.join(BASE, "device_events_long.csv.gz")
    events.to_csv(out, index=False, compression="gzip")
    mb = os.path.getsize(out) / 1e6

    trans = door_transitions(events)
    trans.to_csv(os.path.join(BASE, "door_transitions_long.csv"), index=False)
    print(f"door_transitions_long.csv  rows={len(trans):,}  "
          f"(open={int((trans.transition=='open').sum())}, "
          f"close={int((trans.transition=='close').sum())})")

    print(f"device_events_long.csv.gz  rows={len(events):,}  size={mb:.1f} MB")
    print("per dataset:\n", events.groupby("dataset").size())
    print("units:\n", events.groupby("dataset")["unit"].nunique())
    print("date span:\n", events.groupby("dataset")["date"].agg(["min", "max"]))
    print("NaT datetimes dropped? remaining NaT =", events["datetime"].isna().sum())
    return events


if __name__ == "__main__":
    main()

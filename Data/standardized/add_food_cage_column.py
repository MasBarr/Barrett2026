"""
add_food_cage_column.py  —  add cage-level food intake alongside the per-mouse value.

The standardized food table stores intake as `food_g_per_mouse_per_day` (cage total
divided by the number of mice in the cage). This adds two sibling columns so cage-level
analysis needs no re-derivation later:

  mice_in_cage             — animals sharing that cage's hopper
  food_g_per_cage_per_day  — food_g_per_mouse_per_day * mice_in_cage  (the raw cage total)

Lab A is single-housed, so mice_in_cage = 1 and per-cage == per-mouse there.
Lab B is group-housed by cage (E-J = 3 mice, K = 4), read from subjects.csv.

Reads the current standardized files from GitHub and rewrites food_intake_long.csv
in place next to this script. Re-run and re-push after any food data change.
"""
import os
import pandas as pd

BASE = "https://raw.githubusercontent.com/MasBarr/Barrett2026/main/Data/standardized"
HERE = os.path.dirname(os.path.abspath(__file__))

food = pd.read_csv(f"{BASE}/food_intake_long.csv")
subj = pd.read_csv(f"{BASE}/subjects.csv")

# mice per cage, per lab
lb_cage_n = subj[subj.dataset == "Lab B"].groupby(subj.subject_id.str[0]).size()   # 'E'..'K' -> count


def mice_in_cage(row):
    if row.dataset == "Lab A":
        return 1                                   # single-housed: one mouse per cage
    return int(lb_cage_n.get(row.subject_id))      # Lab B: food subject_id is the cage letter


food["mice_in_cage"] = food.apply(mice_in_cage, axis=1)
food["food_g_per_cage_per_day"] = food.food_g_per_mouse_per_day * food.mice_in_cage

# keep the new columns next to the per-mouse column
cols = list(food.columns)
cols.remove("mice_in_cage"); cols.remove("food_g_per_cage_per_day")
i = cols.index("food_g_per_mouse_per_day") + 1
cols[i:i] = ["mice_in_cage", "food_g_per_cage_per_day"]
food = food[cols]

out = os.path.join(HERE, "food_intake_long.csv")
food.to_csv(out, index=False)

print(f"wrote {out}")
print("columns:", list(food.columns))
for lab in ("Lab A", "Lab B"):
    d = food[food.dataset == lab]
    print(f"  {lab}: mice_in_cage {sorted(d.mice_in_cage.unique())}  "
          f"per-mouse {d.food_g_per_mouse_per_day.mean():.2f}  "
          f"per-cage {d.food_g_per_cage_per_day.mean():.2f} g/day")

import pandas as pd, numpy as np, glob, os, re
from pathlib import Path
from datetime import date, timedelta

BASE = Path(r"c:/Users/masba/OneDrive/Documents/Tumbly_paper/data")
OUT  = BASE/"standardized"; OUT.mkdir(exist_ok=True)
CYN, WIN = BASE/"Cynthia", BASE/"Winston"
TRF_START = {"Cynthia": date(2026,6,25), "Winston": date(2026,6,20)}

def didx(ds, d): return (d - TRF_START[ds]).days
def phase_to_diet(p):
    p=str(p).lower()
    if "trf" in p: return "TRF"
    if "adl" in p or p=="al": return "control"
    return np.nan

# ---------------- BODY WEIGHT / FOOD (Cynthia timelines) ----------------
def cyn_timeline(fn, valcol):
    df=pd.read_csv(fn)
    mice=[c for c in df.columns if c not in ("Phase","Date")]
    df["Date"]=pd.to_datetime(df["Date"]).dt.date
    long=df.melt(id_vars=["Phase","Date"], value_vars=mice,
                 var_name="subject_id", value_name=valcol).dropna(subset=[valcol])
    long["dataset"]="Cynthia"; long["subject_type"]="mouse"; long["design"]="within"
    long["phase"]=long["Phase"].replace({"starting weight":"baseline","transition day":"transition"})
    long["diet"]=long["phase"].map(phase_to_diet)
    long["date"]=long["Date"]; long["day_index"]=[didx("Cynthia",d) for d in long["Date"]]
    return long[["dataset","subject_id","subject_type","diet","design","phase","date","day_index",valcol]]

def read_below_header(fn, marker):
    raw=pd.read_csv(fn, header=None, dtype=str, skip_blank_lines=False)
    hdr=raw.index[raw[0].astype(str).str.strip()==marker][0]
    df=raw.iloc[hdr+1:].copy()
    df.columns=[str(c).strip() for c in raw.iloc[hdr].tolist()]
    return df.reset_index(drop=True)

def win_bw(fn):
    df=read_below_header(fn, "Cage #")
    df=df.rename(columns={df.columns[0]:"Cage#",df.columns[1]:"Mouse",df.columns[2]:"Cond"})
    df["Cage#"]=df["Cage#"].ffill()
    datecols=[c for c in df.columns if re.match(r"\d{4}-\d{2}-\d{2}",str(c))]
    long=df.melt(id_vars=["Cage#","Mouse","Cond"], value_vars=datecols,
                 var_name="date", value_name="body_weight_g")
    long["body_weight_g"]=pd.to_numeric(long["body_weight_g"],errors="coerce")
    long=long.dropna(subset=["body_weight_g","Mouse"])
    long["dataset"]="Winston"; long["subject_type"]="mouse"; long["design"]="between"
    long["subject_id"]=long["Mouse"]
    long["phase"]=long["Cond"].apply(lambda s:"TRF" if "TRF" in str(s) else "AL")
    long["diet"]=long["phase"].map(lambda p:"TRF" if p=="TRF" else "control")
    long["date"]=pd.to_datetime(long["date"]).dt.date
    long["day_index"]=[didx("Winston",d) for d in long["date"]]
    return long[["dataset","subject_id","subject_type","diet","design","phase","date","day_index","body_weight_g"]]

CAGE_MAP={"TRF_1":"E","TRF_2":"F","TRF_3":"I","TRF_4":"J","AL_1":"G","AL_2":"H","AL_3":"K"}
def win_food(fn):
    df=pd.read_csv(fn)
    val=[c for c in df.columns if c!="Day"]
    long=df.melt(id_vars=["Day"],value_vars=val,var_name="col",value_name="food_g_per_mouse_per_day").dropna()
    long["dataset"]="Winston"; long["subject_type"]="cage"; long["design"]="between"
    long["subject_id"]=long["col"].map(CAGE_MAP)
    long["phase"]=long["col"].str.startswith("TRF").map({True:"TRF",False:"AL"})
    long["diet"]=long["phase"].map(lambda p:"TRF" if p=="TRF" else "control")
    long["day_index"]=long["Day"].astype(int)
    long["date"]=[TRF_START["Winston"]+timedelta(days=int(x)) for x in long["day_index"]]
    return long[["dataset","subject_id","subject_type","diet","design","phase","date","day_index","food_g_per_mouse_per_day"]]

bw = pd.concat([cyn_timeline(CYN/"E4_D-TRF_single-housed_updated__Weight_timeline.csv","body_weight_g"),
                win_bw(WIN/"Temp_File_Kravtiz_Lab_CohM2_1wk_Mice_Data_Share__Copy_of_Body_Weights.csv")],
               ignore_index=True)
food = pd.concat([cyn_timeline(CYN/"E4_D-TRF_single-housed_updated__Food_timeline.csv","food_g_per_mouse_per_day"),
                  win_food(WIN/"Winston_Li_TRF_Pre-Injury_CohM2_Isocaloric_Feeding__Preinjury_CohM2.csv")],
                 ignore_index=True)

# ---------------- SUBJECTS ----------------
cyn_subj=pd.DataFrame({"subject_id":["1316","1338","1339","1340","1341","1342"]})
cyn_subj=cyn_subj.assign(dataset="Cynthia",subject_type="mouse",diet="within (ADL+TRF)",design="within",
    sex="Male",strain_background="human APOE4 knock-in",age="~8 months",cage=np.nan,tumbly_unit=np.nan,
    future_condition=np.nan,notes="single-housed; each mouse measured under ADL then TRF")
wfn=WIN/"Temp_File_Kravtiz_Lab_CohM2_1wk_Mice_Data_Share__Copy_of_Body_Weights.csv"
wdf=read_below_header(wfn, "Cage #")
wdf=wdf.rename(columns={wdf.columns[0]:"Cage#",wdf.columns[1]:"Mouse",wdf.columns[2]:"Cond"})
wdf["Cage#"]=wdf["Cage#"].ffill()
wdf=wdf.dropna(subset=["Mouse"])
win_subj=pd.DataFrame({"subject_id":wdf["Mouse"].values,
    "cage":wdf["Cage#"].astype(str).str.replace(".0","",regex=False).values,
    "future_condition":wdf["Cond"].values})
win_subj=win_subj.assign(dataset="Winston",subject_type="mouse",
    diet=[("TRF" if "TRF" in str(s) else "control") for s in wdf["Cond"].values],
    design="between",sex="Male",strain_background="C57BL/6J",age="~7-8 weeks",tumbly_unit=np.nan,
    notes="group-housed by cage; pre-injury (no injury applied in this dataset)")
cols=["dataset","subject_id","subject_type","diet","design","sex","strain_background","age","cage","tumbly_unit","future_condition","notes"]
subjects=pd.concat([cyn_subj[cols],win_subj[cols]],ignore_index=True)

# ---------------- DEVICE SUMMARY ----------------
def load_logs(folder, pattern, unit_from):
    frames=[]
    for f in glob.glob(str(folder/pattern)):
        try: d=pd.read_csv(f,dtype=str)
        except Exception: continue
        if "Datetime" not in d.columns or len(d)==0: continue
        d["unit"]=unit_from(os.path.basename(f), d)
        frames.append(d)
    return pd.concat(frames,ignore_index=True) if frames else pd.DataFrame()

def cyn_unit(fn,d):
    if "Device_Number" in d and d["Device_Number"].notna().any():
        return "TUMBLY"+str(d["Device_Number"].dropna().iloc[0]).zfill(3)
    return fn.split("_")[0]
def win_unit(fn,d):
    m=re.match(r"(Unit\d+)_",fn); return m.group(1) if m else "NA"

def summarize(logs, dataset):
    if logs.empty: return pd.DataFrame()
    logs["date"]=pd.to_datetime(logs["Datetime"].str.split().str[0],format="%m/%d/%Y",errors="coerce").dt.date
    logs["batt"]=pd.to_numeric(logs["Battery_Voltage"],errors="coerce")
    logs["door"]=pd.to_numeric(logs["DoorOpen"],errors="coerce")
    logs["is_err"]=(logs["Error"].astype(str).str.strip()!="OK")
    g=logs.groupby(["unit","date"])
    out=g.apply(lambda x:pd.Series({
        "n_samples":len(x),
        "mean_battery_v":round(x["batt"].mean(),3),
        "min_battery_v":round(x["batt"].min(),3),
        "pct_error":round(100*x["is_err"].mean(),3),
        "pct_door_open":round(100*x["door"].mean(),3),
        "n_timeddoor":int((x["Task"]=="TimedDoor").sum()),
        "n_freefeeding":int((x["Task"]=="FreeFeeding").sum()),
    }),include_groups=False).reset_index()
    out=out.dropna(subset=["date"])
    out.insert(0,"dataset",dataset)
    out["day_index"]=[didx(dataset,d) for d in out["date"]]
    return out

dev=pd.concat([
    summarize(load_logs(CYN,"TUMBLY*.csv",cyn_unit),"Cynthia"),
    summarize(load_logs(WIN,"Unit*.csv",win_unit),"Winston")
],ignore_index=True)

LAB={"Cynthia":"Lab A","Winston":"Lab B"}   # anonymized labels for the published dataset
for name,df in [("subjects",subjects),("body_weight_long",bw),("food_intake_long",food),("device_summary_long",dev)]:
    df["dataset"]=df["dataset"].replace(LAB)
    df.to_csv(OUT/(name+".csv"),index=False)
    print(name+".csv  rows="+str(len(df))+"  cols="+str(list(df.columns)))
print("\nSubjects:\n", subjects.groupby(["dataset","diet"]).size())
print("\nBW:\n", bw.groupby(["dataset","diet"]).size())
print("\nFood:\n", food.groupby(["dataset","diet"]).size())
print("\nDevice-days:\n", dev.groupby("dataset").agg(units=("unit","nunique"),rows=("unit","size")))

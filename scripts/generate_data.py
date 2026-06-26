"""
Synthetic MRI Operations Data Generator
----------------------------------------
Generates realistic synthetic data for the MRI Operations Intelligence Platform.
Distributions and correlations are informed by MRI scheduling research.

Tables produced:
    - procedures       : procedure reference data with template durations
    - scanners         : scanner inventory by site
    - patients         : anonymized patient pool (no PII)
    - staffing         : technologist shift schedule
    - calendar_events  : holidays and maintenance windows
    - appointments     : scheduled exams (scheduled start/end, assigned scanner)
    - actual_exam_logs : actual exam execution (actual start/end, delay reasons)

Run:
    python scripts/generate_data.py
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from faker import Faker

# ── Reproducibility ──────────────────────────────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

# ── Config ───────────────────────────────────────────────────────────────────
OUTPUT_DIR = "data/synthetic"
START_DATE = datetime(2023, 1, 1)
END_DATE   = datetime(2024, 12, 31)
N_PATIENTS = 2000

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── 1. PROCEDURES ─────────────────────────────────────────────────────────────
PROCEDURES = [
    ("MRI-BRAIN",   "Brain MRI",                        45,  False, "medium"),
    ("MRI-BRAIN-C", "Brain MRI with Contrast",          60,  True,  "medium"),
    ("MRI-SPINE-C", "Cervical Spine MRI",               50,  False, "medium"),
    ("MRI-SPINE-T", "Thoracic Spine MRI",               50,  False, "medium"),
    ("MRI-SPINE-L", "Lumbar Spine MRI",                 50,  False, "medium"),
    ("MRI-KNEE",    "Knee MRI",                         40,  False, "low"),
    ("MRI-SHOULDER","Shoulder MRI",                     40,  False, "low"),
    ("MRI-HIP",     "Hip MRI",                          45,  False, "low"),
    ("MRI-ABDOMEN", "Abdomen MRI",                      60,  True,  "high"),
    ("MRI-PELVIS",  "Pelvis MRI",                       55,  True,  "high"),
    ("MRI-CARDIAC", "Cardiac MRI",                      75,  True,  "high"),
    ("MRI-BREAST",  "Breast MRI",                       60,  True,  "high"),
    ("MRI-PROSTATE","Prostate MRI",                     70,  True,  "high"),
    ("MRI-FETAL",   "Fetal MRI",                        60,  False, "high"),
    ("MRI-WRIST",   "Wrist MRI",                        35,  False, "low"),
    ("MRI-ANKLE",   "Ankle MRI",                        35,  False, "low"),
    ("MRI-NEURO-F", "Neuro Functional MRI",             90,  False, "high"),
    ("MRI-SPECTRO", "MR Spectroscopy",                  80,  False, "high"),
    ("MRI-ART",     "MR Arthrography",                  55,  True,  "medium"),
    ("MRI-ANGIO",   "MR Angiography",                   65,  True,  "medium"),
]

procedures_df = pd.DataFrame(PROCEDURES, columns=[
    "procedure_code", "procedure_name", "template_duration_min",
    "contrast_required", "complexity"
])
procedures_df["procedure_id"] = range(1, len(procedures_df) + 1)

complexity_std = {"low": 0.10, "medium": 0.18, "high": 0.28}
procedures_df["duration_std_pct"] = procedures_df["complexity"].map(complexity_std)

# ── 2. SCANNERS ───────────────────────────────────────────────────────────────
SCANNERS = [
    ("SC01", "Main",    "3.0T", "active", False),
    ("SC02", "Main",    "1.5T", "active", False),
    ("SC03", "Main",    "3.0T", "active", True),
    ("SC04", "North",   "1.5T", "active", False),
    ("SC05", "North",   "3.0T", "active", False),
    ("SC06", "South",   "1.5T", "active", True),
    ("SC07", "South",   "3.0T", "active", False),
    ("SC08", "Main",    "1.5T", "active", False),
]

scanners_df = pd.DataFrame(SCANNERS, columns=[
    "scanner_id", "site", "field_strength", "status", "open_bore"
])

scanner_delay_bias = {
    "SC01": 2, "SC02": 0, "SC03": -2, "SC04": 3,
    "SC05": 1, "SC06": 0, "SC07": 4,  "SC08": -1,
}
scanners_df["delay_bias_min"] = scanners_df["scanner_id"].map(scanner_delay_bias)

# ── 3. PATIENTS ───────────────────────────────────────────────────────────────
AGE_GROUPS = ["18-30", "31-45", "46-60", "61-75", "75+"]
AGE_GROUP_WEIGHTS = [0.12, 0.22, 0.28, 0.25, 0.13]

patients_df = pd.DataFrame({
    "patient_id":    [f"PT{str(i).zfill(5)}" for i in range(1, N_PATIENTS + 1)],
    "age_group":     np.random.choice(AGE_GROUPS, size=N_PATIENTS, p=AGE_GROUP_WEIGHTS),
    "has_implant":   np.random.choice([True, False], size=N_PATIENTS, p=[0.08, 0.92]),
    "is_pediatric":  np.random.choice([True, False], size=N_PATIENTS, p=[0.05, 0.95]),
    "claustrophobic":np.random.choice([True, False], size=N_PATIENTS, p=[0.12, 0.88]),
})

# ── 4. STAFFING ───────────────────────────────────────────────────────────────
shifts = []
current = START_DATE
while current <= END_DATE:
    if current.weekday() < 5:
        for scanner in scanners_df["scanner_id"]:
            for shift, start_h, end_h in [("AM", 7, 15), ("PM", 13, 21)]:
                shifts.append({
                    "date":           current.date(),
                    "scanner_id":     scanner,
                    "shift":          shift,
                    "shift_start":    current.replace(hour=start_h, minute=0),
                    "shift_end":      current.replace(hour=end_h,   minute=0),
                    "technologist_id":f"TECH{random.randint(1, 20):02d}",
                })
    current += timedelta(days=1)

staffing_df = pd.DataFrame(shifts)

# ── 5. CALENDAR EVENTS ────────────────────────────────────────────────────────
HOLIDAYS_2023 = ["2023-01-02","2023-01-16","2023-02-20","2023-05-29",
                 "2023-07-04","2023-09-04","2023-11-23","2023-12-25"]
HOLIDAYS_2024 = ["2024-01-01","2024-01-15","2024-02-19","2024-05-27",
                 "2024-07-04","2024-09-02","2024-11-28","2024-12-25"]

calendar_events = []
for h in HOLIDAYS_2023 + HOLIDAYS_2024:
    calendar_events.append({
        "date": h, "event_type": "holiday",
        "description": "Federal Holiday", "affects_scheduling": True
    })

for scanner in scanners_df["scanner_id"]:
    for quarter_start in ["2023-01-01","2023-04-01","2023-07-01","2023-10-01",
                          "2024-01-01","2024-04-01","2024-07-01","2024-10-01"]:
        maint_date = pd.Timestamp(quarter_start) + timedelta(days=random.randint(5, 80))
        calendar_events.append({
            "date": str(maint_date.date()), "event_type": "maintenance",
            "description": f"Scheduled maintenance - {scanner}",
            "affects_scheduling": True, "scanner_id": scanner,
        })

calendar_df = pd.DataFrame(calendar_events)
holiday_dates = set(HOLIDAYS_2023 + HOLIDAYS_2024)

# ── 6. APPOINTMENTS + ACTUAL EXAM LOGS ───────────────────────────────────────
DELAY_REASONS = [
    "patient_late", "prior_exam_overrun", "equipment_issue",
    "contrast_reaction", "patient_prep_incomplete", "technologist_handoff",
    "emergency_add_on", "no_show",
    "on_time", "on_time", "on_time", "on_time", "on_time",
]

PROC_WEIGHTS = [3,2,3,2,3,4,3,2,1,1,1,1,1,1,2,2,1,1,1,1]

appointments = []
actual_logs  = []
apt_id = 1

current = START_DATE
while current <= END_DATE:
    if current.weekday() >= 5 or str(current.date()) in holiday_dates:
        current += timedelta(days=1)
        continue

    for _, scanner in scanners_df.iterrows():
        slot_time        = current.replace(hour=7,  minute=0, second=0)
        day_end          = current.replace(hour=19, minute=0, second=0)
        cumulative_delay = 0

        while slot_time < day_end:
            if random.random() > 0.85:
                slot_time += timedelta(minutes=15)
                continue

            proc         = procedures_df.sample(1, weights=PROC_WEIGHTS).iloc[0]
            template_min = proc["template_duration_min"]
            sched_start  = slot_time
            sched_end    = slot_time + timedelta(minutes=int(template_min))

            if sched_end > day_end:
                break

            patient = patients_df.sample(1).iloc[0]

            # Actual duration with realistic modifiers
            std_min         = template_min * proc["duration_std_pct"]
            actual_duration = max(10, np.random.normal(template_min, std_min))

            if proc["contrast_required"]:
                actual_duration += np.random.normal(5, 2)
            if patient["claustrophobic"]:
                actual_duration += np.random.normal(8, 3)
            if patient["age_group"] == "75+":
                actual_duration += np.random.normal(4, 2)
            if patient["is_pediatric"]:
                actual_duration += np.random.normal(10, 4)
            if slot_time.hour >= 15:
                actual_duration += np.random.normal(3, 1.5)

            actual_duration += scanner["delay_bias_min"]
            actual_duration  = max(10, round(actual_duration, 1))

            # Start delay
            delay_reason = random.choice(DELAY_REASONS)
            start_delay  = 0

            if delay_reason == "patient_late":
                start_delay = np.random.normal(12, 5)
            elif delay_reason == "prior_exam_overrun":
                start_delay = cumulative_delay * 0.8
            elif delay_reason == "equipment_issue":
                start_delay = np.random.normal(20, 8)
            elif delay_reason == "technologist_handoff":
                start_delay = np.random.normal(8, 3)
            elif delay_reason == "emergency_add_on":
                start_delay = np.random.normal(25, 10)
            elif delay_reason == "no_show":
                slot_time = sched_end
                apt_id += 1
                continue

            start_delay  = max(0, round(start_delay, 1))
            actual_start = sched_start + timedelta(minutes=start_delay)
            actual_end   = actual_start + timedelta(minutes=actual_duration)

            actual_slot_used = (actual_end - sched_start).total_seconds() / 60
            cumulative_delay = max(0, actual_slot_used - template_min)

            end_delta = (actual_end - sched_end).total_seconds() / 60
            adherent  = abs(end_delta) <= 10

            appointment_id = f"APT{str(apt_id).zfill(6)}"

            appointments.append({
                "appointment_id":        appointment_id,
                "patient_id":            patient["patient_id"],
                "procedure_code":        proc["procedure_code"],
                "scanner_id":            scanner["scanner_id"],
                "site":                  scanner["site"],
                "scheduled_start":       sched_start,
                "scheduled_end":         sched_end,
                "template_duration_min": template_min,
                "day_of_week":           current.strftime("%A"),
                "hour_of_day":           slot_time.hour,
                "is_contrast":           proc["contrast_required"],
                "complexity":            proc["complexity"],
            })

            actual_logs.append({
                "log_id":               f"LOG{str(apt_id).zfill(6)}",
                "appointment_id":        appointment_id,
                "actual_start":          actual_start,
                "actual_end":            actual_end,
                "actual_duration_min":   round(actual_duration, 1),
                "start_delay_min":       round(start_delay, 1),
                "end_delta_min":         round(end_delta, 1),
                "adherent":              adherent,
                "delay_reason":          delay_reason if start_delay > 2 else "on_time",
                "technologist_id":       f"TECH{random.randint(1, 20):02d}",
            })

            slot_time = sched_end
            apt_id += 1

    current += timedelta(days=1)

appointments_df = pd.DataFrame(appointments)
actual_logs_df  = pd.DataFrame(actual_logs)

# ── 7. SAVE ───────────────────────────────────────────────────────────────────
def save(df, name):
    path = f"{OUTPUT_DIR}/{name}.csv"
    df.to_csv(path, index=False)
    print(f"  {name:30s} {len(df):>7,} rows  ->  {path}")

print("\nGenerating synthetic MRI operations dataset...")
print(f"  Date range : {START_DATE.date()} to {END_DATE.date()}")
print(f"  Scanners   : {len(scanners_df)}")
print(f"  Patients   : {len(patients_df)}")
print()

save(procedures_df,   "procedures")
save(scanners_df,     "scanners")
save(patients_df,     "patients")
save(staffing_df,     "staffing")
save(calendar_df,     "calendar_events")
save(appointments_df, "appointments")
save(actual_logs_df,  "actual_exam_logs")

print(f"\nDone. {len(appointments_df):,} appointments generated.")
print(f"Overall adherence rate : {actual_logs_df['adherent'].mean():.1%}")
print(f"Mean start delay       : {actual_logs_df['start_delay_min'].mean():.1f} min")
print(f"Mean actual duration   : {actual_logs_df['actual_duration_min'].mean():.1f} min")
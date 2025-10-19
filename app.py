# app.py
import json
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Miracles MAP App — MAP 1 (Scoring View)",
    page_icon="🧭",
    layout="wide",
)

# ─────────────────────────────────────────────────────────────
# STYLING — compact one-line headers
# ─────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2.0rem;}
h1, h2, h3, h4 { font-weight: 800; color: #1a1a1a; }

/* table header bar */
.table-header {
  background:#1E4878; 
  color:#fff; 
  padding:8px 6px; 
  font-weight:700; 
  border-radius:6px;
  font-size:0.8rem;          /* smaller text */
  white-space:nowrap;        /* prevent wrapping */
  text-align:center;
}

/* level left label bar */
.level-bar {
  background:#eaf2ff; 
  color:#0d47a1; 
  font-weight:700; 
  font-size:0.9rem; 
  padding:6px 10px; 
  border:1px solid #cfe0ff; 
  border-radius:6px;
}

/* input boxes */
input[type="text"] {
  background:#f5f6f8; 
  border:1px solid #ced4da; 
  border-radius:8px;
  height:36px; 
  width:100%; 
  text-align:center; 
  font-size:0.9rem; 
  color:#333;
}

/* total footer */
.total-bar {
  background:#1E4878; 
  color:#fff; 
  font-weight:700; 
  padding:6px 10px; 
  border-radius:6px;
  font-size:0.9rem;
  text-align:center;
}

/* compact column padding */
[data-testid="column"] {padding-left:0.25rem; padding-right:0.25rem;}
</style>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────
SEGMENTS = [
    "HDB",
    "Private Resale",
    "Landed",
    "New Launch",
    "Top Projects",
    "Referral",
    "Indus/Comm",
    "Social Media",
]

LEVELS = [
    "Interest",
    "Knowledge",
    "Confidence",
    "Market",
    "Investment",
    "Commitment",
    "Support",
    "Income",
    "Willingness",
]

DATA_PATH = Path("data_store.json")

# ─────────────────────────────────────────────────────────────
# DATA STORAGE
# ─────────────────────────────────────────────────────────────
@st.cache_resource
def _init_store() -> dict:
    if DATA_PATH.exists():
        try:
            return json.loads(DATA_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_store(store: dict) -> None:
    DATA_PATH.write_text(json.dumps(store, indent=2), encoding="utf-8")

STORE = _init_store()

def empty_scores_dict():
    return {lvl: {seg: "" for seg in SEGMENTS} for lvl in LEVELS}

# ─────────────────────────────────────────────────────────────
# VALIDATION HELPERS
# ─────────────────────────────────────────────────────────────
def sanitize_cell(v: str) -> str:
    v = (v or "").strip()
    if not v.isdigit():
        return ""
    n = int(v)
    return str(n) if 1 <= n <= 8 else ""

def validate_row_unique(row_vals: dict) -> dict:
    seen = set()
    out = {}
    for seg, v in row_vals.items():
        vv = sanitize_cell(v)
        if vv and vv in seen:
            out[seg] = ""
        else:
            out[seg] = vv
            if vv:
                seen.add(vv)
    return out

def compute_totals(scores: dict) -> dict:
    totals = {seg: 0 for seg in SEGMENTS}
    for lvl in LEVELS:
        for seg in SEGMENTS:
            v = scores[lvl][seg]
            if v:
                totals[seg] += int(v)
    return totals

# ─────────────────────────────────────────────────────────────
# ASSOCIATE SELECTOR
# ─────────────────────────────────────────────────────────────
st.title("🧭 Miracles MAP App — MAP 1 (Scoring View)")

associate_names = sorted(STORE.keys())
sel_cols = st.columns([2, 3, 3, 2])
with sel_cols[0]:
    mode = st.selectbox("Mode", ["Select associate", "New associate"], index=1 if not associate_names else 0)
with sel_cols[1]:
    selected_name = st.selectbox(
        "Existing",
        ["—"] + associate_names,
        index=0 if mode == "New associate" or not associate_names else 1,
        disabled=(mode != "Select associate"),
    )
with sel_cols[2]:
    entered_name = st.text_input("Associate name", value="", placeholder="Full name")
with sel_cols[3]:
    load_btn = st.button("Load / Start")

current_key = None
if mode == "Select associate" and selected_name != "—" and load_btn:
    current_key = selected_name
elif mode == "New associate" and entered_name.strip() and load_btn:
    current_key = entered_name.strip()

if "current_key" not in st.session_state and current_key:
    st.session_state["current_key"] = current_key
elif current_key:
    st.session_state["current_key"] = current_key

if "current_key" not in st.session_state:
    st.info("Select an existing associate or choose **New associate** to begin.")
    st.stop()

current_key = st.session_state["current_key"]

if current_key not in STORE:
    STORE[current_key] = {
        "profile": {"name": current_key, "mobile": "", "email": "", "manager": ""},
        "scores": empty_scores_dict(),
    }
    save_store(STORE)

profile = STORE[current_key]["profile"]
scores = STORE[current_key]["scores"]

# ─────────────────────────────────────────────────────────────
# PROFILE + PIE CHART
# ─────────────────────────────────────────────────────────────
t1, t2 = st.columns([1.1, 1])
with t1:
    st.subheader("Associate Details")
    c1, c2 = st.columns(2)
    with c1:
        profile["name"] = st.text_input("Name", value=profile.get("name", ""))
        profile["mobile"] = st.text_input("Mobile", value=profile.get("mobile", ""))
    with c2:
        profile["email"] = st.text_input("Email", value=profile.get("email", ""))
        profile["manager"] = st.text_input("Manager", value=profile.get("manager", ""))

with t2:
    st.subheader("FOCUS SEGMENTATION")
    totals_preview = compute_totals(scores)
    if sum(totals_preview.values()) > 0:
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(
            list(totals_preview.values()),
            labels=SEGMENTS,
            autopct="%1.0f%%",
            startangle=90,
        )
        ax.axis("equal")
        st.pyplot(fig)
    else:
        st.caption("Totals will appear here once you enter scores.")

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# HEADER BAR
# ─────────────────────────────────────────────────────────────
hdr = st.columns([1.2] + [1] * 8)
with hdr[0]:
    st.markdown('<div class="table-header">Level</div>', unsafe_allow_html=True)
for i, seg in enumerate(SEGMENTS, start=1):
    with hdr[i]:
        st.markdown(f'<div class="table-header">{seg}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# GRID INPUT (LEVELS)
# ─────────────────────────────────────────────────────────────
for lvl in LEVELS:
    bar_cols = st.columns([1.2, 8])
    with bar_cols[0]:
        st.markdown(f'<div class="level-bar">{lvl}</div>', unsafe_allow_html=True)
    with bar_cols[1]:
        st.markdown('<div class="row-band"></div>', unsafe_allow_html=True)

    row_cols = st.columns([1.2] + [1] * 8)
    with row_cols[0]:
        st.write("")
    new_row_vals = {}
    for i, seg in enumerate(SEGMENTS, start=1):
        with row_cols[i]:
            key = f"cell::{current_key}::{lvl}::{seg}"
            default = scores[lvl][seg]
            v = st.text_input(" ", value=default, key=key, label_visibility="collapsed", max_chars=1)
            new_row_vals[seg] = v
    scores[lvl] = validate_row_unique(new_row_vals)

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# TOTAL ROW
# ─────────────────────────────────────────────────────────────
totals = compute_totals(scores)
ft = st.columns([1.2] + [1] * 8)
with ft[0]:
    st.markdown('<div class="total-bar">TOTAL</div>', unsafe_allow_html=True)
for i, seg in enumerate(SEGMENTS, start=1):
    with ft[i]:
        st.markdown(f'<div class="total-bar">{totals[seg]}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# SAVE / EXPORT
# ─────────────────────────────────────────────────────────────
a, b, c = st.columns([1, 1, 2])
with a:
    if st.button("💾 Save / Update"):
        STORE[current_key]["profile"] = profile
        STORE[current_key]["scores"] = scores
        save_store(STORE)
        st.success("Saved successfully.")

with b:
    if st.button("🗂 View saved associates"):
        if not STORE:
            st.info("No records yet.")
        else:
            df = []
            for k, rec in STORE.items():
                df.append(
                    {
                        "Associate": rec["profile"].get("name", k),
                        "Mobile": rec["profile"].get("mobile", ""),
                        "Email": rec["profile"].get("email", ""),
                        "Manager": rec["profile"].get("manager", ""),
                    }
                )
            st.dataframe(pd.DataFrame(df), use_container_width=True)

with c:
    full_map = {"profile": profile, "scores": scores, "totals": totals}
    st.download_button(
        "⬇️ Export mapping (JSON)",
        data=json.dumps(full_map, indent=2).encode("utf-8"),
        file_name=f"{current_key.replace(' ','_')}_map1.json",
        mime="application/json",
    )
    totals_df = pd.DataFrame([{"Segment": seg, "Total": val} for seg, val in totals.items()])
    st.download_button(
        "⬇️ Export totals (CSV)",
        data=totals_df.to_csv(index=False).encode("utf-8"),
        file_name=f"{current_key.replace(' ','_')}_totals.csv",
        mime="text/csv",
    )

# ─────────────────────────────────────────────────────────────
# FOOTER INSTRUCTIONS
# ─────────────────────────────────────────────────────────────
st.markdown("---")
left, right = st.columns([1.2, 1])
with left:
    st.subheader("Levels")
    st.markdown(
        """
- **Interest** — Measure the level of interest you have for the segment  
- **Knowledge** — Measure the level of knowledge you have for the segment  
- **Confidence** — Measure the level of confidence you have for the segment  
- **Market** — Measure the current market potential for the segment  
- **Investment** — Measure the level of investment you are willing to invest for the segment  
- **Commitment** — Measure the level of time you are willing to commit for the segment  
- **Support** — Measure the level of perceived support you can receive for the segment  
- **Income** — Measure the level of perceived income you can receive for the segment  
- **Willingness** — Measure the level of willingness you have for the segment
"""
    )

with right:
    st.subheader("Instructions")
    st.markdown(
        """
1) Start from each level of measurement and rate them across the Segments  
2) Rate each Segment using a scale **1 to 8**, **1 = lowest**, **8 = highest**  
3) Complete the mapping based on your own analysis  
4) Try to complete within **10 minutes**  
5) The mapping should be done in the presence of a **District Head**
"""
    )

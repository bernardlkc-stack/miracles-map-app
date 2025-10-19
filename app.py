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
    page_title="Miracles MAP App — MAP 1 & 2",
    page_icon="🧭",
    layout="wide",
)

# ─────────────────────────────────────────────────────────────
# STYLING
# ─────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2.0rem;}
h1, h2, h3, h4 { font-weight: 800; color: #1a1a1a; }
.table-header {
  background:#1E4878; color:#fff; padding:8px 6px; font-weight:700;
  border-radius:6px; font-size:0.8rem; white-space:nowrap; text-align:center;
}
.level-bar {
  background:#eaf2ff; color:#0d47a1; font-weight:700; font-size:0.9rem;
  padding:6px 10px; border:1px solid #cfe0ff; border-radius:6px; text-align:center;
}
input[type="text"] {
  background:#f5f6f8; border:1px solid #ced4da; border-radius:8px;
  height:36px; width:100%; text-align:center; font-size:0.9rem; color:#333;
}
.total-bar {
  background:#1E4878; color:#fff; font-weight:700; padding:6px 10px;
  border-radius:6px; font-size:0.9rem; text-align:center;
}
[data-testid="column"] {padding-left:0.25rem; padding-right:0.25rem;}
</style>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────
SEGMENTS = [
    "HDB","Private Resale","Landed","New Launch",
    "Top Projects","Referral","Indus/Comm","Social Media",
]
LEVELS = [
    "Interest","Knowledge","Confidence","Market",
    "Investment","Commitment","Support","Income","Willingness",
]
DATA_PATH = Path("data_store.json")

# ─────────────────────────────────────────────────────────────
# ACTIVITY RECOMMENDATIONS (MAP 2)
# ─────────────────────────────────────────────────────────────
ACTIVITIES = {
    "HDB": [
        "HiP - Friday Business Insights",
        "HiP - HDB Module 1 and 2",
        "XCEL - Mastering Timeline and Financial Calculation",
        "XCEL - GTA Set Up",
        "SWAT - The BIG 3 in HDB",
        "SWAT - HDB Mastery by Strategic Flow",
        "SWAT - How to assess your seller and get seller's listing",
        "SWAT - RTD Advisor App",
        "SWAT - Resale Timeline",
    ],
    "Private Resale": [
        "HiP - Friday Business Insights",
        "HiP - Huttons Analyzer Workshop",
        "HiP - Real Insights",
        "HiP - Comprehensive Strategies for Effective Marketing",
        "XCEL - GTA Set Up",
        "XCEL - Mastering Timeline and Financial Calculation",
        "SWAT - How to assess your seller and get seller's listing",
        "SWAT - RTD Advisor App",
        "SWAT - Resale Timeline",
    ],
    "Landed": [
        "HiP - Friday Business Insights",
        "HiP - Monthly Tech Overview",
        "HiP - Landed Analysis",
        "HiP - Huttons Analyzer Workshop",
        "XCEL - GTA Set Up",
        "XCEL - Mastering Timeline and Financial Calculation",
        "SWAT - Proven Methods to Win Over Landed Client",
        "SWAT - How to assess your seller and get seller's list",
    ],
    "New Launch": [
        "XCEL - New Launch: Project Swinging Techniques",
        "XCEL - New Launch: Essence of Serving a New Launch",
        "XCEL - Mastering Timeline and Financial Calculation",
        "XCEL - Mastering Google Adwords",
        "XCEL - Mastering Facebook Ads",
        "SWAT - Facebook Marketing (Basic & Advanced)",
        "SWAT - Learn how to create first landing page with SWAT",
    ],
    "Top Projects": [
        "HiP - Friday Business Insights",
        "HiP - Huttons Analyzer Workshop",
        "HiP - Real Insights",
        "XCEL - Mastering TOP Projects",
        "XCEL - GTA Set Up",
        "SWAT - TOP Rental and Resale",
        "SWAT - How to assess your seller and get seller's listing",
        "SWAT - RTD Advisor App",
        "SWAT - Resale Timeline",
    ],
    "Referral": [
        "HiP - Friday Business Insights",
        "XCEL - CRM: Organise Your Way to Better Sales",
        "Register ConnectPro with Bernard Lau",
        "Create Digital Namecard",
        "Referral System 1: Engaging Your Clients",
        "Referral System 2: Working with Connectors",
        "Referral System 3: Unlimited Prospecting using Digital",
        "SWAT - Referral Based System - Zero Marketing Cost",
        "SWAT - Absolute Script",
    ],
    "Indus/Comm": [
        "HiP - Friday Business Insights",
        "HiP - Huttons Analyzer Workshop",
        "XCEL - Mastering Timeline and Financial Calculation",
        "XCEL - GTA Set Up",
        "SWAT - Commercial Expo: Giving U the Extra Edge",
        "SWAT - RTD Advisor App",
        "SWAT - How to assess your seller and get seller's listing",
        "SWAT - Resale Timeline",
    ],
    "Social Media": [
        "HiP - Friday Business Insights",
        "HiP - Generate More Leads",
        "XCEL - Power Script to Wow Your Clients",
        "XCEL - Mastering Google Adwords",
        "XCEL - Mastering Facebook Ads",
        "XCEL - CRM: Organise Your Way to Better Sales",
        "SWAT - Facebook Marketing (Basic)",
        "SWAT - Facebook Marketing (Advanced)",
        "SWAT - Facebook Marketing Webinar",
    ],
}
SEGMENT_COLORS = {
    "HDB": "#1E4878","Private Resale": "#C65D00","Landed": "#B5B5B5",
    "New Launch": "#D9A600","Top Projects": "#2E6BAA",
    "Referral": "#2F8B47","Indus/Comm": "#5B5B5B","Social Media": "#6E4A4A",
}

# ─────────────────────────────────────────────────────────────
# DATA HANDLING
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
# VALIDATION
# ─────────────────────────────────────────────────────────────
def sanitize_cell(v: str) -> str:
    v = (v or "").strip()
    if not v.isdigit(): return ""
    n = int(v)
    return str(n) if 1 <= n <= 8 else ""

def validate_row_unique(row_vals: dict) -> dict:
    seen=set(); out={}
    for seg,v in row_vals.items():
        vv=sanitize_cell(v)
        if vv and vv in seen: out[seg]=""
        else:
            out[seg]=vv
            if vv: seen.add(vv)
    return out

def compute_totals(scores: dict) -> dict:
    totals={seg:0 for seg in SEGMENTS}
    for lvl in LEVELS:
        for seg in SEGMENTS:
            v=scores[lvl][seg]
            if v: totals[seg]+=int(v)
    return totals

# ─────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────
st.title("🧭 Miracles MAP App — MAP 1 + MAP 2")

associate_names=sorted(STORE.keys())
sel_cols=st.columns([2,3,3,2])
with sel_cols[0]:
    mode=st.selectbox("Mode",["Select associate","New associate"],index=1 if not associate_names else 0)
with sel_cols[1]:
    selected_name=st.selectbox("Existing",["—"]+associate_names,
        index=0 if mode=="New associate" or not associate_names else 1,
        disabled=(mode!="Select associate"))
with sel_cols[2]:
    entered_name=st.text_input("Associate name",value="",placeholder="Full name")
with sel_cols[3]:
    load_btn=st.button("Load / Start")

current_key=None
if mode=="Select associate" and selected_name!="—" and load_btn:
    current_key=selected_name
elif mode=="New associate" and entered_name.strip() and load_btn:
    current_key=entered_name.strip()

if "current_key" not in st.session_state and current_key:
    st.session_state["current_key"]=current_key
elif current_key:
    st.session_state["current_key"]=current_key

if "current_key" not in st.session_state:
    st.info("Select an existing associate or choose **New associate** to begin.")
    st.stop()

current_key=st.session_state["current_key"]
if current_key not in STORE:
    STORE[current_key]={"profile":{"name":current_key,"mobile":"","email":"","manager":""},"scores":empty_scores_dict()}
    save_store(STORE)

profile=STORE[current_key]["profile"]
scores=STORE[current_key]["scores"]

# ─────────────────────────────────────────────────────────────
# PROFILE + PIE CHART
# ─────────────────────────────────────────────────────────────
t1,t2=st.columns([1.1,1])
with t1:
    st.subheader("Associate Details")
    c1,c2=st.columns(2)
    with c1:
        profile["name"]=st.text_input("Name",value=profile.get("name",""))
        profile["mobile"]=st.text_input("Mobile",value=profile.get("mobile",""))
    with c2:
        profile["email"]=st.text_input("Email",value=profile.get("email",""))
        profile["manager"]=st.text_input("Manager",value=profile.get("manager",""))

with t2:
    st.subheader("FOCUS SEGMENTATION")
    totals_preview=compute_totals(scores)
    if sum(totals_preview.values())>0:
        fig,ax=plt.subplots(figsize=(4,4))
        ax.pie(list(totals_preview.values()),labels=SEGMENTS,autopct="%1.0f%%",startangle=90)
        ax.axis("equal")
        st.pyplot(fig)
    else:
        st.caption("Totals will appear here once you enter scores.")

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# MAP 1 GRID
# ─────────────────────────────────────────────────────────────
hdr=st.columns([1.2]+[1]*8)
with hdr[0]: st.markdown('<div class="table-header">Level</div>',unsafe_allow_html=True)
for i,seg in enumerate(SEGMENTS,start=1):
    with hdr[i]: st.markdown(f'<div class="table-header">{seg}</div>',unsafe_allow_html=True)

for lvl in LEVELS:
    row_cols=st.columns([1.2]+[1]*8)
    with row_cols[0]:
        st.markdown(f'<div class="level-bar">{lvl}</div>',unsafe_allow_html=True)
    new_row_vals={}
    for i,seg in enumerate(SEGMENTS,start=1):
        with row_cols[i]:
            key=f"cell::{current_key}::{lvl}::{seg}"
            default=scores[lvl][seg]
            v=st.text_input(" ",value=default,key=key,label_visibility="collapsed",max_chars=1,placeholder=" ")
            new_row_vals[seg]=v
    scores[lvl]=validate_row_unique(new_row_vals)

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# TOTALS
# ─────────────────────────────────────────────────────────────
totals=compute_totals(scores)
ft=st.columns([1.2]+[1]*8)
with ft[0]: st.markdown('<div class="total-bar">TOTAL</div>',unsafe_allow_html=True)
for i,seg in enumerate(SEGMENTS,start=1):
    with ft[i]: st.markdown(f'<div class="total-bar">{totals[seg]}</div>',unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# MAP 2 — COLORED RECOMMENDATIONS
# ─────────────────────────────────────────────────────────────
st.markdown("## 🎯 MAP 2 — Recommended Activities for Your Top 3 Focus Segments")
totals_sorted=sorted(totals.items(),key=lambda x:x[1],reverse=True)
top3=[seg for seg,_ in totals_sorted[:3]]
if not any(totals.values()):
    st.info("Fill in your MAP 1 grid to view recommendations.")
else:
    st.write(f"Your **Top 3 Focus Segments** are: **{', '.join(top3)}**")
    cols=st.columns(3)
    for idx,seg in enumerate(top3):
        with cols[idx]:
            color=SEGMENT_COLORS.get(seg,"#333")
            st.markdown(
                f"""
                <div style="background:{color};color:white;padding:8px 10px;border-radius:5px;
                font-weight:700;text-align:center;">{seg.upper()}</div>
                <div style="border:1px solid #ccc;padding:10px;min-height:300px;">
                  <table style="width:100%;font-size:0.85rem;">
                    <tr><th align="left">Activities</th><th align="right">Done</th></tr>
                    {"".join([f"<tr><td>{act}</td><td align='right'>✓</td></tr>" for act in ACTIVITIES.get(seg,[])])}
                  </table>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.caption("All Rights Reserved. Proprietary Property of Miracles Group, RTD Huttons. Disclaimer: This report is meant for suggestive purpose only; agents should conduct their own analysis.")

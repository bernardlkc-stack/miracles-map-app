import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import json

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Miracles MAP App — Scoring Style",
    page_icon="🧭",
    layout="wide"
)

# ---------------- CSS ----------------
st.markdown("""
<style>
.stApp { background-color: #ffffff; }
h1, h2, h3 { color: #222; font-weight: 700; }

.grid {
  display: grid;
  grid-template-columns: 220px repeat(8, 1fr);
  gap: 4px;
  align-items: center;
  margin-bottom: 6px;
}

.header {
  background-color: #eaf2ff;
  color: #0d47a1;
  font-weight: 700;
  text-align: center;
  padding: 8px 0;
  border-bottom: 2px solid #b3d1ff;
}

.level {
  background-color: #eaf2ff;
  color: #0d47a1;
  font-weight: 700;
  text-align: left;
  padding: 6px 10px;
  border-bottom: 2px solid #b3d1ff;
}

.button-row {
  display: flex;
  justify-content: center;
  gap: 4px;
}

button[data-baseweb="button"] {
  background-color: #f6f7fb !important;
  color: #333 !important;
  border: 1px solid #ccc !important;
  border-radius: 8px !important;
  font-size: 0.85rem !important;
  width: 30px !important;
  height: 30px !important;
  padding: 0 !important;
}

.selected {
  background-color: #0d47a1 !important;
  color: white !important;
  border: 1px solid #0d47a1 !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------- DATA ----------------
SEGMENTS = [
    "HDB", "Private Resale", "Landed", "New Launch",
    "Top Projects", "Referral", "Indus/Comm", "Social Media"
]
LEVELS = [
    "Interest", "Knowledge", "Confidence", "Market",
    "Investment", "Commitment", "Support", "Income", "Willingness"
]

# ---------------- STATE ----------------
def ensure_row_state(level):
    key = f"row::{level}"
    if key not in st.session_state:
        st.session_state[key] = {seg: None for seg in SEGMENTS}
    return key

def get_row(level):
    return st.session_state[ensure_row_state(level)]

def set_cell(level, seg, val):
    st.session_state[ensure_row_state(level)][seg] = val

def validate_row(level):
    row = get_row(level)
    used = set()
    for seg, v in row.items():
        if v is None:
            continue
        if v in used or v not in range(1, 9):
            row[seg] = None
        else:
            used.add(v)

def all_complete():
    return all(all(v in range(1,9) for v in get_row(lvl).values()) for lvl in LEVELS)

# ---------------- APP ----------------
st.title("🧭 Miracles MAP App — MAP 1 (Scoring View)")
st.caption("Click to assign **unique scores (1–8)** per row. Each number may only appear once per level.")

# ---------------- HEADER ----------------
st.markdown("<div class='grid'>"
            + "<div class='header'></div>"
            + "".join(f"<div class='header'>{seg}</div>" for seg in SEGMENTS)
            + "</div>", unsafe_allow_html=True)

# ---------------- GRID ----------------
for level in LEVELS:
    ensure_row_state(level)
    st.markdown("<div class='grid'>", unsafe_allow_html=True)
    st.markdown(f"<div class='level'>{level}</div>", unsafe_allow_html=True)
    
    cols = st.columns(8, gap="small")
    for i, seg in enumerate(SEGMENTS):
        with cols[i]:
            current = get_row(level)[seg]
            buttons = [1,2,3,4,5,6,7,8]
            button_row = st.container()
            with button_row:
                btn_cols = st.columns(len(buttons))
                for j, num in enumerate(buttons):
                    with btn_cols[j]:
                        btn_class = "selected" if current == num else ""
                        clicked = st.button(f"{num}", key=f"{level}-{seg}-{num}", help=f"{seg} → {num}")
                        if clicked:
                            if num in [get_row(level)[s] for s in SEGMENTS if s != seg]:
                                st.warning(f"⚠️ {num} already used in {level}. Must be unique.")
                            else:
                                set_cell(level, seg, num)
    validate_row(level)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- TOTALS + CHART ----------------
values = {seg: {} for seg in SEGMENTS}
totals = {seg: 0 for seg in SEGMENTS}

if all_complete():
    for lvl in LEVELS:
        row = get_row(lvl)
        for seg, val in row.items():
            values[seg][lvl] = int(val)
    for seg in SEGMENTS:
        totals[seg] = sum(values[seg][lvl] for lvl in LEVELS)

st.divider()
st.markdown("### Totals")

cols = st.columns(8)
for i, seg in enumerate(SEGMENTS):
    with cols[i]:
        st.markdown(f"**{seg}**: {totals[seg] if totals[seg] else '—'}")

if all_complete() and sum(totals.values()) > 0:
    fig, ax = plt.subplots()
    ax.pie([totals[k] for k in SEGMENTS], labels=SEGMENTS, autopct='%1.0f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)
else:
    st.info("Complete all rows to see totals and chart.")

import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import json

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Miracles MAP App (MAP 1)",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean, neutral styling + fixed header setup
st.markdown(
    """
    <style>
      .stApp { background: #ffffff; }
      .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
      /* Sticky header styling */
      div[data-testid="stHorizontalBlock"] div[data-testid="stVerticalBlock"]:first-child {
          position: sticky;
          top: 3.5rem; /* Adjust if title overlaps */
          background-color: white;
          z-index: 999;
          border-bottom: 2px solid #eee;
          padding-top: 0.25rem;
          padding-bottom: 0.25rem;
      }
      div[data-testid="stVerticalBlock"] > div > div > div {
          text-align: center;
      }
    </style>
    """,
    unsafe_allow_html=True
)

DB = "map.db"

SEGMENTS = [
    "HDB", "Private Resale", "Landed", "New Launch",
    "Top Projects", "Referral", "Indus/Comm", "Social Media"
]
LEVELS = [
    "Interest", "Knowledge", "Confidence", "Market",
    "Investment", "Commitment", "Support", "Income", "Willingness"
]

RANK_OPTIONS = [8,7,6,5,4,3,2,1]
RANK_LABELS = {
    8: "8 – Very Strong",
    7: "7 – Strong",
    6: "6 – Above Average",
    5: "5 – Average",
    4: "4 – Below Average",
    3: "3 – Weak",
    2: "2 – Very Weak",
    1: "1 – Lowest",
}

def fmt_rank(x: int) -> str:
    return RANK_LABELS.get(x, str(x))

# ---------------- DB HELPERS ----------------
def conn():
    return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    c = conn()
    cur = c.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS associates(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            mobile TEXT,
            email TEXT,
            manager TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS map1(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            associate_name TEXT NOT NULL,
            data_json TEXT NOT NULL,
            totals_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    c.commit()
    c.close()

def upsert_associate(name, mobile="", email="", manager=""):
    c = conn(); cur = c.cursor()
    cur.execute("SELECT id FROM associates WHERE name=?", (name,))
    row = cur.fetchone()
    if row is None:
        cur.execute("INSERT INTO associates(name, mobile, email, manager) VALUES(?,?,?,?)",
                    (name, mobile, email, manager))
    else:
        cur.execute("UPDATE associates SET mobile=?, email=?, manager=? WHERE name=?",
                    (mobile, email, manager, name))
    c.commit(); c.close()

def list_associates():
    c = conn()
    df = pd.read_sql_query("SELECT name, mobile, email, manager FROM associates ORDER BY name", c)
    c.close()
    return df

def save_map1(associate_name, data, totals):
    c = conn(); cur = c.cursor()
    now = datetime.now().isoformat(timespec="seconds")
    cur.execute(
        "INSERT INTO map1(associate_name, data_json, totals_json, created_at) VALUES(?,?,?,?)",
        (associate_name, json.dumps(data), json.dumps(totals), now)
    )
    c.commit(); c.close()

def history_map1(associate_name):
    c = conn()
    df = pd.read_sql_query(
        "SELECT id, associate_name, data_json, totals_json, created_at FROM map1 WHERE associate_name=? ORDER BY created_at DESC",
        c, params=(associate_name,)
    )
    c.close()
    return df

# ---------------- STATE HELPERS ----------------
def ensure_row_state(level: str):
    key = f"row_state::{level}"
    if key not in st.session_state:
        st.session_state[key] = {seg: None for seg in SEGMENTS}
    return key

def get_row_selections(level: str) -> dict:
    key = ensure_row_state(level)
    return st.session_state[key]

def set_row_selection(level: str, segment: str, value: int | None):
    key = ensure_row_state(level)
    st.session_state[key][segment] = value

def available_options_for_cell(level: str, segment: str):
    row = get_row_selections(level)
    chosen_elsewhere = {row[s] for s in SEGMENTS if s != segment and row[s] is not None}
    current_value = row[segment]
    options = [r for r in RANK_OPTIONS if r not in chosen_elsewhere]
    if current_value is not None and current_value not in options:
        options = sorted(options + [current_value], reverse=True)
    return options, current_value

def row_complete(level: str) -> bool:
    row = get_row_selections(level)
    return all(val in RANK_OPTIONS for val in row.values())

def all_rows_complete() -> bool:
    return all(row_complete(level) for level in LEVELS)

# ---------------- INIT ----------------
init_db()

# ---------------- SIDEBAR ----------------
st.sidebar.header("Associate")
assoc_df = list_associates()
choices = ["— New —"] + assoc_df["name"].tolist()

default_index = 0
if "selected" in st.session_state and st.session_state["selected"] in choices:
    default_index = choices.index(st.session_state["selected"])

selected = st.sidebar.selectbox("Select associate", choices, index=default_index)

if selected == "— New —":
    name = st.sidebar.text_input("Name*")
    mobile = st.sidebar.text_input("Mobile")
    email = st.sidebar.text_input("Email")
    manager = st.sidebar.text_input("Manager", value="Bernard Lau")
    if st.sidebar.button("Save Associate"):
        if name.strip():
            upsert_associate(name.strip(), mobile.strip(), email.strip(), manager.strip())
            st.session_state["selected"] = name.strip()
            st.sidebar.success(f"Saved {name.strip()}. Loading…")
            st.rerun()
        else:
            st.sidebar.error("Name is required.")
else:
    rec = assoc_df[assoc_df["name"] == selected].iloc[0]
    st.sidebar.write(f"**Mobile:** {rec['mobile'] or '-'}")
    st.sidebar.write(f"**Email:** {rec['email'] or '-'}")
    st.sidebar.write(f"**Manager:** {rec['manager'] or '-'}")
    if st.sidebar.button("Refresh"):
        st.rerun()

# ---------------- MAIN UI ----------------
st.title("🧭 Miracles MAP App — MAP 1 (Ranking by Level)")
st.caption("Assign **unique ranks 1–8** in every row. Totals are the sum of ranks across the 9 levels; the chart reflects the segment focus by total score.")

if selected == "— New —":
    st.info("➡️ Add or select an associate from the sidebar to start.")
    st.stop()

st.subheader(f"Ranking Grid — {selected}")
st.markdown("Each row (level) must use **all scores 1–8 exactly once** across the 8 segments.")

# --- Fixed header row ---
header_cols = st.columns(len(SEGMENTS), gap="small")
for i, seg in enumerate(SEGMENTS):
    with header_cols[i]:
        st.markdown(f"<div style='text-align:center; font-weight:700; color:#333;'>{seg}</div>", unsafe_allow_html=True)

# --- Ranking Rows ---
for level in LEVELS:
    ensure_row_state(level)
    row_cols = st.columns(len(SEGMENTS), gap="small")

    for i, seg in enumerate(SEGMENTS):
        with row_cols[i]:
            options, current = available_options_for_cell(level, seg)
            options_with_blank = [None] + options
            labels_with_blank = ["— Select —"] + [fmt_rank(v) for v in options]

            if current is None:
                current_index = 0
            else:
                current_index = options_with_blank.index(current) if current in options_with_blank else 0

            selected_label = st.selectbox(
                label=level if i == 0 else " ",
                options=list(range(len(options_with_blank))),
                index=current_index,
                format_func=lambda idx, _labels=labels_with_blank: _labels[idx],
                key=f"{seg}::{level}",
            )

            new_value = options_with_blank[selected_label] if options_with_blank else None
            set_row_selection(level, seg, new_value)

# --- Calculate totals ---
values = {seg: {} for seg in SEGMENTS}
totals = {seg: 0 for seg in SEGMENTS}

if all_rows_complete():
    for level in LEVELS:
        row = get_row_selections(level)
        for seg, val in row.items():
            values[seg][level] = int(val)
    for seg in SEGMENTS:
        totals[seg] = sum(values[seg][lvl] for lvl in LEVELS)

# --- Totals Row ---
totals_cols = st.columns(len(SEGMENTS), gap="small")
for i, seg in enumerate(SEGMENTS):
    with totals_cols[i]:
        if all_rows_complete():
            st.markdown(f"**Total: {totals[seg]}**")
        else:
            st.markdown("**Total: —**")

st.markdown("---")

# --- Chart and Actions ---
if all_rows_complete() and sum(totals.values()) > 0:
    labels = list(totals.keys())
    sizes = [totals[k] for k in labels]
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.0f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)
else:
    st.warning("Complete **all rows** with unique ranks 1–8 before totals and chart are shown.")

with st.expander("Instructions", expanded=True):
    st.markdown("""
1️⃣ In each **row (level)**, assign **unique ranks 1–8** across the 8 segments.  
2️⃣ Each number 1–8 can be used **once per row only** (no duplicates).  
3️⃣ When **all rows are complete**, the **totals** and **chart** will appear.  
4️⃣ Totals are the **sum of ranks (1–8)** over the 9 levels.  
5️⃣ Aim to complete within 10 minutes in the presence of a District Head.
""")

st.markdown("---")

c1, c2, c3 = st.columns([1, 1, 2])

save_disabled = not all_rows_complete()
if c1.button("💾 Save Mapping", type="primary", disabled=save_disabled):
    values = {seg: {} for seg in SEGMENTS}
    totals = {seg: 0 for seg in SEGMENTS}
    for level in LEVELS:
        row = get_row_selections(level)
        for seg, val in row.items():
            values[seg][level] = int(val)
    for seg in SEGMENTS:
        totals[seg] = sum(values[seg][lvl] for lvl in LEVELS)
    save_map1(selected, values, totals)
    st.success(f"Mapping for {selected} saved!")
    st.balloons()

if c2.button("📜 View History"):
    df = history_map1(selected)
    if df.empty:
        st.info("No history yet.")
    else:
        out_rows = []
        for _, r in df.iterrows():
            t = json.loads(r["totals_json"])
            row = {"created_at": r["created_at"], **t}
            out_rows.append(row)
        st.dataframe(pd.DataFrame(out_rows), use_container_width=True)

if all_rows_complete():
    with c3:
        df_export = pd.DataFrame([{"Segment": k, "Total": v} for k, v in totals.items()])
        st.download_button(
            "⬇️ Export current totals (CSV)",
            data=df_export.to_csv(index=False).encode("utf-8"),
            file_name=f"{selected.replace(' ','_')}_map1_totals.csv",
            mime="text/csv"
        )
        st.download_button(
            "⬇️ Export current mapping (JSON)",
            data=json.dumps(values, indent=2).encode("utf-8"),
            file_name=f"{selected.replace(' ','_')}_map1_values.json",
            mime="application/json"
        )

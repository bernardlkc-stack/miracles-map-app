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
    layout="wide"
)

# --- CSS for styling ---
st.markdown("""
<style>
.stApp { background-color: #ffffff; }
h1, h2, h3 { color: #222; font-weight: 700; }
label { font-weight: 600 !important; }

.row-header {
  background: #eaf2ff;
  border-bottom: 1px solid #cfe0ff;
  color: #0d47a1;
  font-weight: 700;
  font-size: 0.95rem;
  padding: 6px 0 4px 0;
  margin-top: 0.35rem;
  text-align: center;
}

.level-title {
  color: #0d47a1;
  font-weight: 800;
  font-size: 1rem;
  margin: 1rem 0 0.25rem 0;
}

input[type=number] {
  background-color: #f3f4f6;
  color: #333;
  border-radius: 6px;
  text-align: center;
  border: 1px solid #ccc;
  width: 100%;
  height: 2.3rem;
  font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

# ---------------- DATA / DB ----------------
DB = "map.db"
SEGMENTS = [
    "HDB", "Private Resale", "Landed", "New Launch",
    "Top Projects", "Referral", "Indus/Comm", "Social Media"
]
LEVELS = [
    "Interest", "Knowledge", "Confidence", "Market",
    "Investment", "Commitment", "Support", "Income", "Willingness"
]

def conn(): return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    c = conn(); cur = c.cursor()
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
    c.commit(); c.close()

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
    c.close(); return df

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
    c.close(); return df

# ---------------- STATE HELPERS ----------------
def ensure_row_state(level: str):
    key = f"row_state::{level}"
    if key not in st.session_state:
        st.session_state[key] = {seg: None for seg in SEGMENTS}
    return key

def get_row(level: str) -> dict:
    return st.session_state[ensure_row_state(level)]

def set_cell(level: str, seg: str, val: int | None):
    st.session_state[ensure_row_state(level)][seg] = val

def validate_row(level: str):
    """Ensure unique 1–8 per row and valid values only."""
    row = get_row(level)
    used = set()
    for seg, val in row.items():
        if val is None: 
            continue
        if not (1 <= val <= 8):
            row[seg] = None
        elif val in used:
            row[seg] = None
        else:
            used.add(val)

def all_complete():
    return all(all(v in range(1,9) for v in get_row(lvl).values()) for lvl in LEVELS)

# ---------------- INIT ----------------
init_db()

# ---------------- HEADER ----------------
st.title("🧭 Miracles MAP App — MAP 1 (Ranking by Level)")
st.caption("Enter unique numbers 1–8 for each row. Each number must appear **once only per row**.")

assoc_df = list_associates()
choices = ["— New —"] + assoc_df["name"].tolist()

col1, col2, col3, col4 = st.columns(4)
with col1:
    selected = st.selectbox("Select Associate", choices)

if selected == "— New —":
    n1, n2, n3, n4 = st.columns(4)
    with n1: name = st.text_input("Name*")
    with n2: mobile = st.text_input("Mobile")
    with n3: email = st.text_input("Email")
    with n4: manager = st.text_input("Manager", value="Bernard Lau")
    if st.button("Save Associate"):
        if name.strip():
            upsert_associate(name.strip(), mobile.strip(), email.strip(), manager.strip())
            st.session_state["selected"] = name.strip()
            st.success(f"Saved {name.strip()} — reloading…")
            st.rerun()
        else:
            st.error("Please enter a name.")
else:
    rec = assoc_df[assoc_df["name"] == selected].iloc[0]
    st.markdown(
        f"**Mobile:** {rec['mobile'] or '-'} • **Email:** {rec['email'] or '-'} • **Manager:** {rec['manager'] or '-'}"
    )

st.divider()

# ---------------- GRID ----------------
if selected == "— New —":
    st.info("➡️ Save or select an associate to begin.")
    st.stop()

st.subheader(f"Ranking Grid — {selected}")
st.markdown("Each row (level) must use **all scores 1–8 exactly once** across 8 segments.")

def render_row_header():
    cols = st.columns(8)
    for i, seg in enumerate(SEGMENTS):
        with cols[i]:
            st.markdown(f"<div class='row-header'>{seg}</div>", unsafe_allow_html=True)

for level in LEVELS:
    st.markdown(f"<div class='level-title'>{level}</div>", unsafe_allow_html=True)
    render_row_header()
    cols = st.columns(8, gap="small")
    ensure_row_state(level)
    for i, seg in enumerate(SEGMENTS):
        with cols[i]:
            val = get_row(level)[seg]
            new_val = st.number_input(
                label=" ",
                min_value=1,
                max_value=8,
                value=val if val in range(1,9) else 1,
                step=1,
                key=f"{seg}::{level}"
            )
            set_cell(level, seg, int(new_val))
    validate_row(level)

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

st.markdown("**Totals**")
cols = st.columns(8, gap="small")
for i, seg in enumerate(SEGMENTS):
    with cols[i]:
        st.markdown(f"**{totals[seg] if totals[seg] else '—'}**")

st.divider()

if all_complete() and sum(totals.values()) > 0:
    labels = list(totals.keys())
    sizes = [totals[k] for k in labels]
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.0f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)
else:
    st.info("Complete all rows to see totals and chart.")

# ---------------- SAVE / EXPORT ----------------
cA, cB, cC = st.columns([1, 1, 2])
if cA.button("💾 Save Mapping", type="primary", disabled=not all_complete()):
    save_map1(selected, values, totals)
    st.success(f"Saved mapping for {selected}")
    st.balloons()

if cB.button("📜 View History"):
    df = history_map1(selected)
    if df.empty:
        st.info("No history found.")
    else:
        out_rows = []
        for _, r in df.iterrows():
            t = json.loads(r["totals_json"])
            row = {"created_at": r["created_at"], **t}
            out_rows.append(row)
        st.dataframe(pd.DataFrame(out_rows), use_container_width=True)

if all_complete():
    with cC:
        df_export = pd.DataFrame([{"Segment": k, "Total": v} for k, v in totals.items()])
        st.download_button(
            "⬇️ Export Totals (CSV)",
            data=df_export.to_csv(index=False).encode("utf-8"),
            file_name=f"{selected.replace(' ','_')}_map_totals.csv",
            mime="text/csv"
        )

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

# --- CSS for layout ---
st.markdown("""
<style>
.stApp { background-color: #ffffff; }
h1, h2, h3 { color: #222; font-weight: 700; }
label { font-weight: 600 !important; }

/* Table-like structure */
.grid-container {
  display: grid;
  grid-template-columns: 150px repeat(8, 1fr);
  align-items: center;
  gap: 6px;
}
.header-cell {
  background: #eaf2ff;
  color: #0d47a1;
  font-weight: 700;
  text-align: center;
  padding: 8px 0;
  font-size: 0.95rem;
  border-bottom: 1px solid #b3d1ff;
}
.level-cell {
  background: #eaf2ff;
  color: #0d47a1;
  font-weight: 700;
  text-align: left;
  padding: 6px 8px;
  font-size: 0.95rem;
  border-bottom: 1px solid #b3d1ff;
}
input[type="text"] {
  background-color: #f5f5f5;
  color: #333;
  text-align: center;
  border-radius: 6px;
  border: 1px solid #ccc;
  font-size: 0.9rem;
  width: 100%;
  height: 2.1rem;
}
</style>
""", unsafe_allow_html=True)

# ---------------- DATA ----------------
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
    cur.execute("""CREATE TABLE IF NOT EXISTS associates(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        mobile TEXT, email TEXT, manager TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS map1(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        associate_name TEXT NOT NULL,
        data_json TEXT NOT NULL,
        totals_json TEXT NOT NULL,
        created_at TEXT NOT NULL)""")
    c.commit(); c.close()
def list_associates():
    c = conn()
    df = pd.read_sql_query("SELECT name, mobile, email, manager FROM associates ORDER BY name", c)
    c.close(); return df
def upsert_associate(name, mobile="", email="", manager=""):
    c = conn(); cur = c.cursor()
    cur.execute("SELECT id FROM associates WHERE name=?", (name,))
    if cur.fetchone() is None:
        cur.execute("INSERT INTO associates(name, mobile, email, manager) VALUES(?,?,?,?)",
                    (name, mobile, email, manager))
    else:
        cur.execute("UPDATE associates SET mobile=?, email=?, manager=? WHERE name=?",
                    (mobile, email, manager, name))
    c.commit(); c.close()
def save_map1(associate_name, data, totals):
    c = conn(); cur = c.cursor()
    now = datetime.now().isoformat(timespec="seconds")
    cur.execute("INSERT INTO map1(associate_name,data_json,totals_json,created_at) VALUES(?,?,?,?)",
                (associate_name, json.dumps(data), json.dumps(totals), now))
    c.commit(); c.close()
def history_map1(associate_name):
    c = conn()
    df = pd.read_sql_query("SELECT created_at, totals_json FROM map1 WHERE associate_name=? ORDER BY created_at DESC",
                           c, params=(associate_name,))
    c.close(); return df

# ---------------- STATE ----------------
def ensure_row_state(level):
    key = f"row::{level}"
    if key not in st.session_state:
        st.session_state[key] = {seg: "" for seg in SEGMENTS}
    return key
def get_row(level): return st.session_state[ensure_row_state(level)]
def set_cell(level, seg, val): st.session_state[ensure_row_state(level)][seg] = val

def validate_row(level):
    """Ensure only 1–8 unique values per row."""
    row = get_row(level)
    seen = set()
    for seg, v in list(row.items()):
        if not v.strip():
            continue
        if not v.isdigit() or int(v) not in range(1,9) or int(v) in seen:
            row[seg] = ""
        else:
            seen.add(int(v))

def all_complete():
    return all(all(c.strip().isdigit() and int(c) in range(1,9) for c in get_row(l).values()) for l in LEVELS)

# ---------------- INIT ----------------
init_db()

# ---------------- HEADER ----------------
st.title("🧭 Miracles MAP App — MAP 1 (Ranking by Level)")
st.caption("Enter **unique numbers 1–8** per row. Each number can only be used once per level.")

assoc_df = list_associates()
choices = ["— New —"] + assoc_df["name"].tolist()

c1, c2, c3, c4 = st.columns(4)
with c1:
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
            st.success(f"✅ Saved {name.strip()} — reloading…")
            st.rerun()
        else:
            st.error("Please enter a name.")
else:
    rec = assoc_df[assoc_df["name"] == selected].iloc[0]
    st.markdown(f"**Mobile:** {rec['mobile'] or '-'}  •  **Email:** {rec['email'] or '-'}  •  **Manager:** {rec['manager'] or '-'}")

st.divider()

if selected == "— New —":
    st.info("➡️ Please save or select an associate to begin.")
    st.stop()

# ---------------- GRID ----------------
st.subheader(f"Ranking Grid — {selected}")
st.markdown("Each row must use **1–8 exactly once** across all 8 segments.")

# Header row
st.markdown("<div class='grid-container'>"
            + "<div class='header-cell'></div>"
            + "".join(f"<div class='header-cell'>{seg}</div>" for seg in SEGMENTS)
            + "</div>", unsafe_allow_html=True)

# Rows
for level in LEVELS:
    ensure_row_state(level)
    st.markdown("<div class='grid-container'>", unsafe_allow_html=True)
    st.markdown(f"<div class='level-cell'>{level}</div>", unsafe_allow_html=True)
    cols = st.columns(8, gap="small")
    for i, seg in enumerate(SEGMENTS):
        with cols[i]:
            val = get_row(level)[seg]
            new_val = st.text_input(
                label=" ",
                value=val,
                key=f"{seg}::{level}",
                max_chars=1,
                placeholder=" ",
            )
            set_cell(level, seg, new_val.strip())
    st.markdown("</div>", unsafe_allow_html=True)
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
    fig, ax = plt.subplots()
    ax.pie([totals[k] for k in SEGMENTS], labels=SEGMENTS, autopct='%1.0f%%', startangle=90)
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
        out = []
        for _, r in df.iterrows():
            t = json.loads(r["totals_json"])
            out.append({"created_at": r["created_at"], **t})
        st.dataframe(pd.DataFrame(out), use_container_width=True)

if all_complete():
    with cC:
        df_export = pd.DataFrame([{"Segment": k, "Total": v} for k, v in totals.items()])
        st.download_button(
            "⬇️ Export Totals (CSV)",
            data=df_export.to_csv(index=False).encode("utf-8"),
            file_name=f"{selected.replace(' ','_')}_map_totals.csv",
            mime="text/csv"
        )

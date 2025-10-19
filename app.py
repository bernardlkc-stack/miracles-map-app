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

# --- CSS: compact widgets, blue accents, per-row slim header ---
st.markdown("""
<style>
.stApp { background-color: #ffffff; }
h1, h2, h3 { color: #222; font-weight: 700; }
label { font-weight: 600 !important; }

/* Slim per-row header bar (blue) */
.row-header {
  background: #eaf2ff;
  border-bottom: 1px solid #cfe0ff;
  color: #0d47a1;
  font-weight: 700;
  font-size: 0.95rem;
  padding: 6px 0 4px 0;
  margin-top: 0.35rem;
}

/* Level label on left */
.level-title {
  color: #0d47a1;
  font-weight: 800;
  font-size: 1rem;
  margin: 1rem 0 0.25rem 0;
}

/* Compact selectboxes */
.stSelectbox div[data-baseweb="select"] {
  font-size: 0.9rem !important;
}
.stSelectbox > div > div {
  padding-top: 0.15rem !important;
  padding-bottom: 0.15rem !important;
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
def fmt_rank(x: int) -> str: return RANK_LABELS.get(x, str(x))

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

# ---- unique-per-row ranking state helpers ----
def ensure_row_state(level: str):
    key = f"row_state::{level}"
    if key not in st.session_state:
        st.session_state[key] = {seg: None for seg in SEGMENTS}
    return key

def get_row(level: str) -> dict:
    return st.session_state[ensure_row_state(level)]

def set_cell(level: str, seg: str, val: int | None):
    st.session_state[ensure_row_state(level)][seg] = val

def options_for(level: str, seg: str):
    row = get_row(level)
    taken = {row[s] for s in SEGMENTS if s != seg and row[s] is not None}
    cur = row[seg]
    opts = [r for r in RANK_OPTIONS if r not in taken]
    if cur is not None and cur not in opts:
        opts = sorted(opts + [cur], reverse=True)
    return opts, cur

def row_complete(level: str) -> bool:
    return all(v in RANK_OPTIONS for v in get_row(level).values())

def all_complete() -> bool:
    return all(row_complete(level) for level in LEVELS)

# ---------------- INIT ----------------
init_db()

# ---------------- TOP: TITLE + ASSOCIATE ----------------
st.title("🧭 Miracles MAP App — MAP 1 (Ranking by Level)")
st.caption("Assign **unique ranks 1–8** in each row. Totals (sum of ranks) reveal the strongest segments.")

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
            st.success(f"Saved {name.strip()} — reloading…"); st.rerun()
        else:
            st.error("Please enter a name.")
else:
    rec = assoc_df[assoc_df["name"] == selected].iloc[0]
    st.markdown(
        f"**Mobile:** {rec['mobile'] or '-'} &nbsp;&nbsp; • &nbsp;&nbsp; "
        f"**Email:** {rec['email'] or '-'} &nbsp;&nbsp; • &nbsp;&nbsp; "
        f"**Manager:** {rec['manager'] or '-'}",
        unsafe_allow_html=True
    )

st.divider()

# ---------------- RANKING GRID ----------------
if selected == "— New —":
    st.info("➡️ Save or select an associate to begin.")
    st.stop()

st.subheader(f"Ranking Grid — {selected}")
st.markdown("Each row (level) must use **all scores 1–8 exactly once** across 8 segments.")

# helper to render a slim header aligned with st.columns(8)
def render_row_header():
    cols = st.columns(8)
    for i, seg in enumerate(SEGMENTS):
        with cols[i]:
            st.markdown(f"<div class='row-header'>{seg}</div>", unsafe_allow_html=True)

# For every level, show a slim header THEN the 8 dropdowns under it
for level in LEVELS:
    st.markdown(f"<div class='level-title'>{level}</div>", unsafe_allow_html=True)
    render_row_header()
    cols = st.columns(8, gap="small")
    for i, seg in enumerate(SEGMENTS):
        with cols[i]:
            opts, cur = options_for(level, seg)
            opts_with_blank = [None] + opts
            labels = ["— Select —"] + [fmt_rank(x) for x in opts]
            idx = opts_with_blank.index(cur) if cur in opts_with_blank else 0
            pick = st.selectbox(
                label=" ",
                options=list(range(len(opts_with_blank))),
                index=idx,
                format_func=lambda j, _L=labels: _L[j],
                key=f"{seg}::{level}",
            )
            set_cell(level, seg, opts_with_blank[pick])

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

# Totals row (aligned with columns)
st.markdown("**Totals**")
cols = st.columns(8, gap="small")
for i, seg in enumerate(SEGMENTS):
    with cols[i]:
        st.markdown(f"**{totals[seg] if totals[seg] else '—'}**")

st.divider()

if all_complete() and sum(totals.values()) > 0:
    labels = list(totals.keys()); sizes = [totals[k] for k in labels]
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.0f%%', startangle=90)
    ax.axis('equal'); st.pyplot(fig)
else:
    st.info("Complete all rows to see totals and chart.")

# ---------------- SAVE / EXPORT ----------------
cA, cB, cC = st.columns([1, 1, 2])
if cA.button("💾 Save Mapping", type="primary", disabled=not all_complete()):
    save_map1(selected, values, totals)
    st.success(f"Saved mapping for {selected}"); st.balloons()

if cB.button("📜 View History"):
    df = history_map1(selected)
    if df.empty:
        st.info("No history found.")
    else:
        out_rows = []
        for _, r in df.iterrows():
            t = json.loads(r["totals_json"])
            row = {"created_at": r["created_at"], **t}; out_rows.append(row)
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
        st.download_button(
            "⬇️ Export Mapping (JSON)",
            data=json.dumps(values, indent=2).encode("utf-8"),
            file_name=f"{selected.replace(' ','_')}_map_values.json",
            mime="application/json"
        )

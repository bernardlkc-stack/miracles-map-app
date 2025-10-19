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

# --- CSS for Sticky Header, Compact Columns & Font ---
st.markdown("""
<style>
.stApp { background-color: #ffffff; }
h1, h2, h3 { color: #222; font-weight: 700; }
label { font-weight: 600 !important; }

/* Sticky header bar */
.sticky-header {
  position: sticky;
  top: 3.3rem;
  z-index: 1000;
  background-color: #e6f0ff;
  border-bottom: 2px solid #b3d1ff;
  padding: 6px 0;
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  color: #004aad;
  font-weight: 700;
  text-align: center;
}

/* Ensure all 8 columns stay in one line */
.column-wrapper {
  display: flex;
  justify-content: space-between;
  gap: 0.3rem;
  overflow-x: auto;
}
.column-wrapper > div {
  flex: 1 0 11.5%;
  min-width: 120px;
}

/* Compact dropdowns */
div[data-baseweb="select"] {
  font-size: 0.85rem !important;
}
.stSelectbox > div > div {
  padding-top: 0.2rem !important;
  padding-bottom: 0.2rem !important;
}

/* Left side labels (Interest, Knowledge, etc.) */
.level-label {
  color: #004aad;
  font-weight: 700;
  font-size: 0.9rem;
  margin-top: 0.7rem;
  margin-bottom: 0.3rem;
}
</style>
""", unsafe_allow_html=True)

# ---------------- DATABASE ----------------
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

# ---------------- STATE ----------------
def ensure_row_state(level: str):
    key = f"row_state::{level}"
    if key not in st.session_state:
        st.session_state[key] = {seg: None for seg in SEGMENTS}
    return key

def get_row_selections(level: str) -> dict:
    return st.session_state[ensure_row_state(level)]

def set_row_selection(level: str, segment: str, value: int | None):
    st.session_state[ensure_row_state(level)][segment] = value

def available_options_for_cell(level: str, segment: str):
    row = get_row_selections(level)
    chosen_elsewhere = {row[s] for s in SEGMENTS if s != segment and row[s] is not None}
    current_value = row[segment]
    options = [r for r in RANK_OPTIONS if r not in chosen_elsewhere]
    if current_value is not None and current_value not in options:
        options = sorted(options + [current_value], reverse=True)
    return options, current_value

def all_rows_complete():
    return all(all(val in RANK_OPTIONS for val in get_row_selections(level).values()) for level in LEVELS)

# ---------------- INIT ----------------
init_db()

# ---------------- HEADER ----------------
st.title("🧭 Miracles MAP App — MAP 1 (Ranking by Level)")
st.caption("Assign **unique ranks 1–8** per row. Totals identify strongest business segments.")

# --- Associate Info ---
assoc_df = list_associates()
choices = ["— New —"] + assoc_df["name"].tolist()

col1, col2, col3, col4 = st.columns(4)
with col1:
    selected = st.selectbox("Select Associate", choices)

if selected == "— New —":
    with st.container():
        name = st.text_input("Name*")
        mobile = st.text_input("Mobile")
        email = st.text_input("Email")
        manager = st.text_input("Manager", value="Bernard Lau")
        if st.button("Save Associate"):
            if name.strip():
                upsert_associate(name.strip(), mobile.strip(), email.strip(), manager.strip())
                st.session_state["selected"] = name.strip()
                st.success(f"✅ Saved {name.strip()}. Refreshing…")
                st.rerun()
            else:
                st.error("Please enter a name.")
else:
    rec = assoc_df[assoc_df["name"] == selected].iloc[0]
    st.markdown(
        f"""
        **Mobile:** {rec['mobile'] or '-'}  
        **Email:** {rec['email'] or '-'}  
        **Manager:** {rec['manager'] or '-'}
        """
    )

st.divider()

# ---------------- GRID ----------------
if selected == "— New —":
    st.info("➡️ Please save or select an associate to begin.")
    st.stop()

st.subheader(f"Ranking Grid — {selected}")
st.markdown("Each row (level) must use **all scores 1–8 exactly once** across 8 segments.")

# --- Sticky Header ---
st.markdown(
    "<div class='sticky-header'>" + "".join([f"<div style='width:11.5%'>{seg}</div>" for seg in SEGMENTS]) + "</div>",
    unsafe_allow_html=True
)

# --- Dropdown Rows ---
for level in LEVELS:
    ensure_row_state(level)
    st.markdown(f"<div class='level-label'>{level}</div>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='column-wrapper'>", unsafe_allow_html=True)
        for seg in SEGMENTS:
            options, current = available_options_for_cell(level, seg)
            opts = [None] + options
            labels = ["— Select —"] + [fmt_rank(o) for o in options]
            idx = opts.index(current) if current in opts else 0
            choice = st.selectbox(
                label=" ",
                options=list(range(len(opts))),
                index=idx,
                format_func=lambda i, _l=labels: _l[i],
                key=f"{seg}::{level}"
            )
            set_row_selection(level, seg, opts[choice])
        st.markdown("</div>", unsafe_allow_html=True)

# --- Totals Row ---
values = {seg: {} for seg in SEGMENTS}
totals = {seg: 0 for seg in SEGMENTS}
if all_rows_complete():
    for level in LEVELS:
        row = get_row_selections(level)
        for seg, val in row.items():
            values[seg][level] = int(val)
    for seg in SEGMENTS:
        totals[seg] = sum(values[seg][lvl] for lvl in LEVELS)

st.markdown(
    "<div class='sticky-header' style='background:#004aad;color:white;border:none;'>" +
    "".join([f"<div style='width:11.5%'>Total: {totals[seg] if totals[seg] > 0 else '—'}</div>" for seg in SEGMENTS]) +
    "</div>",
    unsafe_allow_html=True
)

# --- Chart ---
if all_rows_complete():
    labels = list(totals.keys())
    sizes = [totals[k] for k in labels]
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.0f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)
else:
    st.warning("Complete all rows before totals and chart appear.")

# --- Save / Export ---
colA, colB, colC = st.columns([1, 1, 2])
if colA.button("💾 Save Mapping", type="primary", disabled=not all_rows_complete()):
    save_map1(selected, values, totals)
    st.success(f"Saved mapping for {selected} ✅")
    st.balloons()

if colB.button("📜 View History"):
    df = history_map1(selected)
    if df.empty:
        st.info("No history found.")
    else:
        st.dataframe(df[["created_at", "totals_json"]], use_container_width=True)

if all_rows_complete():
    with colC:
        df_export = pd.DataFrame([{"Segment": k, "Total": v} for k, v in totals.items()])
        st.download_button(
            "⬇️ Export Totals (CSV)",
            data=df_export.to_csv(index=False).encode("utf-8"),
            file_name=f"{selected.replace(' ','_')}_map_totals.csv",
            mime="text/csv"
        )
